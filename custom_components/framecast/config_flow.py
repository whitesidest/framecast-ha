"""Config flow: prompt for FrameCast URL + API key, validate with a list_devices call.

Options flow: the poll interval. Automations that react to the art changing
wait on this poll, so a home that drives a dial or a light from the Frame
wants it short; the default stays a quiet 60 s.
"""
from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import FrameCastApiError, FrameCastAuthError, FrameCastClient
from .const import (
    CONF_API_KEY,
    CONF_SCAN_INTERVAL,
    CONF_URL,
    DEFAULT_SCAN_INTERVAL_S,
    DOMAIN,
    MAX_SCAN_INTERVAL_S,
    MIN_SCAN_INTERVAL_S,
)

USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_URL, default="http://framecast:8000"): str,
        vol.Required(CONF_API_KEY): str,
    }
)


def options_schema(current: int) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_SCAN_INTERVAL, default=current): vol.All(
                vol.Coerce(int), vol.Range(min=MIN_SCAN_INTERVAL_S, max=MAX_SCAN_INTERVAL_S)
            ),
        }
    )


class FrameCastConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}
        if user_input is not None:
            session = async_get_clientsession(self.hass)
            client = FrameCastClient(session, user_input[CONF_URL], user_input[CONF_API_KEY])
            try:
                await client.list_devices()
            except FrameCastAuthError:
                errors["base"] = "invalid_auth"
            except FrameCastApiError:
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(user_input[CONF_URL])
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title="FrameCast", data=user_input)

        return self.async_show_form(step_id="user", data_schema=USER_SCHEMA, errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> FrameCastOptionsFlow:
        return FrameCastOptionsFlow()


class FrameCastOptionsFlow(config_entries.OptionsFlow):
    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        current = int(self.config_entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_S))
        return self.async_show_form(step_id="init", data_schema=options_schema(current))
