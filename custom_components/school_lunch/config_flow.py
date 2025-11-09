"""Config flow for School Lunch Menu integration."""
from __future__ import annotations

from datetime import datetime, timedelta
import json
import logging
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
import homeassistant.helpers.config_validation as cv

from .const import (
    API_BASE_URL,
    CONF_BUILDING_ID,
    CONF_CHILD_NAME,
    CONF_DISTRICT_ID,
    DEFAULT_DATE_RANGE_DAYS,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_CHILD_NAME): cv.string,
        vol.Required(CONF_BUILDING_ID): cv.string,
        vol.Required(CONF_DISTRICT_ID): cv.string,
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    building_id = data[CONF_BUILDING_ID]
    district_id = data[CONF_DISTRICT_ID]

    # Build the endpoint URL with a date range
    today = datetime.now()
    start_date = (today - timedelta(days=DEFAULT_DATE_RANGE_DAYS)).strftime("%-m-%-d-%Y")
    end_date = (today + timedelta(days=DEFAULT_DATE_RANGE_DAYS)).strftime("%-m-%-d-%Y")

    endpoint_url = (
        f"{API_BASE_URL}?"
        f"buildingId={building_id}&"
        f"districtId={district_id}&"
        f"startDate={start_date}&"
        f"endDate={end_date}"
    )

    # Test the endpoint
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(endpoint_url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status != 200:
                    raise CannotConnect(f"HTTP {response.status}")

                content = await response.text()

                # Try to parse as JSON to validate format
                try:
                    json_data = json.loads(content)
                    # Validate it has the expected structure
                    if not isinstance(json_data, dict) or "FamilyMenuSessions" not in json_data:
                        raise InvalidData("Response does not contain expected FamilyMenuSessions data")
                except json.JSONDecodeError as err:
                    raise InvalidData(f"Invalid JSON: {err}") from err

    except aiohttp.ClientError as err:
        raise CannotConnect(f"Connection error: {err}") from err

    return {"title": f"Lunch Menu - {data[CONF_CHILD_NAME]}"}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for School Lunch Menu."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidData:
                errors["base"] = "invalid_data"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                # Create a unique ID based on building and district IDs
                await self.async_set_unique_id(
                    f"{user_input[CONF_BUILDING_ID]}_{user_input[CONF_DISTRICT_ID]}"
                )
                self._abort_if_unique_id_configured()

                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidData(HomeAssistantError):
    """Error to indicate the data format is invalid."""
