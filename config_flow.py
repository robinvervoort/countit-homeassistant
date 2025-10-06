import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector
from .const import DOMAIN, CONF_USERNAME, CONF_PASSWORD, CONF_NAME, CONF_TIMEOUT, DEFAULT_TIMEOUT, DEFAULT_NAME


class CountItConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a Count-It config flow."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial setup step."""
        errors = {}

        if user_input is not None:
            username = user_input[CONF_USERNAME]
            password = user_input[CONF_PASSWORD]
            name = user_input.get(CONF_NAME, username)
            timeout = user_input.get(CONF_TIMEOUT, DEFAULT_TIMEOUT)

            # Try simple validation
            if not username or not password:
                errors["base"] = "missing_credentials"
            else:
                # If no errors, create the entry
                return self.async_create_entry(
                    title=f"{name}",
                    data={
                        CONF_USERNAME: username,
                        CONF_PASSWORD: password,
                        CONF_NAME: name,
                        CONF_TIMEOUT: timeout,
                    },
                )

        schema = vol.Schema({
            vol.Required(CONF_NAME, default=DEFAULT_NAME): str,
            vol.Required(CONF_USERNAME): str,
            vol.Required(CONF_PASSWORD): str,
            vol.Optional(CONF_TIMEOUT, default=DEFAULT_TIMEOUT): int,
        })

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
            description_placeholders={
                "description": "Connect your Count-It account",
            },
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return CountItOptionsFlow(config_entry)


class CountItOptionsFlow(config_entries.OptionsFlow):
    """Handle Count-It options (edit existing config)."""

    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        errors = {}
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        options_schema = vol.Schema({
            vol.Optional(CONF_NAME, default=self.config_entry.data.get(CONF_NAME, DEFAULT_NAME)): str,
            vol.Optional(CONF_TIMEOUT, default=self.config_entry.data.get(CONF_TIMEOUT, DEFAULT_TIMEOUT)): int,
        })

        return self.async_show_form(
            step_id="init",
            data_schema=options_schema,
            errors=errors,
        )
