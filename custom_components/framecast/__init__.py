"""FrameCast integration setup."""
from __future__ import annotations

import logging

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv

from .api import FrameCastClient
from .const import (
    ATTR_DEVICE_ID,
    ATTR_IMAGE_ID,
    ATTR_RULE_ID,
    CONF_API_KEY,
    CONF_URL,
    DOMAIN,
    PLATFORMS,
    SERVICE_SEND_IMAGE,
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
TRIGGER_RULE_SCHEMA = vol.Schema({vol.Required(ATTR_RULE_ID): vol.Coerce(int)})


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    session = async_get_clientsession(hass)
    client = FrameCastClient(session, entry.data[CONF_URL], entry.data[CONF_API_KEY])
    coordinator = FrameCastCoordinator(hass, client)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    async def _send_image(call: ServiceCall) -> None:
        await client.push_image(call.data[ATTR_DEVICE_ID], call.data[ATTR_IMAGE_ID])

    async def _wake(call: ServiceCall) -> None:
        await client.wake_device(call.data[ATTR_DEVICE_ID])

    async def _trigger_rule(call: ServiceCall) -> None:
        await client.trigger_rule(call.data[ATTR_RULE_ID])

    hass.services.async_register(DOMAIN, SERVICE_SEND_IMAGE, _send_image, schema=SEND_IMAGE_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_WAKE_DEVICE, _wake, schema=WAKE_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_TRIGGER_RULE, _trigger_rule, schema=TRIGGER_RULE_SCHEMA)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
        if not hass.data[DOMAIN]:
            for svc in (SERVICE_SEND_IMAGE, SERVICE_WAKE_DEVICE, SERVICE_TRIGGER_RULE):
                hass.services.async_remove(DOMAIN, svc)
    return unload_ok
