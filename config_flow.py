import voluptuous as vol
import json
from homeassistant import config_entries
from homeassistant.const import CONF_USERNAME, CONF_PASSWORD
from homeassistant.core import callback
from .const import DOMAIN
import logging

_LOGGER = logging.getLogger(__name__)


class CountItConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle Count-It configuration flow."""
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            try:
                # Validate departments JSON
                departments_raw = user_input.get("departments", "{}").strip()
                departments = json.loads(departments_raw)
                if not isinstance(departments, dict):
                    raise ValueError("Departments must be a JSON object")
                user_input["departments"] = departments

                # Create entry directly
                return self.async_create_entry(
                    title=user_input["name"],
                    data=user_input,
                )
            except json.JSONDecodeError as e:
                _LOGGER.warning("Invalid departments JSON: %s", e)
                errors["departments"] = "invalid_json"
            except Exception as e:
                _LOGGER.error("Error creating Count-It entry: %s", e)
                errors["base"] = "unknown"

        schema = vol.Schema({
            vol.Required("name", default="Count-It Account"): str,
            vol.Required(
                CONF_USERNAME,
                description="Email address used to log in to Count-It"
            ): str,
            vol.Required(
                CONF_PASSWORD,
                description="Password for the Count-It account"
            ): str,
            vol.Required(
                "departments",
                description="Enter departments as JSON (e.g. {'Antwerpen': 111, 'Hasselt': 135})"
            ): str,
            vol.Optional(
                "interval",
                default=15,
                description="Polling interval in minutes (default: 15)"
            ): int,
            vol.Optional(
                "timeout",
                default=60,
                description="Connection timeout in seconds (default: 60)"
            ): int,
        })

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return CountItOptionsFlow(config_entry)


class CountItOptionsFlow(config_entries.OptionsFlow):
    """Handle Count-It options."""

    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        errors = {}
        existing = self.config_entry.options or self.config_entry.data

        if user_input is not None:
            try:
                departments = json.loads(user_input.get("departments", "{}"))
                if not isinstance(departments, dict):
                    raise ValueError("Departments must be a JSON object")
                user_input["departments"] = departments
                return self.async_create_entry(title="", data=user_input)
            except json.JSONDecodeError:
                errors["departments"] = "invalid_json"
            except Exception as e:
                _LOGGER.error("Error updating Count-It options: %s", e)
                errors["base"] = "unknown"

        departments_str = json.dumps(existing.get("departments", {}), indent=2, ensure_ascii=False)

        options_schema = vol.Schema({
            vol.Optional(
                "interval",
                default=existing.get("interval", 15),
                description="Polling interval in minutes"
            ): int,
            vol.Optional(
                "timeout",
                default=existing.get("timeout", 60),
                description="Connection timeout in seconds"
            ): int,
            vol.Optional(
                "departments",
                default=departments_str,
                description="Enter departments as JSON (e.g. {'Antwerpen': 111, 'Hasselt': 135})"
            ): str,
        })

        return self.async_show_form(
            step_id="init",
            data_schema=options_schema,
            errors=errors,
        )
