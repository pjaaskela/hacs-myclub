"""MyClub sensors."""
from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, CONF_NAME, DEFAULT_NAME


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    name = entry.data.get(CONF_NAME, DEFAULT_NAME)
    slug = name.lower().replace(" ", "_")

    async_add_entities([
        MyclubNextEventSensor(coordinator, entry, name, slug),
        MyclubEventsSensor(coordinator, entry, name, slug),
    ])


class MyclubNextEventSensor(CoordinatorEntity, SensorEntity):
    """Next upcoming MyClub event."""

    def __init__(self, coordinator, entry, name, slug):
        super().__init__(coordinator)
        self._entry = entry
        self._name = name
        self._attr_name = f"{name} seuraava tapahtuma"
        self._attr_unique_id = f"myclub_{entry.entry_id}_next"
        self._attr_icon = "mdi:calendar-clock"

    @property
    def native_value(self):
        events = self.coordinator.data
        if not events:
            return "Ei tulevia tapahtumia"
        return events[0]["title"]

    @property
    def extra_state_attributes(self):
        events = self.coordinator.data
        if not events:
            return {"count": 0}
        e = events[0]
        return {
            "date": e["date"],
            "time": e["time"],
            "start_iso": e["start_iso"],
            "end_iso": e["end_iso"],
            "location": e["location"],
            "description": e["description"],
            "all_day": e["all_day"],
            "count": len(events),
        }


class MyclubEventsSensor(CoordinatorEntity, SensorEntity):
    """Count of upcoming MyClub events with full list as attributes."""

    def __init__(self, coordinator, entry, name, slug):
        super().__init__(coordinator)
        self._entry = entry
        self._name = name
        self._attr_name = f"{name} tulevat tapahtumat"
        self._attr_unique_id = f"myclub_{entry.entry_id}_events"
        self._attr_icon = "mdi:calendar-multiple"
        self._attr_native_unit_of_measurement = "kpl"

    @property
    def native_value(self):
        return len(self.coordinator.data or [])

    @property
    def extra_state_attributes(self):
        events = self.coordinator.data or []
        return {
            "events": [
                {
                    "title": e["title"],
                    "date": e["date"],
                    "time": e["time"],
                    "location": e["location"],
                    "start_iso": e["start_iso"],
                }
                for e in events
            ]
        }
