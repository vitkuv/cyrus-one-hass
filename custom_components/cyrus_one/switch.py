from homeassistant.components.switch import SwitchDeviceClass, SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import const
from .coordinator import CyrusOneCoordinator, CyrusOneCoordinatorEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> bool:
    coordinator: CyrusOneCoordinator = hass.data[const.DOMAIN][entry.entry_id]

    async_add_entities([AVDirectSwitch(coordinator)])

    return True


class AVDirectSwitch(CyrusOneCoordinatorEntity, SwitchEntity):
    _attr_entity_category = EntityCategory.CONFIG
    _attr_device_class = SwitchDeviceClass.SWITCH
    _attr_unique_id_suffix = "av_direct"
    _attr_icon = "mdi:audio-video"
    _attr_name = "AV Direct"

    @property
    def available(self) -> bool:
        return super().available and self.coordinator.data.get("source") == const.SOURCE_AV

    @property
    def is_on(self) -> bool:
        return self.coordinator.data.get("is_av_direct_enabled")

    async def async_turn_on(self) -> None:
        await self.coordinator.set_av_direct(enabled=True)

    async def async_turn_off(self) -> None:
        await self.coordinator.set_av_direct(enabled=False)
