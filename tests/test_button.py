"""Tests for BrightnessUpButton and BrightnessDownButton entities."""


async def test_brightness_up_press(hass, mock_coordinator):
    """async_press on BrightnessUpButton calls coordinator.set_brightness_up."""
    coord = mock_coordinator
    from custom_components.cyrus_one.button import BrightnessUpButton

    entity = BrightnessUpButton(coord)
    await entity.async_press()
    coord.set_brightness_up.assert_awaited_once()


async def test_brightness_down_press(hass, mock_coordinator):
    """async_press on BrightnessDownButton calls coordinator.set_brightness_down."""
    coord = mock_coordinator
    from custom_components.cyrus_one.button import BrightnessDownButton

    entity = BrightnessDownButton(coord)
    await entity.async_press()
    coord.set_brightness_down.assert_awaited_once()


async def test_unique_id_up(hass, mock_coordinator):
    """BrightnessUpButton has the correct unique_id."""
    coord = mock_coordinator
    from custom_components.cyrus_one.button import BrightnessUpButton

    entity = BrightnessUpButton(coord)
    assert entity.unique_id == "cyrus_one_12345_brightness_up"


async def test_unique_id_down(hass, mock_coordinator):
    """BrightnessDownButton has the correct unique_id."""
    coord = mock_coordinator
    from custom_components.cyrus_one.button import BrightnessDownButton

    entity = BrightnessDownButton(coord)
    assert entity.unique_id == "cyrus_one_12345_brightness_down"
