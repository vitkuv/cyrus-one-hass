from homeassistant.components.button import ButtonEntity
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

    async_add_entities(
        [
            BrightnessUpButton(coordinator),
            BrightnessDownButton(coordinator),
        ]
    )
    return True


class BrightnessUpButton(CyrusOneCoordinatorEntity, ButtonEntity):
    _attr_entity_category = EntityCategory.CONFIG
    _attr_unique_id_suffix = "brightness_up"
    _attr_icon = "mdi:brightness-7"
    _attr_name = "Brightness Up"

    async def async_press(self) -> None:
        await self.coordinator.set_brightness_up()


class BrightnessDownButton(CyrusOneCoordinatorEntity, ButtonEntity):
    _attr_entity_category = EntityCategory.CONFIG
    _attr_unique_id_suffix = "brightness_down"
    _attr_icon = "mdi:brightness-4"
    _attr_name = "Brightness Down"

    async def async_press(self) -> None:
        await self.coordinator.set_brightness_down()
