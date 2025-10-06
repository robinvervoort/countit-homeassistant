import logging
from datetime import timedelta, datetime
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Count-It integration from a config entry."""
    username = entry.data.get("username")
    password = entry.data.get("password")
    name = entry.data.get("name", "Count-It")

    _LOGGER.info("Setting up Count-It integration for user: %s", username)

    from . import scraper  # delay import to avoid blocking HA startup

    async def async_update_data():
        """Fetch new data from Count-It (runs in executor)."""
        _LOGGER.info("Count-It: starting data fetch")

        try:
            def blocking_fetch():
                # Run blocking I/O synchronously in an executor
                sales_data = scraper.fetch_sales(username=username, password=password)
                departments = entry.data.get("departments", {})
                products = scraper.fetch_products(
                    username=username,
                    password=password,
                    departments=departments
                )

                if not departments:
                    print("No departments configured")
                    return []

                print(f"Departments received: {departments}")

                data = sales_data
                data["products"] = products
                data["last_successful_scrape"] = datetime.now().isoformat()
                return data

            data = await hass.async_add_executor_job(blocking_fetch)
            _LOGGER.info("Count-It data fetched successfully: %s", data)
            return data

        except Exception as err:
            _LOGGER.exception("Count-It update failed: %s", err)
            raise UpdateFailed(f"Count-It update failed: {err}") from err

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=f"countit_data_{username}",
        update_method=async_update_data,
        update_interval=timedelta(minutes=15),
    )

    _LOGGER.info("Performing first refresh for Count-It user: %s", username)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, ["sensor", "binary_sensor"])

    _LOGGER.info("Count-It setup complete for %s", username)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a Count-It entry."""
    _LOGGER.info("Unloading Count-It integration for %s", entry.data.get('username'))
    unload_ok = await hass.config_entries.async_unload_platforms(entry, ["sensor", "binary_sensor"])
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok