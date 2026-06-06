"""Tests for BLE message framing (static methods)."""

from custom_components.cyrus_one import const
from custom_components.cyrus_one.coordinator import CyrusOneCoordinator, format_bytes


async def test_ble_create_message_single_byte_payload():
    msg = CyrusOneCoordinator.ble_create_message(const.CMD_MUTE, b"1")
    assert msg == bytes([0x40, 0x2B, 0x4D, 0x31, 0x31, 0x25])


async def test_ble_create_message_two_byte_payload():
    msg = CyrusOneCoordinator.ble_create_message(const.CMD_VOLUME, b"45")
    assert msg == bytes([0x40, 0x2B, 0x56, 0x32, 0x34, 0x35, 0x25])


async def test_ble_create_message_zero_byte_payload():
    msg = CyrusOneCoordinator.ble_create_message(const.CMD_SOURCE, b"")
    assert msg == bytes([0x40, 0x2B, 0x49, 0x30, 0x25])


async def test_ble_create_message_fetch():
    msg = CyrusOneCoordinator.ble_create_message(const.CMD_FETCH, bytes([const.CMD_MUTE]))
    assert msg == bytes([0x40, 0x2B, 0x46, 0x31, 0x4D, 0x25])


async def test_format_bytes():
    assert format_bytes(b"\x40\x2b\x46") == "40 2b 46"
