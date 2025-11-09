# Calendar Entity Implementation Plan

## Overview

Add a calendar entity to the School Lunch Menu integration to display all lunch menus for the month in Home Assistant's native calendar interface.

## Why Calendar Entity?

**Benefits:**
- View entire month of lunches at a glance
- Native calendar UI in Home Assistant
- Calendar cards show upcoming events beautifully
- Can filter/search for specific menu items across days
- Better for planning ahead ("what's lunch next Thursday?")
- Works with calendar-based automations

**Current State:**
- We already fetch 30 days before/after today from the API
- Data is available, just not exposed as calendar events
- Sensor shows only next upcoming lunch

## How Home Assistant Calendars Work

### No Storage Required
- Calendar entities don't persist data themselves
- They respond to requests for events in a date range
- Home Assistant calls `async_get_events(start_date, end_date)` when needed
- We return a list of `CalendarEvent` objects from our coordinator data

### Refresh Handling
- Our existing coordinator already refreshes hourly
- Calendar reads from the same coordinator data
- No additional API calls needed

### Calendar Event Structure
```python
CalendarEvent(
    start=datetime(2025, 11, 11),
    end=datetime(2025, 11, 11),
    summary="School Lunch - Pizza",
    description="Main Entree: Pizza\nSide: Fries\nVegetable: Carrots\n...",
    location="School Cafeteria" (optional)
)
```

## Implementation Steps

### 1. Update manifest.json
Add calendar platform support:
```json
{
  "domain": "school_lunch",
  "name": "School Lunch Menu",
  ...
}
```
No changes needed - platforms are auto-discovered.

### 2. Update __init__.py
Add Platform.CALENDAR to the platforms list:
```python
PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.CALENDAR]
```

### 3. Create calendar.py
New file: `custom_components/school_lunch/calendar.py`

Key components:
```python
from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from datetime import datetime, date

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the School Lunch Menu calendar."""
    child_name = config_entry.data[CONF_CHILD_NAME]
    building_id = config_entry.data[CONF_BUILDING_ID]
    district_id = config_entry.data[CONF_DISTRICT_ID]

    # Use the same coordinator as the sensor
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]

    async_add_entities([SchoolLunchCalendar(coordinator, child_name)])

class SchoolLunchCalendar(CoordinatorEntity, CalendarEntity):
    """School Lunch Menu Calendar."""

    def __init__(self, coordinator, child_name):
        super().__init__(coordinator)
        self._child_name = child_name
        self._attr_name = f"{child_name} School Lunch Calendar"

    @property
    def event(self) -> CalendarEvent | None:
        """Return the next upcoming event."""
        # Return today's or next lunch event
        events = self._get_events(date.today(), date.today() + timedelta(days=7))
        return events[0] if events else None

    async def async_get_events(
        self, hass, start_date: datetime, end_date: datetime
    ) -> list[CalendarEvent]:
        """Return calendar events within a datetime range."""
        return self._get_events(start_date.date(), end_date.date())

    def _get_events(self, start_date: date, end_date: date) -> list[CalendarEvent]:
        """Get events from coordinator data."""
        if not self.coordinator.data:
            return []

        events = []

        # Parse all lunch days from coordinator data
        # (Similar logic to sensor.py _parse_menu_json but return all days, not just next)
        family_menu_sessions = self.coordinator.data.get("FamilyMenuSessions", [])

        for session in family_menu_sessions:
            if session.get("ServingSession") != "Lunch":
                continue

            menu_plans = session.get("MenuPlans", [])

            for menu_plan in menu_plans:
                days = menu_plan.get("Days", [])

                for day in days:
                    day_date_str = day.get("Date", "")
                    if not day_date_str:
                        continue

                    # Parse date
                    try:
                        parsed_date = datetime.strptime(day_date_str, "%m/%d/%Y")
                    except ValueError:
                        continue

                    # Check if in requested range
                    if not (start_date <= parsed_date.date() <= end_date):
                        continue

                    # Extract menu items
                    menu_items = []
                    menu_by_category = {}

                    menu_meals = day.get("MenuMeals", [])
                    for meal in menu_meals:
                        recipe_categories = meal.get("RecipeCategories", [])
                        for category in recipe_categories:
                            category_name = category.get("CategoryName", "Unknown")
                            recipes = category.get("Recipes", [])

                            if category_name not in menu_by_category:
                                menu_by_category[category_name] = []

                            for recipe in recipes:
                                recipe_name = recipe.get("RecipeName", "")
                                if recipe_name:
                                    menu_by_category[category_name].append(recipe_name)
                                    menu_items.append(recipe_name)

                    if not menu_items:
                        continue

                    # Create event summary (first item or summary)
                    if len(menu_items) == 1:
                        summary = menu_items[0]
                    else:
                        summary = f"{menu_items[0]} (+{len(menu_items) - 1} more)"

                    # Create event description (organized by category)
                    description_lines = []
                    for category, items in menu_by_category.items():
                        description_lines.append(f"{category}:")
                        for item in items:
                            description_lines.append(f"  • {item}")
                    description = "\n".join(description_lines)

                    # Create calendar event (all-day event)
                    event = CalendarEvent(
                        start=parsed_date.date(),
                        end=parsed_date.date(),
                        summary=f"Lunch: {summary}",
                        description=description,
                    )
                    events.append(event)

        # Sort events by date
        events.sort(key=lambda e: e.start)
        return events
```

