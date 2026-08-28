"""FrameCast integration setup."""
from __future__ import annotations

import logging
import uuid
from collections.abc import Awaitable, Callable

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv

from .api import FrameCastApiError, FrameCastClient
from .const import (
    ATTR_DEVICE_ID,
    ATTR_IMAGE_ID,
    ATTR_RULE_ID,
    ATTR_SOURCE_ID,
    CONF_API_KEY,
    CONF_URL,
    DEVICE_TARGET_ALL,
    DOMAIN,
    PLATFORMS,
    SERVICE_POLL_DEVICE,
    SERVICE_SEND_IMAGE,
    SERVICE_SLEEP_DEVICE,
    SERVICE_SYNC_SOURCE,
    SERVICE_TRIGGER_RULE,
    SERVICE_WAKE_DEVICE,
)
from .coordinator import FrameCastCoordinator

_LOGGER = logging.getLogger(__name__)

SEND_IMAGE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_DEVICE_ID): cv.string,
        vol.Required(ATTR_IMAGE_ID): vol.Coerce(int),
    }
)
WAKE_SCHEMA = vol.Schema({vol.Required(ATTR_DEVICE_ID): cv.string})
SLEEP_SCHEMA = vol.Schema({vol.Required(ATTR_DEVICE_ID): cv.string})
POLL_SCHEMA = vol.Schema({vol.Required(ATTR_DEVICE_ID): cv.string})
TRIGGER_RULE_SCHEMA = vol.Schema({vol.Required(ATTR_RULE_ID): vol.Coerce(int)})
SYNC_SOURCE_SCHEMA = vol.Schema({vol.Required(ATTR_SOURCE_ID): vol.Coerce(int)})


# ─── device_id resolution ───────────────────────────────────────────────────
#
# `device_id` accepts three forms, in this precedence order:
#   1. "all"        — every device across every configured FrameCast entry
#   2. a UUID       — the original addressing mode, unchanged
#   3. a name       — case-insensitive match on FrameTV.name ("Living Room")
#
# Names are matched *after* IDs so an automation written against a UUID can
# never be hijacked by someone naming a device after that UUID. Resolution
# reads the coordinator cache, which the sensors already keep warm; no extra
# API round-trip is spent turning a name into an ID.


def _coordinators(hass: HomeAssistant) -> list[FrameCastCoordinator]:
    return list(hass.data.get(DOMAIN, {}).values())


def _devices_of(coordinator: FrameCastCoordinator) -> dict[str, dict]:
    return (coordinator.data or {}).get("devices", {})


def _label(coordinator: FrameCastCoordinator, device_id: str) -> str:
    """Human-readable target for log/error text."""
    device = _devices_of(coordinator).get(device_id) or {}
    return device.get("name") or device_id


def _known_names(hass: HomeAssistant) -> list[str]:
    return sorted(
        (d.get("name") or "").strip()
        for c in _coordinators(hass)
        for d in _devices_of(c).values()
        if (d.get("name") or "").strip()
    )


def _resolve_targets(
    hass: HomeAssistant, raw: str
) -> list[tuple[FrameCastCoordinator, str]]:
    """Map a `device_id` field to concrete (coordinator, uuid) targets.

    Returns pairs rather than bare IDs so each call goes out on the client of
    the entry that actually owns the device — with two FrameCast servers
    configured, sending every request through one of them would silently 404.
    """
    value = str(raw).strip()
    coordinators = _coordinators(hass)

    if value.casefold() == DEVICE_TARGET_ALL:
        targets = [(c, dev_id) for c in coordinators for dev_id in _devices_of(c)]
        if not targets:
            raise ServiceValidationError(
                "device_id: 'all' matched nothing — FrameCast reported no devices."
            )
        return targets

    for coordinator in coordinators:
        if value in _devices_of(coordinator):
            return [(coordinator, value)]

    matches = [
        (coordinator, dev_id)
        for coordinator in coordinators
        for dev_id, device in _devices_of(coordinator).items()
        if (device.get("name") or "").strip().casefold() == value.casefold()
    ]
    if len(matches) == 1:
        return matches
    if len(matches) > 1:
        raise ServiceValidationError(
            f"device_id: {value!r} matches {len(matches)} FrameCast devices. "
            "Rename one, or use the device's UUID to disambiguate."
        )

    # Not in the cache. A well-formed UUID is still forwarded: the device may
    # have been added since the last coordinator refresh, and the server — not
    # this cache — is the authority on what exists. A non-UUID string that
    # matched no name is a typo, and saying so beats a 404 from the API.
    try:
        uuid.UUID(value)
    except ValueError:
        pass
    else:
        if coordinators:
            return [(coordinators[0], value)]

    known = ", ".join(repr(n) for n in _known_names(hass))
    raise ServiceValidationError(
        f"device_id: no FrameCast device named {value!r}. "
        f"Known devices: {known or '(none)'}. You can also pass a device UUID, "
        f"or '{DEVICE_TARGET_ALL}' to target every device."
    )


