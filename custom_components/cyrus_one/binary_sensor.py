from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import const
from .coordinator import CyrusOneCoordinator, CyrusOneCoordinatorEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> bool:
    coordinator: CyrusOneCoordinator = hass.data[const.DOMAIN][entry.entry_id]

    async_add_entities([HeadphonesSensor(coordinator, entry)])

    return True


class HeadphonesSensor(CyrusOneCoordinatorEntity, BinarySensorEntity):
    _attr_device_class = BinarySensorDeviceClass.PLUG
    _attr_icon = "mdi:headphones"
    _attr_has_entity_name = True
    _attr_translation_key = "headphones"

    @property
    def is_on(self) -> bool:
        return self.coordinator.data.get("is_headphones_connected", False)
