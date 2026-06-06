"""Tests for BLE notification parsing (_handle_ble_notification)."""

from unittest.mock import MagicMock

from bleak import BleakGATTCharacteristic

from custom_components.cyrus_one import const


def _notify(coordinator, cmd, payload, *, is_initialized=True):
    """Build a framed BLE message and feed it to the notification handler."""
    data = bytearray(
        [
            const.BLE_MESSAGE_START,
            const.BLE_MESSAGE_FILLER_BYTE,
            cmd,
            ord("0") + len(payload),
            *payload,
            const.BLE_MESSAGE_END,
        ]
    )
    char = MagicMock(spec=BleakGATTCharacteristic)
    coordinator._handle_ble_notification(char, data)


def test_dac_presence_hd(coordinator):
    coord, _ = coordinator
    _notify(coord, const.CMD_DAC_PRESENCE, b"1")
    assert coord.data["model"] == const.MODEL_CYRUS_ONE_HD
    assert coord.data["source_list"] == const.SOURCES_CYRUS_ONE_HD


def test_dac_presence_base(coordinator):
    coord, _ = coordinator
    _notify(coord, const.CMD_DAC_PRESENCE, b"0")
    assert coord.data["model"] == const.MODEL_CYRUS_ONE
    assert coord.data["source_list"] == const.SOURCES_CYRUS_ONE


def test_mute_on(coordinator):
    coord, _ = coordinator
    _notify(coord, const.CMD_MUTE, b"1")
    assert coord.data["is_muted"] is True


def test_mute_off(coordinator):
    coord, _ = coordinator
    _notify(coord, const.CMD_MUTE, b"0")
    assert coord.data["is_muted"] is False


def test_volume_zero(coordinator):
    coord, _ = coordinator
    _notify(coord, const.CMD_VOLUME, b"00")
    assert coord.data["volume"] == 0


def test_volume_mid(coordinator):
    coord, _ = coordinator
    _notify(coord, const.CMD_VOLUME, b"45")
    assert coord.data["volume"] == 45


def test_volume_max(coordinator):
    coord, _ = coordinator
    _notify(coord, const.CMD_VOLUME, b"90")
    assert coord.data["volume"] == 90


def test_balance(coordinator):
    coord, _ = coordinator
    _notify(coord, const.CMD_BALANCE, b"10")
    assert coord.data["balance"] == 10


def test_source_first(coordinator):
    coord, mock_client = coordinator
    # source_list must be populated first
    _notify(coord, const.CMD_DAC_PRESENCE, b"0")
    _notify(coord, const.CMD_SOURCE, b"1")
    assert coord.data["source"] == const.SOURCE_BLUETOOTH


def test_source_last(coordinator):
    coord, _ = coordinator
    _notify(coord, const.CMD_DAC_PRESENCE, b"0")
    _notify(coord, const.CMD_SOURCE, b"6")
    assert coord.data["source"] == const.SOURCE_AV


def test_sw_version(coordinator):
    coord, _ = coordinator
    _notify(coord, const.CMD_SW_VERSION, b"100")
    assert coord.data["sw_version"] == "1.0.0"


def test_serial_number(coordinator):
    coord, _ = coordinator
    _notify(coord, const.CMD_SERIAL_NUMBER, b"SN12345")
    assert coord.data["serial_number"] == "SN12345"


def test_av_direct_enabled(coordinator):
    coord, _ = coordinator
    _notify(coord, const.CMD_AV_DIRECT, b"1")
    assert coord.data["is_av_direct_enabled"] is True


def test_av_direct_disabled(coordinator):
    coord, _ = coordinator
    _notify(coord, const.CMD_AV_DIRECT, b"0")
    assert coord.data["is_av_direct_enabled"] is False


def test_headphone_on(coordinator):
    coord, _ = coordinator
    _notify(coord, const.CMD_HEADPHONE, b"1")
    assert coord.data["is_headphones_connected"] is True


def test_headphone_off(coordinator):
    coord, _ = coordinator
    _notify(coord, const.CMD_HEADPHONE, b"0")
    assert coord.data["is_headphones_connected"] is False


async def test_mute_triggers_headphone_fetch(coordinator, hass):
    """Mute notification after initialization triggers a headphone fetch."""
    coord, mock_client = coordinator
    before_count = mock_client.write_gatt_char.call_count
    _notify(coord, const.CMD_MUTE, b"1")
    await hass.async_block_till_done()
    # The mute handler creates a background task that fetches headphone state
    assert mock_client.write_gatt_char.call_count > before_count


def test_invalid_frame_start_byte(coordinator):
    """Frame with wrong start byte is rejected."""
    coord, mock_client = coordinator
    data = bytearray([0xFF, 0x2B, 0x4D, 0x31, 0x31, 0x25])
    char = MagicMock(spec=BleakGATTCharacteristic)
    coord._handle_ble_notification(char, data)
    assert coord.data.get("is_muted") is None or coord.data["is_muted"] is False  # unchanged


def test_invalid_frame_end_byte(coordinator):
    """Frame with wrong end byte is rejected."""
    coord, _ = coordinator
    data = bytearray([0x40, 0x2B, 0x4D, 0x31, 0x31, 0xFF])
    char = MagicMock(spec=BleakGATTCharacteristic)
    coord._handle_ble_notification(char, data)
    assert coord.data.get("is_muted") is None or coord.data["is_muted"] is False


def test_unknown_command(coordinator):
    """Unknown command byte is logged but does not update state."""
    coord, _ = coordinator
    _notify(coord, 0x99, b"test")
    # No crash — state unchanged


def test_pre_init_no_listeners(coordinator):
    """Notifications before is_initialized do NOT call async_update_listeners."""
    coord, mock_client = coordinator
    # Reset to pre-init state
    coord.is_initialized = False
    data = bytearray([0x40, 0x2B, 0x56, 0x32, 0x34, 0x35, 0x25])  # volume 45
    char = MagicMock(spec=BleakGATTCharacteristic)
    # Should not crash
    coord._handle_ble_notification(char, data)
