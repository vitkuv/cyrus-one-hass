from typing import Any

from homeassistant.components.bluetooth import BluetoothServiceInfoBleak
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult

from . import const


class CyrusOneConfigFlow(ConfigFlow, domain=const.DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._discovery_info: BluetoothServiceInfoBleak | None = None

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        return self.async_abort(reason="manual_not_supported")

    async def async_step_bluetooth(
        self, discovery_info: BluetoothServiceInfoBleak
    ) -> ConfigFlowResult:
        self._discovery_info = discovery_info
        self.context["title_placeholders"] = {"name": discovery_info.name}
        unique_id = f"cyrus_{discovery_info.name.replace('-', '_')}".lower()

        await self.async_set_unique_id(unique_id)
        self._abort_if_unique_id_configured()
        return await self.async_step_discovery_confirm()

    async def async_step_discovery_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(
                title=f"Cyrus {self._discovery_info.name}",
                data={const.CONF_BLE_NAME: self._discovery_info.name},
            )

        return self.async_show_form(
            step_id="discovery_confirm",
            last_step=True,
            description_placeholders={"name": self._discovery_info.name},
        )
