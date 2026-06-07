from homeassistant.components.media_player import (
    MediaPlayerDeviceClass,
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import const
from .coordinator import CyrusOneCoordinator, CyrusOneCoordinatorEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> bool:
    coordinator: CyrusOneCoordinator = hass.data[const.DOMAIN][entry.entry_id]
    async_add_entities([CyrusOneMediaPlayer(coordinator)])
    return True


class CyrusOneMediaPlayer(CyrusOneCoordinatorEntity, MediaPlayerEntity):
    _attr_unique_id_suffix = "media_player"
    _attr_device_class = MediaPlayerDeviceClass.SPEAKER

    def __init__(self, coordinator: CyrusOneCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_name = f"Cyrus {coordinator.config_entry.data[const.CONF_BLE_NAME]}"

    @property
    def is_volume_disabled(self) -> bool:
        return self.source == const.SOURCE_AV and self.coordinator.data.get("is_av_direct_enabled")

    @property
    def state(self) -> MediaPlayerState | None:
        return MediaPlayerState.ON if self.available else None

    @property
    def is_volume_muted(self) -> bool | None:
        return self.coordinator.data.get("is_muted")

    @property
    def source(self) -> str | None:
        return self.coordinator.data.get("source")

    @property
    def source_list(self) -> tuple[str]:
        return self.coordinator.data["source_list"]

    @property
    def volume_level(self) -> float | None:
        if self.is_volume_disabled:
            return None

        vol = self.coordinator.data.get("volume")
        if vol is None:
            return None
        return max(0, min(90, vol)) / 90.0

    async def async_mute_volume(self, mute: bool) -> None:
        await self.coordinator.set_mute(mute)

    async def async_select_source(self, source: str) -> None:
        await self.coordinator.set_source(source)

    async def async_set_volume_level(self, volume: float) -> None:
        if self.is_volume_disabled:
            return

        vol = round(max(0.0, min(1.0, volume)) * 90)
        await self.coordinator.set_volume(vol)

    @property
    def supported_features(self) -> MediaPlayerEntityFeature:
        features = MediaPlayerEntityFeature.SELECT_SOURCE | MediaPlayerEntityFeature.VOLUME_MUTE
        if not self.is_volume_disabled:
            features |= MediaPlayerEntityFeature.VOLUME_SET
        return features
