"""Sensors: one per FrameTV device, plus one per CompanionScreen."""
from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import FrameCastCoordinator


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: FrameCastCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[SensorEntity] = [
        FrameCastDeviceStatusSensor(coordinator, device_id)
        for device_id in coordinator.data["devices"]
    ]
    for companion_id in coordinator.data.get("companions", {}):
        entities.append(FrameCastCompanionSensor(coordinator, companion_id))
    async_add_entities(entities)


class FrameCastDeviceStatusSensor(CoordinatorEntity[FrameCastCoordinator], SensorEntity):
    _attr_has_entity_name = True
    _attr_icon = "mdi:television-ambient-light"

    def __init__(self, coordinator: FrameCastCoordinator, device_id: str) -> None:
        super().__init__(coordinator)
        self._device_id = device_id
        device = coordinator.data["devices"][device_id]
        self._attr_name = f"{device['name']} status"
        self._attr_unique_id = f"framecast_device_{device_id}_status"

    @property
    def native_value(self) -> str | None:
        device = self.coordinator.data["devices"].get(self._device_id)
        return device.get("status") if device else None

    @property
    def extra_state_attributes(self) -> dict:
        device = self.coordinator.data["devices"].get(self._device_id) or {}
        attrs: dict = {
            "ip_address": device.get("ip_address"),
            "mac_address": device.get("mac_address"),
            "current_content_id": device.get("current_content_id"),
            # Frame art-mode brightness is 0–10 (not 0–100). Surfaced as-is.
            "brightness": device.get("brightness"),
            "matte_id": device.get("matte_id"),
            "last_seen": device.get("last_seen"),
            # Quiet-hours config + live state. start/end are "HH:MM:SS" in the
            # Frame's configured timezone; quiet_hours_active is the in-window
            # flag toggled by the enforce_quiet_hours periodic task.
            "quiet_hours_enabled": device.get("quiet_hours_enabled"),
            "quiet_hours_start": device.get("quiet_hours_start"),
            "quiet_hours_end": device.get("quiet_hours_end"),
            "quiet_hours_brightness": device.get("quiet_hours_brightness"),
            "quiet_hours_active": device.get("quiet_hours_sleep_state"),
        }
        # Surface the currently-displayed artwork's metadata so automations can
        # branch on title/artist/year (e.g. announce on a smart speaker when a
        # specific piece comes up).
        current = (self.coordinator.data.get("current_images") or {}).get(self._device_id)
        if current:
            attrs.update({
                "current_title": current.get("title") or current.get("display_name"),
                "current_artist": current.get("artist"),
                "current_year": current.get("year"),
                "current_medium": current.get("medium"),
                "current_description": current.get("description"),
                "current_image_id": current.get("id"),
                "current_image_url": current.get("file_url"),
                "current_is_favorite": current.get("is_favorite"),
            })
        return attrs


class FrameCastCompanionSensor(CoordinatorEntity[FrameCastCoordinator], SensorEntity):
    """Status sensor for a paired tiny_canvas / companion screen.

    State is the power_mode (always_on | battery). Attributes expose the poll
    interval, schedule-follow flag, and last-sync timestamps so an automation
    can alert when a battery device hasn't checked in.
    """
    _attr_has_entity_name = True
    _attr_icon = "mdi:tablet-dashboard"

    def __init__(self, coordinator: FrameCastCoordinator, companion_id: str) -> None:
        super().__init__(coordinator)
        self._companion_id = companion_id
        c = coordinator.data["companions"][companion_id]
        frame_label = c.get("frame_name") or "Frame"
        self._attr_name = f"{c['name']} ({frame_label})"
        self._attr_unique_id = f"framecast_companion_{companion_id}"

    @property
    def native_value(self) -> str | None:
        c = self.coordinator.data.get("companions", {}).get(self._companion_id)
        return c.get("power_mode") if c else None

    @property
    def extra_state_attributes(self) -> dict:
        c = self.coordinator.data.get("companions", {}).get(self._companion_id) or {}
        return {
            "frame_id": c.get("frame"),
            "frame_name": c.get("frame_name"),
            "mqtt_topic": c.get("mqtt_topic"),
            "mac_address": c.get("mac_address"),
            "is_active": c.get("is_active"),
            "poll_interval_minutes": c.get("poll_interval_minutes"),
            "follow_frame_schedule": c.get("follow_frame_schedule"),
            "last_synced_at": c.get("last_synced_at"),
            "last_published_at": c.get("last_published_at"),
            "last_seen": c.get("last_seen"),
            "last_publish_error": c.get("last_publish_error"),
        }
