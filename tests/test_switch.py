"""Tests for AVDirectSwitch entity."""

from custom_components.cyrus_one import const


async def test_turn_on_calls_coordinator(hass, mock_coordinator):
    """async_turn_on calls coordinator.set_av_direct(True)."""
    coord = mock_coordinator
    from custom_components.cyrus_one.switch import AVDirectSwitch

    entity = AVDirectSwitch(coord)
    await entity.async_turn_on()
    coord.set_av_direct.assert_awaited_once_with(enabled=True)


async def test_turn_off_calls_coordinator(hass, mock_coordinator):
    """async_turn_off calls coordinator.set_av_direct(False)."""
    coord = mock_coordinator
    from custom_components.cyrus_one.switch import AVDirectSwitch

    entity = AVDirectSwitch(coord)
    await entity.async_turn_off()
    coord.set_av_direct.assert_awaited_once_with(enabled=False)


async def test_is_on(hass, mock_coordinator):
    """is_on returns is_av_direct_enabled from coordinator data."""
    coord = mock_coordinator
    coord.data["is_av_direct_enabled"] = True
    from custom_components.cyrus_one.switch import AVDirectSwitch

    entity = AVDirectSwitch(coord)
    assert entity.is_on is True


async def test_available_av_source(hass, mock_coordinator):
    """Available is True when source is AV and coordinator is available."""
    coord = mock_coordinator
    coord.data["source"] = const.SOURCE_AV
    from custom_components.cyrus_one.switch import AVDirectSwitch

    entity = AVDirectSwitch(coord)
    assert entity.available is True


async def test_unavailable_non_av_source(hass, mock_coordinator):
    """Available is False when source is not AV."""
    coord = mock_coordinator
    coord.data["source"] = const.SOURCE_BLUETOOTH
    from custom_components.cyrus_one.switch import AVDirectSwitch

    entity = AVDirectSwitch(coord)
    assert entity.available is False


async def test_unavailable_coordinator(hass, mock_coordinator):
    """Available is False when coordinator is unavailable."""
    coord = mock_coordinator
    coord.data["source"] = const.SOURCE_AV
    coord.available = False
    from custom_components.cyrus_one.switch import AVDirectSwitch

    entity = AVDirectSwitch(coord)
    assert entity.available is False
