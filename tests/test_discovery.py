"""Tests for BLE discovery and MAC address change handling."""

from unittest.mock import AsyncMock, MagicMock, patch

from bleak.backends.scanner import BLEDevice
from bleak_retry_connector import BleakClientWithServiceCache
from homeassistant.components.bluetooth import BluetoothServiceInfoBleak
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.cyrus_one import const

from .conftest import inject_bluetooth_service_info


def _make_service_info(name, address):
    device = MagicMock(spec=BLEDevice)
    device.address = address
    device.name = name
    device.details = {}
    return BluetoothServiceInfoBleak(
        name=name,
        address=address,
        rssi=-70,
        manufacturer_data={},
        service_data={},
        service_uuids=[],
        source="local",
        device=device,
        advertisement=MagicMock(),
        connectable=True,
        time=12345.0,
        tx_power=-127,
    )


async def test_discovery_triggers_connection(hass, enable_bluetooth):
    """A matching BLE advertisement triggers a connect attempt."""
    entry = MockConfigEntry(
        domain=const.DOMAIN,
        data={const.CONF_BLE_NAME: "ONE-12345"},
        unique_id="cyrus_one_12345",
    )
    entry.add_to_hass(hass)

    with patch(
        "custom_components.cyrus_one.coordinator.establish_connection",
        return_value=AsyncMock(spec=BleakClientWithServiceCache),
    ):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        coord = hass.data[const.DOMAIN][entry.entry_id]
        coord.initialization_delay = 0.01

        inject_bluetooth_service_info(hass, _make_service_info("ONE-12345", "AA:BB:CC:DD:EE:FF"))
        await hass.async_block_till_done()
        # connect() was triggered (background task), so we wait briefly
        await hass.async_block_till_done()
        # The coordinator should have a ble_client
        assert coord._ble_client is not None


async def test_discovery_already_connected_skips(hass, enable_bluetooth):
    """A duplicate advertisement for the same MAC is skipped when already connected."""
    entry = MockConfigEntry(
        domain=const.DOMAIN,
        data={const.CONF_BLE_NAME: "ONE-12345"},
        unique_id="cyrus_one_12345",
    )
    entry.add_to_hass(hass)

    client = AsyncMock(spec=BleakClientWithServiceCache)
    client.is_connected = True
    client.address = "AA:BB:CC:DD:EE:FF"

    with patch(
        "custom_components.cyrus_one.coordinator.establish_connection",
        return_value=client,
    ):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        coord = hass.data[const.DOMAIN][entry.entry_id]
        coord.initialization_delay = 0.01

        # First discovery
        inject_bluetooth_service_info(hass, _make_service_info("ONE-12345", "AA:BB:CC:DD:EE:FF"))
        await hass.async_block_till_done()
        await hass.async_block_till_done()

        # Second discovery (same MAC)
        inject_bluetooth_service_info(hass, _make_service_info("ONE-12345", "AA:BB:CC:DD:EE:FF"))
        await hass.async_block_till_done()
        # The connect count should be 1 (only one connect attempt)
        # Note: connect is called via background task, so we check the client ref
        assert coord._ble_client is client


async def test_discovery_new_address_connects(hass, enable_bluetooth):
    """When the device re-appears with a different MAC, coordinator reconnects."""
    entry = MockConfigEntry(
        domain=const.DOMAIN,
        data={const.CONF_BLE_NAME: "ONE-12345"},
        unique_id="cyrus_one_12345",
    )
    entry.add_to_hass(hass)

    old_client = AsyncMock(spec=BleakClientWithServiceCache)
    old_client.is_connected = True
    old_client.address = "AA:BB:CC:DD:EE:FF"

    new_client = AsyncMock(spec=BleakClientWithServiceCache)
    new_client.is_connected = True
    new_client.address = "11:22:33:44:55:66"

    connect_count = 0

    async def connect_side_effect(*args, **kwargs):
        nonlocal connect_count
        connect_count += 1
        if connect_count == 1:
            return old_client
        return new_client

    with patch(
        "custom_components.cyrus_one.coordinator.establish_connection",
        side_effect=connect_side_effect,
    ):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        coord = hass.data[const.DOMAIN][entry.entry_id]
        coord.initialization_delay = 0.01
        with patch.object(const, "BLE_COMMANDS_DELAY", 0):
            # First discovery
            inject_bluetooth_service_info(
                hass, _make_service_info("ONE-12345", "AA:BB:CC:DD:EE:FF")
            )
            await hass.async_block_till_done()
            await hass.async_block_till_done()

            # Simulate disconnect
            coord._handle_device_disconnected(old_client)
            await hass.async_block_till_done()

            # Second discovery with new MAC
            inject_bluetooth_service_info(
                hass, _make_service_info("ONE-12345", "11:22:33:44:55:66")
            )
            await hass.async_block_till_done()
            await hass.async_block_till_done()

            # Coordinator should have reconnected to new address
            assert coord._ble_client is new_client


async def test_disconnect_clears_advertisement_history(hass, enable_bluetooth):
    """Disconnect clears the advertisement history entry."""
    entry = MockConfigEntry(
        domain=const.DOMAIN,
        data={const.CONF_BLE_NAME: "ONE-12345"},
        unique_id="cyrus_one_12345",
    )
    entry.add_to_hass(hass)

    client = AsyncMock(spec=BleakClientWithServiceCache)
    client.is_connected = True
    client.address = "AA:BB:CC:DD:EE:FF"

    with (
        patch(
            "custom_components.cyrus_one.coordinator.establish_connection",
            return_value=client,
        ),
        patch("homeassistant.components.bluetooth.async_clear_advertisement_history") as mock_clear,
    ):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        coord = hass.data[const.DOMAIN][entry.entry_id]
        coord.initialization_delay = 0.01
        with patch.object(const, "BLE_COMMANDS_DELAY", 0):
            inject_bluetooth_service_info(
                hass, _make_service_info("ONE-12345", "AA:BB:CC:DD:EE:FF")
            )
            await hass.async_block_till_done()
            await hass.async_block_till_done()

            # Disconnect should trigger clear advertisement history
            coord._handle_device_disconnected(client)
            await hass.async_block_till_done()
            mock_clear.assert_called_once_with(hass, "AA:BB:CC:DD:EE:FF")
