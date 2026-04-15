"""One button per ContentRule + one per Announcement."""
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
    for rule_id, rule in coordinator.data["rules"].items():
        entities.append(FrameCastRuleButton(coordinator, rule_id, rule["name"]))
    for ann_id, ann in coordinator.data["announcements"].items():
        entities.append(FrameCastAnnouncementButton(coordinator, ann_id, ann["name"]))
    async_add_entities(entities)


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
