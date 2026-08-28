"""Async REST client for the FrameCast API."""
from __future__ import annotations

from typing import Any

import aiohttp


class FrameCastApiError(Exception):
    """Raised on non-2xx responses or transport errors."""


class FrameCastAuthError(FrameCastApiError):
    """Raised on 401/403 responses — API key is missing or invalid."""


class FrameCastClient:
    def __init__(self, session: aiohttp.ClientSession, base_url: str, api_key: str) -> None:
        self._session = session
        self._base = base_url.rstrip("/")
        self._headers = {
            "Authorization": f"Api-Key {api_key}",
            "Accept": "application/json",
        }

    async def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        url = f"{self._base}{path}"
        try:
            async with self._session.request(
                method, url, headers=self._headers, timeout=aiohttp.ClientTimeout(total=15), **kwargs
            ) as resp:
                if resp.status in (401, 403):
                    raise FrameCastAuthError(f"{resp.status} on {path}")
                if resp.status >= 400:
                    text = await resp.text()
                    raise FrameCastApiError(f"{resp.status} on {path}: {text[:200]}")
                if resp.status == 204:
                    return None
                return await resp.json()
        except aiohttp.ClientError as err:
            raise FrameCastApiError(str(err)) from err

    async def _paginated(self, path: str) -> list[dict[str, Any]]:
        data = await self._request("GET", path)
        return data.get("results", data) if isinstance(data, dict) else data

    async def list_devices(self) -> list[dict[str, Any]]:
        return await self._paginated("/api/v1/devices/")

    async def list_rules(self) -> list[dict[str, Any]]:
        return await self._paginated("/api/v1/rules/")

    async def list_announcements(self) -> list[dict[str, Any]]:
        return await self._paginated("/api/v1/announcements/")

    async def list_companions(self) -> list[dict[str, Any]]:
        return await self._paginated("/api/v1/companions/")

    async def get_current_image(self, device_id: str) -> dict[str, Any] | None:
        """Latest delivered image + art metadata for a Frame, or None."""
        data = await self._request("GET", f"/api/v1/devices/{device_id}/current_image/")
        return data.get("image") if isinstance(data, dict) else None

    async def push_image(self, device_id: str, image_id: int) -> dict[str, Any]:
        return await self._request(
            "POST",
            f"/api/v1/devices/{device_id}/push/",
            json={"image_id": image_id},
        )

    async def wake_device(self, device_id: str) -> dict[str, Any]:
        return await self._request("POST", f"/api/v1/devices/{device_id}/wake/")

    async def sleep_device(self, device_id: str) -> dict[str, Any]:
        return await self._request("POST", f"/api/v1/devices/{device_id}/sleep/")

    async def poll_device(self, device_id: str) -> dict[str, Any]:
        return await self._request("POST", f"/api/v1/devices/{device_id}/poll/")

    async def sync_source(self, source_id: int) -> dict[str, Any]:
        return await self._request("POST", f"/api/v1/sources/{source_id}/sync/")

    async def trigger_rule(self, rule_id: int, payload: dict | None = None) -> dict[str, Any]:
        return await self._request(
            "POST", f"/api/v1/rules/{rule_id}/trigger/", json=payload or {}
        )

    async def trigger_announcement(self, announcement_id: int) -> dict[str, Any]:
        return await self._request(
            "POST", f"/api/v1/announcements/{announcement_id}/trigger/"
        )
