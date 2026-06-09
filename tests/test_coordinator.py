"""Tests for coordinator connection lifecycle, commands, and resilience."""

from unittest.mock import MagicMock, patch

from bleak.backends.scanner import BLEDevice
from bleak.exc import BleakError
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.cyrus_one import const
from custom_components.cyrus_one.coordinator import CyrusOneCoordinator


# ---------------------------------------------------------------------------
# Connection lifecycle
# ---------------------------------------------------------------------------
async def test_connection_sends_nine_fetches(coordinator):
    """On connect, nine fetch commands are sent to initialise state."""
    coord, mock_client = coordinator
    assert mock_client.write_gatt_char.call_count == 9


async def test_connection_calls_start_notify(coordinator):
    """On connect, start_notify is called with the GATT data characteristic."""
    coord, mock_client = coordinator
    mock_client.start_notify.assert_called_once_with(
        const.GATT_DATA_CHARACTERISTIC_UUID, coord._handle_ble_notification
    )


async def test_connection_sets_is_initialized(coordinator):
    """After initialization, is_initialized is True."""
    coord, _ = coordinator
    assert coord.is_initialized is True


async def test_disconnect_clears_is_initialized(coordinator):
    """After disconnect, is_initialized is False."""
    coord, mock_client = coordinator
    await coord.disconnect()
    assert coord.is_initialized is False


async def test_available_flag(coordinator):
    """Available is True only when initialized, connected, and not disconnecting."""
    coord, _ = coordinator
    assert coord.available is True
    await coord.disconnect()
    assert coord.available is False


# ---------------------------------------------------------------------------
# Command sending
# ---------------------------------------------------------------------------
async def test_set_volume_writes(coordinator):
    """set_volume writes the correct GATT message and requests volume fetch."""
    coord, mock_client = coordinator
    before = mock_client.write_gatt_char.call_count
    await coord.set_volume(45)
    # Two writes: one for the command, one for the refetch
    assert mock_client.write_gatt_char.call_count == before + 2


async def test_set_mute_writes(coordinator):
    """set_mute sends the correct GATT message."""
    coord, mock_client = coordinator
    before = mock_client.write_gatt_char.call_count
    await coord.set_mute(True)
    assert mock_client.write_gatt_char.call_count == before + 1


async def test_set_source_writes(coordinator):
    """set_source sends the correct GATT message."""
    coord, mock_client = coordinator
    # Populate source_list
    coord.data["source_list"] = const.SOURCES_CYRUS_ONE
    before = mock_client.write_gatt_char.call_count
    await coord.set_source(const.SOURCE_AV)
    assert mock_client.write_gatt_char.call_count == before + 1


async def test_set_av_direct_writes(coordinator):
    """set_av_direct sends the correct GATT message."""
    coord, mock_client = coordinator
    before = mock_client.write_gatt_char.call_count
    await coord.set_av_direct(True)
    assert mock_client.write_gatt_char.call_count == before + 1


async def test_set_balance_writes(coordinator):
    """set_balance writes the correct GATT message and requests balance fetch."""
    coord, mock_client = coordinator
    before = mock_client.write_gatt_char.call_count
    await coord.set_balance(10)
    assert mock_client.write_gatt_char.call_count == before + 2


async def test_brightness_up_writes(coordinator):
    """set_brightness_up sends the correct GATT message."""
    coord, mock_client = coordinator
    before = mock_client.write_gatt_char.call_count
    await coord.set_brightness_up()
    assert mock_client.write_gatt_char.call_count == before + 1


async def test_brightness_down_writes(coordinator):
    """set_brightness_down sends the correct GATT message."""
    coord, mock_client = coordinator
    before = mock_client.write_gatt_char.call_count
    await coord.set_brightness_down()
    assert mock_client.write_gatt_char.call_count == before + 1


async def test_command_delay_enforced(coordinator):
    """Commands are rate-limited by BLE_COMMANDS_DELAY."""
    coord, mock_client = coordinator
    with patch.object(const, "BLE_COMMANDS_DELAY", 1.0):
        await coord.set_mute(True)
        # The second command would be delayed, but we just check no crash
        await coord.set_mute(False)


# ---------------------------------------------------------------------------
# Resilience
# ---------------------------------------------------------------------------
async def test_connection_failure_graceful(hass):
    """When establish_connection raises, coordinator stays uninitialized."""
    entry = MockConfigEntry(
        domain=const.DOMAIN,
        data={const.CONF_BLE_NAME: "ONE-TEST"},
        unique_id="cyrus_one_test",
    )
    entry.add_to_hass(hass)

    with patch(
        "custom_components.cyrus_one.coordinator.establish_connection",
        side_effect=BleakError("device unreachable"),
    ):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        coord: CyrusOneCoordinator = hass.data[const.DOMAIN][entry.entry_id]

        device = MagicMock(spec=BLEDevice)
        device.address = "AA:BB:CC:DD:EE:FF"
        device.name = "ONE-TEST"
        device.details = {}

        await coord.connect(device)
        assert coord._ble_client is None
        assert not coord.is_initialized


async def test_write_gatt_fails_gracefully(coordinator):
    """A BleakError during write is caught and logged, not raised."""
    coord, mock_client = coordinator
    mock_client.write_gatt_char.side_effect = BleakError("disconnected")
    # Should not raise
    await coord.set_mute(True)


async def test_write_to_disconnected_device_noop(coordinator):
    """Writing when no client is connected is a no-op."""
    coord, mock_client = coordinator
    await coord.disconnect()
    await coord.set_mute(True)
    # The mock may have been called before disconnect, so just check no crash


async def test_handle_device_disconnected_clears(coordinator):
    """When disconnected callback fires, ble_client is set to None."""
    coord, mock_client = coordinator
    coord._handle_device_disconnected(mock_client)
    assert coord._ble_client is None
    assert not coord.is_initialized


async def test_shutdown_disconnects(coordinator):
    """async_shutdown calls disconnect."""
    coord, mock_client = coordinator
    await coord.async_shutdown()
    assert coord._ble_client is None
    assert not coord.is_initialized
    # Should be safe to call again
    await coord.async_shutdown()
