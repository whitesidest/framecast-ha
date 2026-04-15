"""Config flow: prompt for FrameCast URL + API key, validate with a list_devices call."""
from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import FrameCastApiError, FrameCastAuthError, FrameCastClient
from .const import CONF_API_KEY, CONF_URL, DOMAIN

USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_URL, default="http://framecast:8000"): str,
        vol.Required(CONF_API_KEY): str,
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
