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
            companions = await self.client.list_companions()
        except FrameCastApiError as err:
            raise UpdateFailed(str(err)) from err

        # Fan out one current_image fetch per device. List is small (homes
        # typically have 1-3 Frames), and the data drives the art-metadata
        # attributes on each device sensor. A single failed fetch should not
        # tank the whole update — we surface None for that device.
        current_images: dict[str, dict[str, Any] | None] = {}
        for d in devices:
            try:
                current_images[str(d["id"])] = await self.client.get_current_image(d["id"])
            except FrameCastApiError:
                current_images[str(d["id"])] = None

        return {
            "devices": {str(d["id"]): d for d in devices},
            "rules": {str(r["id"]): r for r in rules if r.get("is_active", True)},
            "announcements": {str(a["id"]): a for a in announcements},
            "companions": {str(c["id"]): c for c in companions},
            "current_images": current_images,
        }
