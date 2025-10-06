from datetime import datetime, timezone
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN, CONF_NAME

SENSOR_TYPES = {
    "day": {"name": "Daily Sales", "unit": "€"},
    "month": {"name": "Monthly Sales", "unit": "€"},
    "week": {"name": "Weekly Sales", "unit": "€"},
    "year": {"name": "Yearly Sales", "unit": "€"},
    "customers": {"name": "Customers Today", "unit": "customers"},
    "products": {"name": "Products Sold", "unit": "items"},
}


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up Count-It sensors from a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    friendly_name = entry.data.get(CONF_NAME, "Count-It")

    entities = [
        CountItSensor(
            coordinator=coordinator,
            entry_id=entry.entry_id,
            friendly_name=friendly_name,
            key=key,
            name=meta["name"],
            unit=meta["unit"],
        )
        for key, meta in SENSOR_TYPES.items()
    ]

    async_add_entities(entities)


class CountItSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Count-It sensor."""

    def __init__(self, coordinator, entry_id, friendly_name, key, name, unit):
        super().__init__(coordinator)
        self._key = key
        self._friendly_name = friendly_name
        self._attr_name = f"{friendly_name} {name}"
        self._attr_unique_id = f"{entry_id}_{key}"
        self._attr_native_unit_of_measurement = unit

    @property
    def native_value(self):
        value = self.coordinator.data.get(self._key)
        if self._key == "products":
            return len(value) if isinstance(value, list) else 0
        elif self._key == "customers":
            # Force integer for customers
            try:
                return int(float(value))
            except (TypeError, ValueError):
                return 0
        return float(value) if value is not None else 0.0


        # Default numeric or string values
        try:
            return round(float(value), 2)
        except (ValueError, TypeError):
            return value or 0

    @property
    def extra_state_attributes(self):
        """Provide extra sensor attributes."""
        last_updated = datetime.now(timezone.utc).isoformat(timespec="seconds")
        last_scrape = self.coordinator.data.get("last_successful_scrape")
        retry_count = self.coordinator.data.get("retry_count", 0)

        attrs = {
            "account": self._friendly_name,
            "last_updated": last_updated,
            "last_successful_scrape": last_scrape,
            "retry_count": retry_count,
        }

        # Add detailed product list if applicable
        if self._key == "products":
            items = self.coordinator.data.get("products", [])
            attrs["items"] = items
            attrs["items_pretty"] = "\n".join(items) if items else "No products sold"

        return attrs
