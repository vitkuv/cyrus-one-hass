import asyncio
import logging
from functools import cached_property
from time import monotonic
from typing import TypedDict

from bleak import BleakClient, BleakGATTCharacteristic, BLEDevice
from bleak.exc import BleakError
from bleak_retry_connector import BleakClientWithServiceCache, establish_connection
from homeassistant.components import bluetooth
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.device_registry import CONNECTION_BLUETOOTH, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator

from . import const

BLEAK_UNLIKELY_ERROR = "Unlikely error"


def format_bytes(data: bytes) -> str:
    return data.hex(" ", 1)


class CyrusOneState(TypedDict):
    model: str
    source: str
    is_muted: bool
    is_headphones_connected: bool
    is_av_direct_enabled: bool
    volume: int
    balance: int
    sw_version: str
    serial_number: str
    source_list: tuple[str]


class CyrusOneCoordinator(DataUpdateCoordinator[CyrusOneState]):
    initialization_delay = 0.3

    def __init__(
        self, hass: HomeAssistant, logger: logging.Logger, config_entry: ConfigEntry
    ) -> None:
        super().__init__(
            hass,
            logger,
            config_entry=config_entry,
            name=f"Cyrus {config_entry.data[const.CONF_BLE_NAME]} Coordinator",
            update_interval=None,
        )
        self.data = {"source_list": ()}
        self._lock = asyncio.Lock()
        self._ble_client: BleakClient | None = None
        self._ble_last_command_sent_time = 0.0
        self.is_initialized = False
        self._disconnect_requested = False

    @property
    def is_connected(self) -> bool:
        return self._ble_client is not None and self._ble_client.is_connected

    @property
    def is_disconnecting(self) -> bool:
        return self._disconnect_requested or self._shutdown_requested

    @property
    def available(self) -> bool:
        return self.is_initialized and self.is_connected and not self.is_disconnecting

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(const.DOMAIN, self.config_entry.unique_id)},
            connections={(CONNECTION_BLUETOOTH, self.config_entry.data[const.CONF_BLE_NAME])},
            name=self.config_entry.title,
            manufacturer=const.CYRUS_MANUFACTURER,
            model=self.data.get("model"),
            sw_version=self.data.get("sw_version"),
            serial_number=self.data.get("serial_number"),
        )

    def async_setup(self) -> None:
        self.config_entry.async_on_unload(
            bluetooth.async_register_callback(
                self.hass,
                self._handle_device_discovered,
                bluetooth.BluetoothCallbackMatcher(
                    local_name=self.config_entry.data[const.CONF_BLE_NAME]
                ),
                bluetooth.BluetoothScanningMode.ACTIVE,
            )
        )
        self.logger.debug(f"Coordinator for {self.config_entry.data[const.CONF_BLE_NAME]} started")

    @callback
    def _handle_device_discovered(
        self, service_info: bluetooth.BluetoothServiceInfoBleak, change: bluetooth.BluetoothChange
    ) -> None:
        self.logger.debug(
            f"Discovered Cyrus {service_info.name}, {service_info.address}, source: {service_info.source}, rssi: {service_info.rssi}"
        )

        if self.is_connected and self._ble_client.address == service_info.address:
            self.logger.debug(f"Device already connected {service_info.address}")
            return

        self.config_entry.async_create_background_task(
            self.hass,
            self.connect(service_info.device),
            name=f"{self.name} - {self.config_entry.title} - connect",
            eager_start=False,
        )

    async def connect(self, ble_device: BLEDevice) -> None:
        if self.is_connected:
            await self.disconnect()

        async with self._lock:
            self.logger.debug(f"Connecting to {ble_device.name}, {ble_device.address}")
            self.is_initialized = False
            self._disconnect_requested = False

            try:
                self._ble_client = await establish_connection(
                    BleakClientWithServiceCache,
                    ble_device,
                    name=f"Cyrus {ble_device.address} establish connection",
                    disconnected_callback=self._handle_device_disconnected,
                    use_services_cache=True,
                    max_attempts=2,
                )
            except BleakError as err:
                self.logger.info(f"Connection failed: {err}")
                return

            await self._ble_client.start_notify(
                const.GATT_DATA_CHARACTERISTIC_UUID, self._handle_ble_notification
            )

        await self._initialize_state()

    async def async_shutdown(self) -> None:
        await super().async_shutdown()
        await self.disconnect()
        self.logger.debug(f"Coordinator for {self.config_entry.data[const.CONF_BLE_NAME]} stopped")

    async def disconnect(self) -> None:
        self._disconnect_requested = True

        async with self._lock:
            ble_client, self._ble_client = self._ble_client, None
            self.is_initialized = False

            if ble_client and ble_client.is_connected:
                self.logger.debug(f"Disconnecting from {ble_client.address}")
                try:
                    await ble_client.stop_notify(const.GATT_DATA_CHARACTERISTIC_UUID)
                    await ble_client.disconnect()
                except BleakError as err:
                    self.logger.warning(f"Error while disconnecting: {err}")

    def _handle_device_disconnected(self, ble_client: BleakClient) -> None:
        self.logger.debug(f"Disconnected from {ble_client.address}")

        if self._ble_client is not ble_client:
            return

        self._ble_client = None
        is_initialized, self.is_initialized = self.is_initialized, False

        if is_initialized:
            self.async_update_listeners()

        if not self.is_disconnecting:
            bluetooth.async_clear_advertisement_history(self.hass, ble_client.address)

    def _handle_ble_notification(self, char: BleakGATTCharacteristic, data: bytearray) -> None:
        self.logger.debug(f"Received BLE notification: {format_bytes(data)}")

        if data[0] != const.BLE_MESSAGE_START or data[-1] != const.BLE_MESSAGE_END:
            self.logger.warning(f"Received invalid BLE notification: {format_bytes(data)}")
            return

        cmd = data[2]
        payload = data[4:-1]

        match cmd:
            case const.CMD_DAC_PRESENCE:
                if payload == const.BLE_VALUE_TRUE:
                    model = const.MODEL_CYRUS_ONE_HD
                    source_list = const.SOURCES_CYRUS_ONE_HD
                else:
                    model = const.MODEL_CYRUS_ONE
                    source_list = const.SOURCES_CYRUS_ONE

                self.data["model"] = model
                self.data["source_list"] = source_list

            case const.CMD_MUTE:
                self.data["is_muted"] = payload == const.BLE_VALUE_TRUE
                if self.is_initialized:
                    self.config_entry.async_create_task(
                        self.hass, self._ble_request_notification(const.CMD_HEADPHONE)
                    )

            case const.CMD_AV_DIRECT:
                self.data["is_av_direct_enabled"] = payload == const.BLE_VALUE_TRUE

            case const.CMD_HEADPHONE:
                self.data["is_headphones_connected"] = payload == const.BLE_VALUE_TRUE

            case const.CMD_VOLUME:
                self.data["volume"] = int(payload)

            case const.CMD_BALANCE:
                self.data["balance"] = int(payload)

            case const.CMD_SW_VERSION:
                self.data["sw_version"] = ".".join(payload.decode("ascii"))

            case const.CMD_SERIAL_NUMBER:
                self.data["serial_number"] = payload.decode("ascii")

            case const.CMD_SOURCE:
                index = int(payload) - 1
                self.data["source"] = self.data["source_list"][index]

            case _:
                self.logger.warning(
                    f"Received unsupported BLE command: {hex(cmd)}, payload: {format_bytes(payload)}"
                )
                return

        self.logger.debug(f"New state: {self.data}")

        if self.is_initialized:
            self.async_update_listeners()

    @staticmethod
    def ble_create_message(cmd: int, payload: bytes) -> bytes:
        return bytes(
            [
                const.BLE_MESSAGE_START,
                const.BLE_MESSAGE_FILLER_BYTE,
                cmd,
                ord("0") + len(payload),
                *payload,
                const.BLE_MESSAGE_END,
            ]
        )

    async def _ble_write_command(
        self, cmd: int, payload: bytes, *, char: str = const.GATT_DATA_CHARACTERISTIC_UUID
    ) -> None:
        message = self.ble_create_message(cmd, payload)
        async with self._lock:
            self.logger.debug(f"Sending GATT char: {char}, message: {format_bytes(message)}")

            if not self.is_connected:
                self.logger.debug("Device was disconnected, GATT message will be ignored")
                return

            delta = monotonic() - self._ble_last_command_sent_time
            if const.BLE_COMMANDS_DELAY > delta:
                await asyncio.sleep(const.BLE_COMMANDS_DELAY - delta)

            try:
                await self._ble_client.write_gatt_char(char, message, response=True)
            except BleakError as err:
                if BLEAK_UNLIKELY_ERROR not in str(err):
                    self.logger.exception(
                        f"Error for sending GATT char: {char}, message: {format_bytes(message)}"
                    )
            self._ble_last_command_sent_time = monotonic()

    async def _ble_request_notification(self, cmd: int) -> None:
        await self._ble_write_command(const.CMD_FETCH, bytes([cmd]))

    async def _initialize_state(self) -> None:
        for cmd in (
            const.CMD_DAC_PRESENCE,
            const.CMD_AV_DIRECT,
            const.CMD_BALANCE,
            const.CMD_HEADPHONE,
            const.CMD_MUTE,
            const.CMD_SERIAL_NUMBER,
            const.CMD_SOURCE,
            const.CMD_SW_VERSION,
            const.CMD_VOLUME,
        ):
            await self._ble_request_notification(cmd)

        await asyncio.sleep(self.initialization_delay)

        self.is_initialized = True
        self.logger.debug("Initial state successfully fetched")

        device_registry = dr.async_get(self.hass)
        device = device_registry.async_get_device(identifiers=self.device_info["identifiers"])
        if device:
            device_registry.async_update_device(
                device_id=device.id,
                model=self.data.get("model"),
                sw_version=self.data.get("sw_version"),
                serial_number=self.data.get("serial_number"),
            )

        self.async_update_listeners()

    async def set_source(self, source: str) -> None:
        index = self.data["source_list"].index(source)
        await self._ble_write_command(const.CMD_SOURCE, str(index + 1).encode())

    async def set_volume(self, value: int) -> None:
        tens = ord("0") + value // 10
        ones = ord("0") + value % 10
        await self._ble_write_command(const.CMD_VOLUME, bytes([tens, ones]))
        await self._ble_request_notification(const.CMD_VOLUME)

    async def set_mute(self, enabled: bool) -> None:
        val = const.BLE_VALUE_TRUE if enabled else const.BLE_VALUE_FALSE
        await self._ble_write_command(const.CMD_MUTE, val)

    async def set_av_direct(self, enabled: bool) -> None:
        val = const.BLE_VALUE_TRUE if enabled else const.BLE_VALUE_FALSE
        await self._ble_write_command(const.CMD_AV_DIRECT, val)

    async def set_balance(self, value: int) -> None:
        tens = ord("0") + value // 10
        ones = ord("0") + value % 10
        await self._ble_write_command(const.CMD_BALANCE, bytes([tens, ones]))
        await self._ble_request_notification(const.CMD_BALANCE)

    async def set_brightness_up(self) -> None:
        await self._ble_write_command(const.CMD_BRIGHTNESS, bytes([const.PAYLOAD_BRIGHTNESS_UP]))

    async def set_brightness_down(self) -> None:
        await self._ble_write_command(const.CMD_BRIGHTNESS, bytes([const.PAYLOAD_BRIGHTNESS_DOWN]))


class CyrusOneCoordinatorEntity(CoordinatorEntity[CyrusOneCoordinator]):
    _attr_unique_id_suffix: str | None = None

    @cached_property
    def unique_id(self) -> str:
        entry_unique_id = self.coordinator.config_entry.unique_id
        suffix = self._attr_unique_id_suffix
        return f"{entry_unique_id}_{suffix}" if suffix else entry_unique_id

    @property
    def available(self) -> bool:
        return self.coordinator.available

    @property
    def device_info(self) -> DeviceInfo:
        return self.coordinator.device_info
