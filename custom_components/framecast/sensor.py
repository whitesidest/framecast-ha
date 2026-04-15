"""One status sensor per FrameTV device."""
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
    entities = [
        FrameCastDeviceStatusSensor(coordinator, device_id)
        for device_id in coordinator.data["devices"]
    ]
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
        return {
            "ip_address": device.get("ip_address"),
            "current_content_id": device.get("current_content_id"),
            "brightness": device.get("brightness"),
            "last_seen": device.get("last_seen"),
        }
