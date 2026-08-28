"""Per-FrameTV Wake/Sleep/Poll buttons + one per ContentRule + one per Announcement."""
from __future__ import annotations

from homeassistant.components.button import ButtonEntity
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
    entities: list[ButtonEntity] = []
    for device_id, device in coordinator.data["devices"].items():
        name = device.get("name") or f"Frame {device_id[:8]}"
        entities.append(FrameCastWakeButton(coordinator, device_id, name))
        entities.append(FrameCastSleepButton(coordinator, device_id, name))
        entities.append(FrameCastPollButton(coordinator, device_id, name))
    for rule_id, rule in coordinator.data["rules"].items():
        entities.append(FrameCastRuleButton(coordinator, rule_id, rule["name"]))
    for ann_id, ann in coordinator.data["announcements"].items():
        entities.append(FrameCastAnnouncementButton(coordinator, ann_id, ann["name"]))
    async_add_entities(entities)


class _DeviceButtonBase(CoordinatorEntity[FrameCastCoordinator], ButtonEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator: FrameCastCoordinator, device_id: str, device_name: str) -> None:
        super().__init__(coordinator)
        self._device_id = device_id
        self._device_name = device_name


class FrameCastWakeButton(_DeviceButtonBase):
    _attr_icon = "mdi:weather-sunny"

    def __init__(self, coordinator: FrameCastCoordinator, device_id: str, device_name: str) -> None:
        super().__init__(coordinator, device_id, device_name)
        self._attr_name = f"{device_name} Wake"
        self._attr_unique_id = f"framecast_device_{device_id}_wake"

    async def async_press(self) -> None:
        await self.coordinator.client.wake_device(self._device_id)


class FrameCastSleepButton(_DeviceButtonBase):
    _attr_icon = "mdi:weather-night"

    def __init__(self, coordinator: FrameCastCoordinator, device_id: str, device_name: str) -> None:
        super().__init__(coordinator, device_id, device_name)
        self._attr_name = f"{device_name} Sleep"
        self._attr_unique_id = f"framecast_device_{device_id}_sleep"

    async def async_press(self) -> None:
        await self.coordinator.client.sleep_device(self._device_id)


class FrameCastPollButton(_DeviceButtonBase):
    _attr_icon = "mdi:reload"
    _attr_entity_registry_enabled_default = False  # diagnostic; off by default

    def __init__(self, coordinator: FrameCastCoordinator, device_id: str, device_name: str) -> None:
        super().__init__(coordinator, device_id, device_name)
        self._attr_name = f"{device_name} Poll"
        self._attr_unique_id = f"framecast_device_{device_id}_poll"

    async def async_press(self) -> None:
        await self.coordinator.client.poll_device(self._device_id)


class FrameCastRuleButton(CoordinatorEntity[FrameCastCoordinator], ButtonEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator: FrameCastCoordinator, rule_id: str, name: str) -> None:
        super().__init__(coordinator)
        self._rule_id = rule_id
        self._attr_name = f"Rule: {name}"
        self._attr_unique_id = f"framecast_rule_{rule_id}"

    async def async_press(self) -> None:
        await self.coordinator.client.trigger_rule(int(self._rule_id))


class FrameCastAnnouncementButton(CoordinatorEntity[FrameCastCoordinator], ButtonEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator: FrameCastCoordinator, ann_id: str, name: str) -> None:
        super().__init__(coordinator)
        self._ann_id = ann_id
        self._attr_name = f"Announcement: {name}"
        self._attr_unique_id = f"framecast_announcement_{ann_id}"

    async def async_press(self) -> None:
        await self.coordinator.client.trigger_announcement(int(self._ann_id))
