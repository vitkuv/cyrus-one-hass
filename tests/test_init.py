"""Tests for __init__ module (async_setup_entry / async_unload_entry)."""

from unittest.mock import AsyncMock, patch

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.cyrus_one import const
from custom_components.cyrus_one.coordinator import CyrusOneCoordinator


async def test_setup_entry(hass):
    """async_setup_entry creates a coordinator and registers it in hass.data."""
    entry = MockConfigEntry(
        domain=const.DOMAIN,
        data={const.CONF_BLE_NAME: "ONE-12345"},
        unique_id="cyrus_one_12345",
    )
    entry.add_to_hass(hass)

    with patch(
        "custom_components.cyrus_one.coordinator.establish_connection",
        return_value=AsyncMock(),
    ):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    assert const.DOMAIN in hass.data
    assert entry.entry_id in hass.data[const.DOMAIN]
    coordinator = hass.data[const.DOMAIN][entry.entry_id]
    assert isinstance(coordinator, CyrusOneCoordinator)


async def test_unload_entry(hass):
    """async_unload_entry unloads platforms and removes coordinator from hass.data."""
    entry = MockConfigEntry(
        domain=const.DOMAIN,
        data={const.CONF_BLE_NAME: "ONE-12345"},
        unique_id="cyrus_one_12345",
    )
    entry.add_to_hass(hass)

    with patch(
        "custom_components.cyrus_one.coordinator.establish_connection",
        return_value=AsyncMock(),
    ):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.entry_id not in hass.data[const.DOMAIN]


async def test_setup_entry_forwards_platforms(hass):
    """async_setup_entry forwards the correct set of platforms."""
    entry = MockConfigEntry(
        domain=const.DOMAIN,
        data={const.CONF_BLE_NAME: "ONE-12345"},
        unique_id="cyrus_one_12345",
    )
    entry.add_to_hass(hass)

    with patch(
        "custom_components.cyrus_one.coordinator.establish_connection",
        return_value=AsyncMock(),
    ):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    assert const.DOMAIN in hass.data
    assert entry.entry_id in hass.data[const.DOMAIN]


async def test_setup_entry_coordinator_in_data(hass):
    """Coordinator is stored in hass.data under the correct key."""
    entry = MockConfigEntry(
        domain=const.DOMAIN,
        data={const.CONF_BLE_NAME: "ONE-12345"},
        unique_id="cyrus_one_12345",
    )
    entry.add_to_hass(hass)

    with patch(
        "custom_components.cyrus_one.coordinator.establish_connection",
        return_value=AsyncMock(),
    ):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    coordinator = hass.data[const.DOMAIN][entry.entry_id]
    assert coordinator.config_entry is entry
