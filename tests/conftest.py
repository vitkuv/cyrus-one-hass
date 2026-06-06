"""Fixtures for Cyrus ONE custom component tests."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from bleak.backends.scanner import BLEDevice
from bleak_retry_connector import BleakClientWithServiceCache
from homeassistant.components import bluetooth as bluetooth_domain
from homeassistant.components.bluetooth import (
    BluetoothServiceInfoBleak,
    async_get_advertisement_callback,
)
from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.cyrus_one import const
from custom_components.cyrus_one.coordinator import CyrusOneCoordinator


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    yield


# ---------------------------------------------------------------------------
# Helper: inject a BluetoothServiceInfoBleak into the HA bluetooth manager
# ---------------------------------------------------------------------------
def inject_bluetooth_service_info(hass: Any, service_info: BluetoothServiceInfoBleak) -> None:
    """Push a BluetoothServiceInfoBleak through the bluetooth manager callback."""
    async_get_advertisement_callback(hass)(service_info)


# ---------------------------------------------------------------------------
# Shared data fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def ble_device_name() -> str:
    return "ONE-12345"


@pytest.fixture
def ble_device_address() -> str:
    return "AA:BB:CC:DD:EE:FF"


@pytest.fixture
def mock_config_entry(hass: Any, ble_device_name: str) -> MockConfigEntry:
    entry = MockConfigEntry(
        domain=const.DOMAIN,
        data={const.CONF_BLE_NAME: ble_device_name},
        unique_id=f"cyrus_{ble_device_name.replace('-', '_')}".lower(),
    )
    entry.add_to_hass(hass)
    return entry


# ---------------------------------------------------------------------------
# Bluetooth hardware mock (prevents real BLE hardware access)
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def mock_bluetooth_hardware() -> None:
    with (
        patch("habluetooth.scanner.OriginalBleakScanner.start"),
        patch("habluetooth.scanner.platform.system", return_value="Linux"),
        patch("habluetooth.scanner.SYSTEM", "Linux"),
        patch("bluetooth_adapters.systems.platform.system", return_value="Linux"),
        patch("bluetooth_adapters.systems.linux.LinuxAdapters.refresh"),
        patch(
            "bluetooth_adapters.systems.linux.LinuxAdapters.adapters",
            {
                "hci0": {
                    "address": "00:00:00:00:00:01",
                    "hw_version": "usb:v1D6Bp0246d053F",
                    "passive_scan": True,
                    "sw_version": "homeassistant",
                    "manufacturer": "ACME",
                    "product": "BT Adapter",
                    "product_id": "aa01",
                    "vendor_id": "cc01",
                },
            },
        ),
    ):
        yield


@pytest.fixture
async def enable_bluetooth(hass: Any, mock_bluetooth_hardware: None) -> None:
    assert await async_setup_component(hass, bluetooth_domain.DOMAIN, {})
    await hass.async_block_till_done()


# ---------------------------------------------------------------------------
# Mock BLE device + client for coordinator tests
# ---------------------------------------------------------------------------
@pytest.fixture
def mock_ble_device(ble_device_name: str, ble_device_address: str) -> BLEDevice:
    device = MagicMock(spec=BLEDevice)
    device.address = ble_device_address
    device.name = ble_device_name
    device.details = {}
    return device


@pytest.fixture
def mock_ble_client(ble_device_address: str) -> AsyncMock:
    client = AsyncMock(spec=BleakClientWithServiceCache)
    client.is_connected = True
    client.address = ble_device_address
    client.write_gatt_char = AsyncMock()
    client.start_notify = AsyncMock()
    client.stop_notify = AsyncMock()
    client.disconnect = AsyncMock()
    return client


@pytest.fixture
def mock_establish_connection(mock_ble_client: AsyncMock) -> MagicMock:
    with patch(
        "custom_components.cyrus_one.coordinator.establish_connection",
        return_value=mock_ble_client,
    ) as mock:
        yield mock


# ---------------------------------------------------------------------------
# Real coordinator (with mocked BLE) for protocol / state tests
# ---------------------------------------------------------------------------
@pytest.fixture
async def coordinator(
    hass: Any,
    mock_config_entry: MockConfigEntry,
    mock_establish_connection: MagicMock,
    mock_ble_device: BLEDevice,
    enable_bluetooth: None,
) -> tuple[CyrusOneCoordinator, AsyncMock]:
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    coord: CyrusOneCoordinator = hass.data[const.DOMAIN][mock_config_entry.entry_id]
    coord.initialization_delay = 0.01
    with patch.object(const, "BLE_COMMANDS_DELAY", 0):
        await coord.connect(mock_ble_device)
    await hass.async_block_till_done()
    return coord, coord._ble_client


# ---------------------------------------------------------------------------
# Mock coordinator for entity-only tests
# ---------------------------------------------------------------------------
@pytest.fixture
def coordinator_data() -> dict[str, Any]:
    return {
        "model": const.MODEL_CYRUS_ONE,
        "source": const.SOURCE_AV,
        "is_muted": False,
        "is_headphones_connected": False,
        "is_av_direct_enabled": False,
        "volume": 45,
        "balance": 10,
        "sw_version": "1.0.0",
        "serial_number": "SN12345",
        "source_list": const.SOURCES_CYRUS_ONE,
    }


@pytest.fixture
async def mock_coordinator(
    hass: Any,
    mock_config_entry: MockConfigEntry,
    coordinator_data: dict[str, Any],
) -> CyrusOneCoordinator:
    coordinator = AsyncMock(spec=CyrusOneCoordinator)
    coordinator.data = dict(coordinator_data)
    coordinator.available = True
    coordinator.config_entry = mock_config_entry
    coordinator.device_info = {
        "identifiers": {(const.DOMAIN, mock_config_entry.unique_id)},
        "connections": set(),
    }

    with patch(
        "custom_components.cyrus_one.CyrusOneCoordinator",
        return_value=coordinator,
    ):
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()
        yield hass.data[const.DOMAIN][mock_config_entry.entry_id]
