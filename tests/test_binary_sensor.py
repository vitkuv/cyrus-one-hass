"""Tests for HeadphonesSensor entity."""

from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.const import EntityCategory


async def test_is_on(hass, mock_coordinator):
    """is_on returns True when headphones are connected."""
    coord = mock_coordinator
    coord.data["is_headphones_connected"] = True
    from custom_components.cyrus_one.binary_sensor import HeadphonesSensor

    entity = HeadphonesSensor(coord, coord.config_entry)
    assert entity.is_on is True


async def test_is_off(hass, mock_coordinator):
    """is_on returns False when headphones are not connected."""
    coord = mock_coordinator
    coord.data["is_headphones_connected"] = False
    from custom_components.cyrus_one.binary_sensor import HeadphonesSensor

    entity = HeadphonesSensor(coord, coord.config_entry)
    assert entity.is_on is False


async def test_device_class(hass, mock_coordinator):
    """Device class is PLUG."""
    coord = mock_coordinator
    from custom_components.cyrus_one.binary_sensor import HeadphonesSensor

    entity = HeadphonesSensor(coord, coord.config_entry)
    assert entity.device_class == BinarySensorDeviceClass.PLUG


async def test_entity_category(hass, mock_coordinator):
    """Entity category is DIAGNOSTIC."""
    coord = mock_coordinator
    from custom_components.cyrus_one.binary_sensor import HeadphonesSensor

    entity = HeadphonesSensor(coord, coord.config_entry)
    assert entity.entity_category == EntityCategory.DIAGNOSTIC
