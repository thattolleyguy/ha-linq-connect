"""Constants for the School Lunch Menu integration."""

DOMAIN = "school_lunch"

# Configuration
CONF_CHILD_NAME = "child_name"
CONF_BUILDING_ID = "building_id"
CONF_DISTRICT_ID = "district_id"

# API
API_BASE_URL = "https://api.linqconnect.com/api/FamilyMenu"

# Defaults
DEFAULT_SCAN_INTERVAL = 3600  # 1 hour in seconds
DEFAULT_NAME = "School Lunch"
DEFAULT_DATE_RANGE_DAYS = 30  # Days before and after today to fetch

# Attributes
ATTR_MENU_ITEMS = "menu_items"
ATTR_LAST_UPDATED = "last_updated"
ATTR_CHILD_NAME = "child_name"
ATTR_SCHOOL_NAME = "school_name"
