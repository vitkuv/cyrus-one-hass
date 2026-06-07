"""Tests for BalanceNumber entity."""

from custom_components.cyrus_one import const


async def test_native_value(hass, mock_coordinator):
    """native_value returns balance as float."""
    coord = mock_coordinator
    coord.data["balance"] = 10
    from custom_components.cyrus_one.number import BalanceNumber

    entity = BalanceNumber(coord)
    assert entity.native_value == 10.0


async def test_native_value_none(hass, mock_coordinator):
    """native_value returns None when balance is not set."""
    coord = mock_coordinator
    coord.data["balance"] = None
    from custom_components.cyrus_one.number import BalanceNumber

    entity = BalanceNumber(coord)
    assert entity.native_value is None


async def test_set_native_value(hass, mock_coordinator):
    """async_set_native_value calls coordinator.set_balance."""
    coord = mock_coordinator
    from custom_components.cyrus_one.number import BalanceNumber

    entity = BalanceNumber(coord)
    await entity.async_set_native_value(5.0)
    coord.set_balance.assert_awaited_once_with(5)


async def test_available(hass, mock_coordinator):
    """Available is True when headphones not connected and coordinator available."""
    coord = mock_coordinator
    coord.data["is_headphones_connected"] = False
    from custom_components.cyrus_one.number import BalanceNumber

    entity = BalanceNumber(coord)
    assert entity.available is True


async def test_unavailable_headphones(hass, mock_coordinator):
    """Available is False when headphones are connected."""
    coord = mock_coordinator
    coord.data["is_headphones_connected"] = True
    from custom_components.cyrus_one.number import BalanceNumber

    entity = BalanceNumber(coord)
    assert entity.available is False


async def test_unavailable_av_direct(hass, mock_coordinator):
    """Available is False when AV source selected and AV Direct enabled."""
    coord = mock_coordinator
    coord.data["source"] = const.SOURCE_AV
    coord.data["is_av_direct_enabled"] = True
    from custom_components.cyrus_one.number import BalanceNumber

    entity = BalanceNumber(coord)
    assert entity.available is False


async def test_range_step(hass, mock_coordinator):
    """native_min_value, native_max_value, and native_step are correct."""
    coord = mock_coordinator
    from custom_components.cyrus_one.number import BalanceNumber

    entity = BalanceNumber(coord)
    assert entity.native_min_value == 0.0
    assert entity.native_max_value == 20.0
    assert entity.native_step == 1.0
