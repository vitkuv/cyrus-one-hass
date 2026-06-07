from homeassistant.components.number import NumberDeviceClass, NumberEntity
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

    async_add_entities([BalanceNumber(coordinator)])

    return True


class BalanceNumber(CyrusOneCoordinatorEntity, NumberEntity):
    _attr_entity_category = EntityCategory.CONFIG
    _attr_device_class = NumberDeviceClass.SOUND_PRESSURE
    _attr_unique_id_suffix = "_balance"
    _attr_icon = "mdi:tune"
    _attr_has_entity_name = True
    _attr_translation_key = "balance"
    _attr_native_min_value = 0.0
    _attr_native_max_value = 20.0
    _attr_native_step = 1.0

    @property
    def available(self):
        if not self.coordinator.available:
            return False

        data = self.coordinator.data
        if data.get("is_headphones_connected"):
            return False

        if data.get("source") == const.SOURCE_AV and data.get("is_av_direct_enabled"):
            return False

        return True

    @property
    def native_value(self) -> float | None:
        value = self.coordinator.data.get("balance")
        if value is not None:
            return float(value)
        return None

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.set_balance(int(value))