async def _fan_out(
    hass: HomeAssistant,
    raw: str,
    service: str,
    action: Callable[[FrameCastClient, str], Awaitable[object]],
) -> None:
    """Run `action` against every resolved target, one at a time.

    Targets are attempted independently: with `device_id: all`, one Frame that
    is unplugged must not stop the others from being told. Failures are
    collected and raised together at the end so the call still reports as
    failed in HA rather than silently half-succeeding.
    """
    targets = _resolve_targets(hass, raw)
    errors: list[str] = []
    for coordinator, device_id in targets:
        try:
            await action(coordinator.client, device_id)
        except FrameCastApiError as err:
            errors.append(f"{_label(coordinator, device_id)}: {err}")

    if errors:
        raise HomeAssistantError(
            f"{service} failed for {len(errors)} of {len(targets)} device(s) — "
            + "; ".join(errors)
        )


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    session = async_get_clientsession(hass)
    client = FrameCastClient(session, entry.data[CONF_URL], entry.data[CONF_API_KEY])
    coordinator = FrameCastCoordinator(hass, client)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    async def _send_image(call: ServiceCall) -> None:
        image_id = call.data[ATTR_IMAGE_ID]
        await _fan_out(
            hass, call.data[ATTR_DEVICE_ID], SERVICE_SEND_IMAGE,
            lambda c, dev_id: c.push_image(dev_id, image_id),
        )

    async def _wake(call: ServiceCall) -> None:
        await _fan_out(
            hass, call.data[ATTR_DEVICE_ID], SERVICE_WAKE_DEVICE,
            lambda c, dev_id: c.wake_device(dev_id),
        )

    async def _sleep(call: ServiceCall) -> None:
        await _fan_out(
            hass, call.data[ATTR_DEVICE_ID], SERVICE_SLEEP_DEVICE,
            lambda c, dev_id: c.sleep_device(dev_id),
        )

    async def _poll_device(call: ServiceCall) -> None:
        await _fan_out(
            hass, call.data[ATTR_DEVICE_ID], SERVICE_POLL_DEVICE,
            lambda c, dev_id: c.poll_device(dev_id),
        )

    async def _trigger_rule(call: ServiceCall) -> None:
        await client.trigger_rule(call.data[ATTR_RULE_ID])

    async def _sync_source(call: ServiceCall) -> None:
        await client.sync_source(call.data[ATTR_SOURCE_ID])

    hass.services.async_register(DOMAIN, SERVICE_SEND_IMAGE, _send_image, schema=SEND_IMAGE_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_WAKE_DEVICE, _wake, schema=WAKE_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_SLEEP_DEVICE, _sleep, schema=SLEEP_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_TRIGGER_RULE, _trigger_rule, schema=TRIGGER_RULE_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_POLL_DEVICE, _poll_device, schema=POLL_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_SYNC_SOURCE, _sync_source, schema=SYNC_SOURCE_SCHEMA)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
        if not hass.data[DOMAIN]:
            for svc in (
                SERVICE_SEND_IMAGE, SERVICE_WAKE_DEVICE, SERVICE_SLEEP_DEVICE,
                SERVICE_TRIGGER_RULE, SERVICE_POLL_DEVICE, SERVICE_SYNC_SOURCE,
            ):
                hass.services.async_remove(DOMAIN, svc)
    return unload_ok
