"""Polls FrameCast for devices, rules, and announcements."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import FrameCastApiError, FrameCastClient
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class FrameCastCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    def __init__(self, hass: HomeAssistant, client: FrameCastClient) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=DEFAULT_SCAN_INTERVAL,
        )
        self.client = client

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            devices = await self.client.list_devices()
            rules = await self.client.list_rules()
            announcements = await self.client.list_announcements()
        except FrameCastApiError as err:
            raise UpdateFailed(str(err)) from err
        return {
            "devices": {str(d["id"]): d for d in devices},
            "rules": {str(r["id"]): r for r in rules if r.get("is_active", True)},
            "announcements": {str(a["id"]): a for a in announcements},
        }