### 4. Update Coordinator Sharing

Modify `__init__.py` to share the coordinator between sensor and calendar:

```python
async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up School Lunch Menu from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Create coordinator once and share it
    building_id = entry.data[CONF_BUILDING_ID]
    district_id = entry.data[CONF_DISTRICT_ID]
    coordinator = SchoolLunchCoordinator(hass, building_id, district_id)

    await coordinator.async_config_entry_first_refresh()

    # Store coordinator for both platforms to use
    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "data": entry.data,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True
```

### 5. Update sensor.py

Modify sensor setup to use shared coordinator:
```python
async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the School Lunch Menu sensor."""
    # Get shared coordinator
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    data = hass.data[DOMAIN][config_entry.entry_id]["data"]

    child_name = data[CONF_CHILD_NAME]
    building_id = data[CONF_BUILDING_ID]
    district_id = data[CONF_DISTRICT_ID]

    async_add_entities([SchoolLunchSensor(coordinator, child_name, building_id, district_id)])
```

### 6. Update Coordinator to Store All Days

Modify `SchoolLunchCoordinator._parse_menu_json()` to return ALL lunch days, not just the next one:

```python
def _parse_menu_json(self, data: dict) -> dict:
    """Parse the LINQ Connect JSON menu data - store ALL lunches."""
    menu_data = {
        "all_lunches": [],  # NEW: Store all lunch days
        "next_lunch": {     # Keep next lunch for sensor
            "menu_items": [],
            "menu_by_category": {},
            "menu_plans": [],
            "date": None,
        }
    }

    # Collect ALL lunch days (not just next)
    # ... parse and store all days in all_lunches list
    # ... then find next one for next_lunch dict

    return menu_data
```

## Calendar Display Options

### Dashboard Calendar Card
```yaml
type: calendar
entities:
  - calendar.child_name_school_lunch_calendar
```

### Upcoming Events Card
```yaml
type: custom:atomic-calendar-revive
entities:
  - entity: calendar.child_name_school_lunch_calendar
    name: School Lunches
maxDaysToShow: 7
```

### List Card (Built-in)
```yaml
type: custom:list-card
entity: calendar.child_name_school_lunch_calendar
```

## Automations Examples

### Notify if Pizza Day Coming Up
```yaml
automation:
  - alias: "Pizza Day Alert"
    trigger:
      - platform: calendar
        entity_id: calendar.child_name_school_lunch_calendar
        event: start
        offset: "-1:0:0"  # 1 day before
    condition:
      - condition: template
        value_template: "{{ 'Pizza' in trigger.calendar_event.summary }}"
    action:
      - service: notify.mobile_app
        data:
          title: "Pizza Day Tomorrow!"
          message: "{{ trigger.calendar_event.description }}"
```

### Morning Lunch Reminder
```yaml
automation:
  - alias: "Morning Lunch Reminder"
    trigger:
      - platform: time
        at: "07:00:00"
    action:
      - service: notify.mobile_app
        data:
          title: "Today's Lunch"
          message: |
            {{ state_attr('calendar.child_school_lunch_calendar', 'message') }}
```

## Testing Steps

1. Add Platform.CALENDAR to __init__.py
2. Create calendar.py with the implementation above
3. Restart Home Assistant
4. Check Settings → Devices & Services → School Lunch Menu
5. Should see both a sensor and calendar entity
6. Add calendar card to dashboard
7. Verify events show up for the month

## Benefits Summary

✅ See entire month of lunches at once
✅ Native Home Assistant calendar interface
✅ No extra API calls (uses same coordinator data)
✅ Works with calendar automations
✅ Can search for specific items across days
✅ Beautiful calendar cards available
✅ Sensor still works independently

## Version Planning

- Current: v1.1.0 (Next Lunch Sensor)
- Proposed: v1.2.0 (Add Calendar Entity)

## Notes

- Calendar and sensor share the same coordinator
- Only one API call per hour (coordinator refresh)
- Calendar events are generated on-demand from coordinator data
- All-day events (no specific time)
- Can add multiple children = multiple calendar entities
- Each child gets their own calendar

## Future Enhancements

- Color-code events by menu category (if possible)
- Add location field (school name)
- Allow filtering by menu item type
- Week-ahead summary sensor attribute
