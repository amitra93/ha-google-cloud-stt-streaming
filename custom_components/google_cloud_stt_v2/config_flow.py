"""Config flow for Google Cloud Speech-to-Text V2 integration."""

from __future__ import annotations

import json
import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    BooleanSelector,
    FileSelector,
    FileSelectorConfig,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
    TextSelectorConfig,
)

from .const import (
    CONF_MODEL,
    CONF_PHRASE_HINTS,
    CONF_PUNCTUATION,
    CONF_RECOGNIZER,
    CONF_REGION,
    CONF_SERVICE_ACCOUNT_INFO,
    CONF_SPEECH_END_TIMEOUT,
    CONF_SPEECH_START_TIMEOUT,
    DEFAULT_PUNCTUATION,
    DEFAULT_RECOGNIZER,
    DEFAULT_SPEECH_END_TIMEOUT,
    DEFAULT_SPEECH_START_TIMEOUT,
    DOMAIN,
    SUPPORTED_MODELS,
    SUPPORTED_REGIONS,
    TITLE,
)

_LOGGER = logging.getLogger(__name__)

UPLOADED_KEY_FILE = "uploaded_key_file"
RAW_KEY_JSON = "raw_key_json"


class GoogleCloudSTTV2ConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Google Cloud Speech-to-Text V2."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize flow."""
        self._service_account_info: dict[str, Any] | None = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Step 1: Upload or paste Service Account Key JSON."""
        errors: dict[str, str] = {}

        if user_input is not None:
            raw_json = user_input.get(RAW_KEY_JSON)
            file_id = user_input.get(UPLOADED_KEY_FILE)

            json_data = None
            if file_id:
                try:
                    from homeassistant.components.file_upload import process_uploaded_file
                    with process_uploaded_file(self.hass, file_id) as file_path:
                        content = file_path.read_text()
                        json_data = json.loads(content)
                except Exception as err:
                    _LOGGER.error("Failed to read uploaded key file: %s", err)
                    errors["base"] = "invalid_json_file"
            elif raw_json:
                try:
                    json_data = json.loads(raw_json)
                except Exception as err:
                    _LOGGER.error("Failed to parse JSON string: %s", err)
                    errors["base"] = "invalid_json_format"

            if json_data and "project_id" in json_data and "private_key" in json_data:
                self._service_account_info = json_data
                await self.async_set_unique_id(json_data["project_id"])
                self._abort_if_unique_id_configured()
                return await self.async_step_config()
            elif json_data:
                errors["base"] = "invalid_service_account_json"

        schema = vol.Schema(
            {
                vol.Optional(UPLOADED_KEY_FILE): FileSelector(FileSelectorConfig(accept=".json")),
                vol.Optional(RAW_KEY_JSON): TextSelector(TextSelectorConfig(multiline=True)),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
            description_placeholders={"title": TITLE},
        )

    async def async_step_config(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Step 2: Force selection of Region and Model, plus parameters."""
        errors: dict[str, str] = {}

        if user_input is not None:
            data = {
                CONF_SERVICE_ACCOUNT_INFO: self._service_account_info,
                CONF_REGION: user_input[CONF_REGION],
                CONF_MODEL: user_input[CONF_MODEL],
            }
            options = {
                CONF_RECOGNIZER: user_input.get(CONF_RECOGNIZER, DEFAULT_RECOGNIZER),
                CONF_PUNCTUATION: user_input.get(CONF_PUNCTUATION, DEFAULT_PUNCTUATION),
                CONF_PHRASE_HINTS: user_input.get(CONF_PHRASE_HINTS, ""),
                CONF_SPEECH_START_TIMEOUT: user_input.get(CONF_SPEECH_START_TIMEOUT, DEFAULT_SPEECH_START_TIMEOUT),
                CONF_SPEECH_END_TIMEOUT: user_input.get(CONF_SPEECH_END_TIMEOUT, DEFAULT_SPEECH_END_TIMEOUT),
            }
            project_id = self._service_account_info.get("project_id", "GCP STT V2")
            return self.async_create_entry(
                title=f"GCP STT V2 ({project_id} / {user_input[CONF_REGION]})",
                data=data,
                options=options,
            )

        schema = vol.Schema(
            {
                vol.Required(CONF_REGION): SelectSelector(
                    SelectSelectorConfig(
                        options=SUPPORTED_REGIONS,
                        mode=SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Required(CONF_MODEL): SelectSelector(
                    SelectSelectorConfig(
                        options=SUPPORTED_MODELS,
                        mode=SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Optional(CONF_RECOGNIZER, default=DEFAULT_RECOGNIZER): TextSelector(
                    TextSelectorConfig()
                ),
                vol.Optional(CONF_PHRASE_HINTS, default=""): TextSelector(
                    TextSelectorConfig(multiline=True)
                ),
                vol.Optional(CONF_PUNCTUATION, default=DEFAULT_PUNCTUATION): BooleanSelector(),
                vol.Optional(CONF_SPEECH_START_TIMEOUT, default=DEFAULT_SPEECH_START_TIMEOUT): NumberSelector(
                    NumberSelectorConfig(min=1.0, max=30.0, step=0.5, mode=NumberSelectorMode.BOX)
                ),
                vol.Optional(CONF_SPEECH_END_TIMEOUT, default=DEFAULT_SPEECH_END_TIMEOUT): NumberSelector(
                    NumberSelectorConfig(min=0.2, max=10.0, step=0.1, mode=NumberSelectorMode.BOX)
                ),
            }
        )

        return self.async_show_form(
            step_id="config",
            data_schema=schema,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Get the options flow for this handler."""
        return GoogleCloudSTTV2OptionsFlowHandler()


class GoogleCloudSTTV2OptionsFlowHandler(OptionsFlow):
    """Handle options for Google Cloud STT V2."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        options = self.config_entry.options

        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_RECOGNIZER,
                    default=options.get(CONF_RECOGNIZER, DEFAULT_RECOGNIZER),
                ): TextSelector(TextSelectorConfig()),
                vol.Optional(
                    CONF_PHRASE_HINTS,
                    default=options.get(CONF_PHRASE_HINTS, ""),
                ): TextSelector(TextSelectorConfig(multiline=True)),
                vol.Optional(
                    CONF_PUNCTUATION,
                    default=options.get(CONF_PUNCTUATION, DEFAULT_PUNCTUATION),
                ): BooleanSelector(),
                vol.Optional(
                    CONF_SPEECH_START_TIMEOUT,
                    default=options.get(CONF_SPEECH_START_TIMEOUT, DEFAULT_SPEECH_START_TIMEOUT),
                ): NumberSelector(NumberSelectorConfig(min=1.0, max=30.0, step=0.5, mode=NumberSelectorMode.BOX)),
                vol.Optional(
                    CONF_SPEECH_END_TIMEOUT,
                    default=options.get(CONF_SPEECH_END_TIMEOUT, DEFAULT_SPEECH_END_TIMEOUT),
                ): NumberSelector(NumberSelectorConfig(min=0.2, max=10.0, step=0.1, mode=NumberSelectorMode.BOX)),
            }
        )

        return self.async_show_form(step_id="init", data_schema=schema)
