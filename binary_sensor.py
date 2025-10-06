from datetime import datetime, timezone
from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN, CONF_NAME

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the Count-It scraper status binary sensor."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    friendly_name = entry.data.get(CONF_NAME, "Count-It")

    async_add_entities([CountItStatusSensor(coordinator, entry.entry_id, friendly_name)])


class CountItStatusSensor(CoordinatorEntity, BinarySensorEntity):
    """Binary sensor indicating whether the scraper succeeded recently."""

    def __init__(self, coordinator, entry_id, friendly_name):
        super().__init__(coordinator)
        self._friendly_name = friendly_name
        self._attr_name = f"{friendly_name} Scraper Status"
        self._attr_unique_id = f"{entry_id}_scraper_status"

    @property
    def is_on(self):
        """Return True if the scraper succeeded within the last 30 minutes."""
        last_scrape = self.coordinator.data.get("last_successful_scrape")
        if not last_scrape:
            return False
        try:
            dt = datetime.fromisoformat(last_scrape)
            delta = datetime.now(timezone.utc) - dt.replace(tzinfo=timezone.utc)
            return delta.total_seconds() < 1800  # 30 minutes
        except Exception:
            return False

    @property
    def extra_state_attributes(self):
        """Return diagnostic details."""
        data = self.coordinator.data
        return {
            "account": self._friendly_name,
            "last_successful_scrape": data.get("last_successful_scrape"),
            "retry_count": data.get("retry_count", 0),
            "day": data.get("day", 0),
            "month": data.get("month", 0),
            "week": data.get("week", 0),
            "year": data.get("year", 0),
            "customers": data.get("customers", 0),
            "product_count": len(data.get("products", [])) if isinstance(data.get("products"), list) else 0,
        }

    @property
    def device_class(self):
        return "connectivity"

    @property
    def icon(self):
        return "mdi:cloud-check-outline" if self.is_on else "mdi:cloud-alert-outline"
