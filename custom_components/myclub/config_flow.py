"""Config flow for MyClub integration."""
from __future__ import annotations

import re
import asyncio
import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback

from .const import (
    DOMAIN, CONF_ICAL_URL, CONF_NAME, CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL, DEFAULT_NAME,
)


def _looks_like_ical_url(url: str) -> bool:
    return bool(re.match(r"https?://", url))


class MyclubConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            url = user_input[CONF_ICAL_URL].strip()
            if not _looks_like_ical_url(url):
                errors[CONF_ICAL_URL] = "invalid_url"
            else:
                # Quick connectivity check
                try:
                    timeout = aiohttp.ClientTimeout(total=10)
                    async with aiohttp.ClientSession(timeout=timeout) as session:
                        async with session.get(url) as resp:
                            if resp.status != 200:
                                errors[CONF_ICAL_URL] = "cannot_connect"
                            else:
                                text = await resp.text(errors="replace")
                                if "BEGIN:VCALENDAR" not in text:
                                    errors[CONF_ICAL_URL] = "not_ical"
                except asyncio.TimeoutError:
                    errors[CONF_ICAL_URL] = "cannot_connect"
                except aiohttp.ClientError:
                    errors[CONF_ICAL_URL] = "cannot_connect"

            if not errors:
                await self.async_set_unique_id(url)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=user_input.get(CONF_NAME, DEFAULT_NAME),
                    data=user_input,
                )

        schema = vol.Schema({
            vol.Required(CONF_NAME, default=DEFAULT_NAME): str,
            vol.Required(CONF_ICAL_URL): str,
            vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.All(
                int, vol.Range(min=5, max=1440)
            ),
        })

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return MyclubOptionsFlow(config_entry)


class MyclubOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self._config_entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current = self._config_entry.data
        schema = vol.Schema({
            vol.Optional(
                CONF_SCAN_INTERVAL,
                default=current.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
            ): vol.All(int, vol.Range(min=5, max=1440)),
        })
        return self.async_show_form(step_id="init", data_schema=schema)
