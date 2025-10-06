from datetime import datetime, timezone
from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN, CONF_NAME


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the Count-It binary sensor."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    friendly_name = entry.data.get(CONF_NAME, "Count-It")

    async_add_entities([
        CountItStatusSensor(coordinator, entry.entry_id, friendly_name)
    ])


class CountItStatusSensor(CoordinatorEntity, BinarySensorEntity):
    """Binary sensor indicating scraper success or failure."""

    _attr_device_class = "connectivity"

    def __init__(self, coordinator, entry_id, friendly_name):
        super().__init__(coordinator)
        self._entry_id = entry_id
        self._friendly_name = friendly_name
        self._attr_name = f"{friendly_name} Scraper Status"
        self._attr_unique_id = f"{entry_id}_scraper_status"

    @property
    def is_on(self):
        """Return True if the last scrape succeeded."""
        # Count-It always sets last_successful_scrape when successful
        last_scrape = self.coordinator.data.get("last_successful_scrape")
        return bool(last_scrape)

    @property
    def icon(self):
        """Return a contextual icon."""
        return "mdi:check-circle-outline" if self.is_on else "mdi:alert-circle-outline"

    @property
    def extra_state_attributes(self):
        """Return detailed status info."""
        last_scrape = self.coordinator.data.get("last_successful_scrape")
        retry_count = self.coordinator.data.get("retry_count", 0)

        attrs = {
            "account": self._friendly_name,
            "retry_count": retry_count,
            "last_updated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "last_successful_scrape": last_scrape or "Never",
        }

        # Add result summaries for clarity
        if self.is_on:
            attrs["status"] = "Online"
            attrs["last_result"] = "Data fetched successfully"
        else:
            attrs["status"] = "Offline"
            attrs["last_result"] = "Scraper failed or never ran"

        return attrs
