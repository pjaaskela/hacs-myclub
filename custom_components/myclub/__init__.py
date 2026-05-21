"""MyClub integration for Home Assistant."""
from __future__ import annotations

import asyncio
import logging
import re
from datetime import datetime, timezone, timedelta

import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, CONF_ICAL_URL, CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL, MAX_EVENTS

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor"]

FI_DAYS = ["ma", "ti", "ke", "to", "pe", "la", "su"]


def _parse_dt(s: str) -> datetime:
    s = s.strip()
    tz = timezone(timedelta(hours=3))
    if "T" in s:
        return datetime.strptime(s[:15], "%Y%m%dT%H%M%S").replace(tzinfo=tz)
    return datetime.strptime(s[:8], "%Y%m%d").replace(tzinfo=tz)


def _parse_ical(text: str) -> list[dict]:
    now = datetime.now(tz=timezone(timedelta(hours=3)))
    events = []
    for block in re.findall(r"BEGIN:VEVENT(.*?)END:VEVENT", text, re.DOTALL):
        summary = re.search(r"\nSUMMARY:(.+)", block)
        location = re.search(r"\nLOCATION:(.+)", block)
        description = re.search(r"\nDESCRIPTION:(.+)", block)
        dt_start = re.search(r"\nDTSTART[^:]*:(\S+)", block)
        dt_end = re.search(r"\nDTEND[^:]*:(\S+)", block)
        if not summary or not dt_start:
            continue
        try:
            start = _parse_dt(dt_start.group(1))
            end = _parse_dt(dt_end.group(1)) if dt_end else start
        except ValueError:
            continue

        if start < now - timedelta(hours=2):
            continue

        all_day = "T" not in dt_start.group(1)
        day_str = FI_DAYS[start.weekday()]
        date_str = f"{day_str} {start.day}.{start.month}."
        time_str = f"{start.strftime('%H:%M')}–{end.strftime('%H:%M')}" if not all_day else ""

        events.append({
            "title": summary.group(1).strip(),
            "date": date_str,
            "time": time_str,
            "start_iso": start.isoformat(),
            "end_iso": end.isoformat() if end else start.isoformat(),
            "location": location.group(1).strip() if location else "",
            "description": description.group(1).strip() if description else "",
            "all_day": all_day,
            "_ts": start.timestamp(),
        })

    events.sort(key=lambda e: e["_ts"])
    for e in events:
        del e["_ts"]
    return events[:MAX_EVENTS]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    ical_url = entry.data[CONF_ICAL_URL]
    scan_minutes = entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

    async def _fetch() -> list[dict]:
        try:
            timeout = aiohttp.ClientTimeout(total=15)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(ical_url) as resp:
                    if resp.status != 200:
                        raise UpdateFailed(f"HTTP {resp.status}")
                    text = await resp.text(errors="replace")
            return _parse_ical(text)
        except asyncio.TimeoutError as e:
            raise UpdateFailed("Timeout fetching iCal") from e
        except aiohttp.ClientError as e:
            raise UpdateFailed(f"Network error: {e}") from e

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=f"myclub_{entry.entry_id}",
        update_method=_fetch,
        update_interval=timedelta(minutes=scan_minutes),
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
