"""Tests for CyrusOneMediaPlayer entity."""

from unittest.mock import MagicMock

import pytest
from homeassistant.components.media_player import (
    MediaPlayerEntityFeature,
    MediaPlayerState,
)

from custom_components.cyrus_one import const


async def test_state_on(hass, mock_coordinator):
    """State is ON when available."""
    coord = mock_coordinator
    from custom_components.cyrus_one.media_player import CyrusOneMediaPlayer

    entity = CyrusOneMediaPlayer(coord)
    entity.hass = hass
    assert entity.state == MediaPlayerState.ON


async def test_state_none_when_unavailable(hass, mock_coordinator):
    """State is None when coordinator is unavailable."""
    coord = mock_coordinator
    coord.available = False
    from custom_components.cyrus_one.media_player import CyrusOneMediaPlayer

    entity = CyrusOneMediaPlayer(coord)
    entity.hass = hass
    assert entity.state is None


async def test_volume_mapping(hass, mock_coordinator):
    """Volume 20 is approximated to HA 0.05."""
    coord = mock_coordinator
    coord.data["volume"] = 20
    from custom_components.cyrus_one.media_player import CyrusOneMediaPlayer

    entity = CyrusOneMediaPlayer(coord)
    entity.hass = hass
    assert entity.volume_level == pytest.approx(0.05, abs=0.01)


async def test_volume_av_direct_returns_none(hass, mock_coordinator):
    """When AV Direct is enabled on AV source, volume_level returns 1.0."""
    coord = mock_coordinator
    coord.data["source"] = const.SOURCE_AV
    coord.data["is_av_direct_enabled"] = True
    from custom_components.cyrus_one.media_player import CyrusOneMediaPlayer

    entity = CyrusOneMediaPlayer(coord)
    entity.hass = hass
    assert entity.volume_level is None


async def test_is_muted(hass, mock_coordinator):
    """is_volume_muted returns is_muted from coordinator data."""
    coord = mock_coordinator
    coord.data["is_muted"] = True
    from custom_components.cyrus_one.media_player import CyrusOneMediaPlayer

    entity = CyrusOneMediaPlayer(coord)
    assert entity.is_volume_muted is True


async def test_source(hass, mock_coordinator):
    """Source returns the current source from coordinator data."""
    coord = mock_coordinator
    from custom_components.cyrus_one.media_player import CyrusOneMediaPlayer

    entity = CyrusOneMediaPlayer(coord)
    assert entity.source == const.SOURCE_AV


async def test_source_list(hass, mock_coordinator):
    """source_list returns the full sources tuple."""
    coord = mock_coordinator
    from custom_components.cyrus_one.media_player import CyrusOneMediaPlayer

    entity = CyrusOneMediaPlayer(coord)
    assert entity.source_list == const.SOURCES_CYRUS_ONE


async def test_select_source_calls_coordinator(hass, mock_coordinator):
    """async_select_source calls coordinator.set_source."""
    coord = mock_coordinator
    from custom_components.cyrus_one.media_player import CyrusOneMediaPlayer

    entity = CyrusOneMediaPlayer(coord)
    await entity.async_select_source(const.SOURCE_PHONO)
    coord.set_source.assert_awaited_once_with(const.SOURCE_PHONO)


async def test_set_volume_calls_coordinator(hass, mock_coordinator):
    """async_set_volume_level calls coordinator.set_volume."""
    coord = mock_coordinator
    coord.data["source"] = const.SOURCE_BLUETOOTH
    from custom_components.cyrus_one.media_player import CyrusOneMediaPlayer

    entity = CyrusOneMediaPlayer(coord)
    await entity.async_set_volume_level(0.5)
    coord.set_volume.assert_awaited_once_with(69)


async def test_set_volume_disabled_av_direct(hass, mock_coordinator):
    """async_set_volume_level is a no-op when AV Direct is enabled on AV source."""
    coord = mock_coordinator
    coord.data["source"] = const.SOURCE_AV
    coord.data["is_av_direct_enabled"] = True
    from custom_components.cyrus_one.media_player import CyrusOneMediaPlayer

    entity = CyrusOneMediaPlayer(coord)
    entity.hass = hass
    entity.entity_id = "media_player.test_av_direct"
    entity.platform = MagicMock()
    await entity.async_set_volume_level(0.5)
    coord.set_volume.assert_not_awaited()


async def test_supported_features(hass, mock_coordinator):
    """supported_features includes VOLUME_SET when volume is not disabled."""
    coord = mock_coordinator
    coord.data["source"] = const.SOURCE_BLUETOOTH
    from custom_components.cyrus_one.media_player import CyrusOneMediaPlayer

    entity = CyrusOneMediaPlayer(coord)
    features = entity.supported_features
    assert features & MediaPlayerEntityFeature.VOLUME_SET
    assert features & MediaPlayerEntityFeature.VOLUME_MUTE
    assert features & MediaPlayerEntityFeature.SELECT_SOURCE


async def test_supported_features_no_volume_set(hass, mock_coordinator):
    """supported_features excludes VOLUME_SET when volume is disabled."""
    coord = mock_coordinator
    coord.data["source"] = const.SOURCE_AV
    coord.data["is_av_direct_enabled"] = True
    from custom_components.cyrus_one.media_player import CyrusOneMediaPlayer

    entity = CyrusOneMediaPlayer(coord)
    features = entity.supported_features
    assert not (features & MediaPlayerEntityFeature.VOLUME_SET)
    assert features & MediaPlayerEntityFeature.VOLUME_MUTE
    assert features & MediaPlayerEntityFeature.SELECT_SOURCE


async def test_unique_id(hass, mock_coordinator):
    """unique_id includes the suffix."""
    coord = mock_coordinator
    from custom_components.cyrus_one.media_player import CyrusOneMediaPlayer

    entity = CyrusOneMediaPlayer(coord)
    assert entity.unique_id == "cyrus_one_12345_media_player"
