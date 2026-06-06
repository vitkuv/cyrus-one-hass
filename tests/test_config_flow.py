"""Tests for CyrusOneConfigFlow."""

from unittest.mock import MagicMock

from homeassistant.components.bluetooth import BluetoothServiceInfoBleak
from homeassistant.config_entries import SOURCE_BLUETOOTH, SOURCE_USER
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.cyrus_one import const


def _make_discovery_info(name="ONE-12345", address="AA:BB:CC:DD:EE:FF"):
    device = MagicMock()
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
        time=100.0,
        tx_power=-127,
    )


async def test_user_step_aborts(hass):
    """Manual setup via user step is aborted with reason."""
    result = await hass.config_entries.flow.async_init(
        const.DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] == "abort"
    assert result["reason"] == "manual_not_supported"


async def test_bluetooth_step(hass):
    """Bluetooth discovery creates a unique_id and shows confirmation form."""
    result = await hass.config_entries.flow.async_init(
        const.DOMAIN,
        context={"source": SOURCE_BLUETOOTH},
        data=_make_discovery_info(),
    )
    assert result["type"] == "form"
    assert result["step_id"] == "discovery_confirm"
    assert result["description_placeholders"]["name"] == "ONE-12345"
    assert result["flow_id"] is not None


async def test_bluetooth_duplicate_abort(hass):
    """When the same device is already configured, bluetooth discovery aborts."""
    entry = MockConfigEntry(
        domain=const.DOMAIN,
        data={const.CONF_BLE_NAME: "ONE-12345"},
        unique_id="cyrus_one_12345",
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        const.DOMAIN,
        context={"source": SOURCE_BLUETOOTH},
        data=_make_discovery_info(),
    )
    assert result["type"] == "abort"
    assert result["reason"] == "already_configured"


async def test_discovery_confirm_form(hass):
    """Discovery confirmation form is shown with correct placeholders."""
    result = await hass.config_entries.flow.async_init(
        const.DOMAIN,
        context={"source": SOURCE_BLUETOOTH},
        data=_make_discovery_info(),
    )
    assert result["step_id"] == "discovery_confirm"
    assert result["description_placeholders"]["name"] == "ONE-12345"


async def test_discovery_confirm_create_entry(hass):
    """Confirming discovery creates a config entry."""
    result = await hass.config_entries.flow.async_init(
        const.DOMAIN,
        context={"source": SOURCE_BLUETOOTH},
        data=_make_discovery_info(),
    )
    result = await hass.config_entries.flow.async_configure(result["flow_id"], user_input={})
    assert result["type"] == "create_entry"
    assert result["title"] == "Cyrus ONE-12345"
    assert result["data"][const.CONF_BLE_NAME] == "ONE-12345"
