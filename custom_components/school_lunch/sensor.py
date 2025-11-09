"""Sensor platform for School Lunch Menu integration."""
from __future__ import annotations

from datetime import datetime, timedelta
import json
import logging

import aiohttp
import async_timeout

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import (
    API_BASE_URL,
    ATTR_CHILD_NAME,
    ATTR_LAST_UPDATED,
    ATTR_MENU_ITEMS,
    ATTR_SCHOOL_NAME,
    CONF_BUILDING_ID,
    CONF_CHILD_NAME,
    CONF_DISTRICT_ID,
    DEFAULT_DATE_RANGE_DAYS,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the School Lunch Menu sensor."""
    child_name = config_entry.data[CONF_CHILD_NAME]
    building_id = config_entry.data[CONF_BUILDING_ID]
    district_id = config_entry.data[CONF_DISTRICT_ID]

    coordinator = SchoolLunchCoordinator(hass, building_id, district_id)

    await coordinator.async_config_entry_first_refresh()

    async_add_entities([SchoolLunchSensor(coordinator, child_name, building_id, district_id)])


class SchoolLunchCoordinator(DataUpdateCoordinator):
    """Class to manage fetching School Lunch Menu data."""

    def __init__(self, hass: HomeAssistant, building_id: str, district_id: str) -> None:
        """Initialize."""
        self.building_id = building_id
        self.district_id = district_id

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )

    async def _async_update_data(self) -> dict:
        """Fetch data from API endpoint."""
        # Build the endpoint URL with a rolling date range
        today = datetime.now()
        start_date = (today - timedelta(days=DEFAULT_DATE_RANGE_DAYS)).strftime("%-m-%-d-%Y")
        end_date = (today + timedelta(days=DEFAULT_DATE_RANGE_DAYS)).strftime("%-m-%-d-%Y")

        endpoint_url = (
            f"{API_BASE_URL}?"
            f"buildingId={self.building_id}&"
            f"districtId={self.district_id}&"
            f"startDate={start_date}&"
            f"endDate={end_date}"
        )

        try:
            async with async_timeout.timeout(10):
                async with aiohttp.ClientSession() as session:
                    async with session.get(endpoint_url) as response:
                        if response.status != 200:
                            raise UpdateFailed(f"Error fetching data: HTTP {response.status}")

                        content = await response.text()

                        # Parse JSON
                        try:
                            json_data = json.loads(content)
                            menu_data = self._parse_menu_json(json_data)
                            return menu_data
                        except json.JSONDecodeError as err:
                            raise UpdateFailed(f"Error parsing JSON: {err}") from err

        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err

    def _parse_menu_json(self, data: dict) -> dict:
        """Parse the LINQ Connect JSON menu data."""
        menu_data = {
            "menu_items": [],
            "menu_by_category": {},
            "menu_plans": [],
            "date": None,
        }

        # Get today's date in the format used by the API (M/D/YYYY)
        today = datetime.now()
        today_str = today.strftime("%-m/%-d/%Y")  # Remove leading zeros

        # Also try with leading zeros in case format varies
        today_alt = today.strftime("%m/%d/%Y")

        try:
            # Navigate through the JSON structure
            family_menu_sessions = data.get("FamilyMenuSessions", [])

            for session in family_menu_sessions:
                # Look for Lunch session
                if session.get("ServingSession") != "Lunch":
                    continue

                menu_plans = session.get("MenuPlans", [])

                for menu_plan in menu_plans:
                    menu_plan_name = menu_plan.get("MenuPlanName", "")
                    days = menu_plan.get("Days", [])

                    for day in days:
                        day_date = day.get("Date", "")

                        # Check if this is today's menu (try both date formats)
                        if day_date not in [today_str, today_alt]:
                            continue

                        menu_data["date"] = day_date

                        # Process all menu meals for today
                        menu_meals = day.get("MenuMeals", [])

                        for meal in menu_meals:
                            meal_name = meal.get("MenuMealName", "")
                            if meal_name:
                                menu_data["menu_plans"].append(meal_name)

                            recipe_categories = meal.get("RecipeCategories", [])

                            for category in recipe_categories:
                                category_name = category.get("CategoryName", "Unknown")
                                recipes = category.get("Recipes", [])

                                # Initialize category list if not exists
                                if category_name not in menu_data["menu_by_category"]:
                                    menu_data["menu_by_category"][category_name] = []

                                for recipe in recipes:
                                    recipe_name = recipe.get("RecipeName", "")
                                    if recipe_name:
                                        menu_data["menu_by_category"][category_name].append(recipe_name)
                                        menu_data["menu_items"].append(recipe_name)

        except (KeyError, TypeError) as err:
            _LOGGER.error("Error parsing menu JSON structure: %s", err)

        # Remove duplicates while preserving order
        seen = set()
        unique_items = []
        for item in menu_data["menu_items"]:
            if item not in seen:
                seen.add(item)
                unique_items.append(item)
        menu_data["menu_items"] = unique_items

        return menu_data


class SchoolLunchSensor(CoordinatorEntity, SensorEntity):
    """Representation of a School Lunch Menu sensor."""

    def __init__(
        self,
        coordinator: SchoolLunchCoordinator,
        child_name: str,
        building_id: str,
        district_id: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._child_name = child_name
        self._building_id = building_id
        self._district_id = district_id
        self._attr_name = f"{child_name} School Lunch"
        self._attr_unique_id = f"school_lunch_{building_id}_{district_id}_{child_name}"

    @property
    def native_value(self) -> str:
        """Return the state of the sensor."""
        if not self.coordinator.data or not self.coordinator.data.get("menu_items"):
            return "No menu available"

        menu_items = self.coordinator.data["menu_items"]

        # Return the first item as the main state, or a summary
        if len(menu_items) == 1:
            return menu_items[0]
        elif len(menu_items) > 1:
            return f"{menu_items[0]} (+{len(menu_items) - 1} more)"

        return "No menu available"

    @property
    def extra_state_attributes(self) -> dict:
        """Return the state attributes."""
        if not self.coordinator.data:
            return {}

        attributes = {
            ATTR_CHILD_NAME: self._child_name,
            ATTR_MENU_ITEMS: self.coordinator.data.get("menu_items", []),
            ATTR_LAST_UPDATED: datetime.now().isoformat(),
        }

        # Add menu organized by category
        if menu_by_category := self.coordinator.data.get("menu_by_category"):
            attributes["menu_by_category"] = menu_by_category

        # Add menu plan names
        if menu_plans := self.coordinator.data.get("menu_plans"):
            attributes["menu_plans"] = menu_plans

        if date := self.coordinator.data.get("date"):
            attributes["menu_date"] = date

        return attributes

    @property
    def icon(self) -> str:
        """Return the icon to use in the frontend."""
        return "mdi:food-apple"
