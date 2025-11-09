# School Lunch Menu Integration

A Home Assistant custom component that displays school lunch menus for your children by fetching data from LINQ Connect API endpoints.

## Features

- Supports multiple children/schools
- Fetches menu data from LINQ Connect JSON API
- Updates every hour automatically
- Easy configuration through the Home Assistant UI
- Displays full menu items as sensor attributes
- Organizes menu by category (Main Entree, Side, Vegetable, Fruit, Milk, etc.)

## Installation

1. Copy the `school_lunch` folder to your Home Assistant `custom_components` directory:
   ```bash
   cp -r custom_components/school_lunch /config/custom_components/
   ```

2. Restart Home Assistant

3. Add the integration through the UI:
   - Go to Settings → Devices & Services
   - Click "+ Add Integration"
   - Search for "School Lunch Menu"
   - Enter your child's name, building ID, and district ID

## Configuration

The integration requires three pieces of information for each child:

- **Child's Name**: A friendly name to identify the sensor (e.g., "Emma", "John")
- **Building ID**: The GUID for your school building (e.g., `0170d186-06bd-ed11-82b1-9fb642954f29`)
- **District ID**: The GUID for your school district (e.g., `a83d5cd9-a7a8-ed11-8e69-da0395d724bd`)

### Getting Your Building and District IDs

To find your building and district IDs:

1. Visit your school district's lunch menu website (if they use LINQ Connect)
2. Open your browser's developer tools (F12)
3. Go to the Network tab
4. Navigate the menu site to view lunch menus
5. Look for API calls to `api.linqconnect.com/api/FamilyMenu`
6. In the request URL, you'll find the `buildingId` and `districtId` parameters

The integration automatically constructs the API URL with a rolling 30-day date window (30 days before and after today), so the menu data is always fresh and includes today's menu.

You can add multiple children by adding the integration multiple times with different names. If your children attend the same school, you can use the same building and district IDs.

## Sensor Data

Each sensor provides:

- **State**: The first menu item or a summary (e.g., "Pizza (+3 more)")
- **Attributes**:
  - `menu_items`: Full list of all menu items for today
  - `menu_by_category`: Menu items organized by category (Main Entree, Side, Vegetable, Fruit, Milk, Condiments)
  - `menu_plans`: Names of the menu plans available (e.g., "Week 3 - 1", "Pizza", "Salad Line")
  - `child_name`: The child's name
  - `menu_date`: The date of the menu
  - `last_updated`: Timestamp of last successful update

## LINQ Connect JSON Format

The integration automatically parses the LINQ Connect API JSON response, which has the following structure:

```json
{
  "FamilyMenuSessions": [
    {
      "ServingSession": "Lunch",
      "MenuPlans": [
        {
          "MenuPlanName": "2025/2026 Secondary Lunch",
          "Days": [
            {
              "Date": "9/30/2025",
              "MenuMeals": [
                {
                  "MenuMealName": "Week 3 - 1",
                  "RecipeCategories": [
                    {
                      "CategoryName": "Main Entree",
                      "Recipes": [
                        {"RecipeName": "Pizza"},
                        {"RecipeName": "Chicken Nuggets"}
                      ]
                    }
                  ]
                }
              ]
            }
          ]
        }
      ]
    }
  ]
}
```

The integration automatically:
- Filters for "Lunch" serving session
- Finds today's menu by date
- Extracts all recipes organized by category
- Removes duplicates while preserving order

## Automation Examples

### Send notification with today's lunch menu:

```yaml
automation:
  - alias: "Morning Lunch Menu"
    trigger:
      - platform: time
        at: "07:00:00"
    action:
      - service: notify.mobile_app
        data:
          title: "Today's Lunch Menu"
          message: >
            Emma's lunch: {{ state_attr('sensor.emma_school_lunch', 'menu_items') | join(', ') }}
```

### Display on dashboard:

```yaml
type: entities
entities:
  - entity: sensor.emma_school_lunch
  - type: attribute
    entity: sensor.emma_school_lunch
    attribute: menu_items
    name: Full Menu
```

## Troubleshooting

- **"Cannot connect" error**:
  - Verify your building ID and district ID are correct
  - Check that your Home Assistant instance can reach api.linqconnect.com
  - Ensure the IDs are valid GUIDs in the correct format
- **"Invalid data" error**:
  - Verify the building and district IDs match a valid school in the LINQ Connect system
  - Check Home Assistant logs for detailed error information
- **No menu items**:
  - The menu might not be published for today yet
  - Check that the API is returning data for the "Lunch" serving session
  - View Home Assistant logs for detailed parsing information
- **Sensor shows "No menu available"**:
  - The school may not have published menus yet
  - Check the menu_date attribute to see if any date was found
  - Some schools only publish menus during the school year

## Support

For issues and feature requests, please visit the GitHub repository.
