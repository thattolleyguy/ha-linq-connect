# School Lunch Menu Integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
[![GitHub Release](https://img.shields.io/github/release/thattolleyguy/ha-linq-connect.svg)](https://github.com/thattolleyguy/ha-linq-connect/releases)

A Home Assistant custom component that displays school lunch menus for your children by fetching data from LINQ Connect API endpoints.

## Features

- 🍎 Displays today's lunch menu as a sensor
- 👨‍👩‍👧‍👦 Supports multiple children/schools
- 📅 Automatically manages rolling date windows (no manual date updates needed!)
- 🔄 Updates every hour
- 📊 Menu organized by category (Main Entree, Side, Vegetable, Fruit, Milk, etc.)
- ⚙️ Easy configuration through Home Assistant UI
- 🔌 Integrates with automations and dashboards

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Click on "Integrations"
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add this repository URL: `https://github.com/thattolleyguy/ha-linq-connect`
6. Select category: "Integration"
7. Click "Add"
8. Click "Install" on the School Lunch Menu card
9. Restart Home Assistant
10. Add the integration through Settings → Devices & Services

### Manual Installation

1. Download the latest release from the [releases page](https://github.com/thattolleyguy/ha-linq-connect/releases)
2. Extract the `school_lunch` folder from the zip
3. Copy the `school_lunch` folder to your `config/custom_components/` directory
4. Restart Home Assistant
5. Add the integration through Settings → Devices & Services

## Configuration

### Getting Your Building and District IDs

To use this integration, you need two IDs from LINQ Connect:

1. Visit your school district's lunch menu website
2. Open browser Developer Tools (F12)
3. Go to the Network tab
4. Navigate to view lunch menus
5. Look for API calls to `api.linqconnect.com/api/FamilyMenu`
6. Copy the `buildingId` and `districtId` from the URL

Example URL:
```
https://api.linqconnect.com/api/FamilyMenu?buildingId=0170d186-06bd-ed11-82b1-9fb642954f29&districtId=a83d5cd9-a7a8-ed11-8e69-da0395d724bd&...
```

From this, extract:
- **Building ID**: `0170d186-06bd-ed11-82b1-9fb642954f29`
- **District ID**: `a83d5cd9-a7a8-ed11-8e69-da0395d724bd`

### Adding the Integration

1. Go to **Settings → Devices & Services**
2. Click **"+ Add Integration"**
3. Search for **"School Lunch Menu"**
4. Enter:
   - **Child's Name**: e.g., "Emma"
   - **Building ID**: Your school's building ID
   - **District ID**: Your district ID
5. Repeat for additional children

## Sensor Data

Each sensor provides:

- **State**: Summary of today's menu (e.g., "Pizza (+5 more items)")
- **Attributes**:
  - `menu_items`: Complete list of all lunch items
  - `menu_by_category`: Items organized by category
  - `menu_plans`: Available menu plan names
  - `child_name`: The child's name
  - `menu_date`: Date of the menu
  - `last_updated`: Last update timestamp

## Dashboard Examples

### Simple Entity Card

```yaml
type: entity
entity: sensor.emma_school_lunch
```

### Detailed Menu Card

```yaml
type: entities
title: Today's Lunch Menu
entities:
  - entity: sensor.emma_school_lunch
    name: Emma's Lunch
  - type: attribute
    entity: sensor.emma_school_lunch
    attribute: menu_items
    name: Full Menu
```

### Menu by Category

```yaml
type: markdown
content: |
  ## {{ state_attr('sensor.emma_school_lunch', 'child_name') }}'s Lunch

  **Main Entree:**
  {% for item in state_attr('sensor.emma_school_lunch', 'menu_by_category')['Main Entree'] %}
  - {{ item }}
  {% endfor %}

  **Sides:**
  {% for item in state_attr('sensor.emma_school_lunch', 'menu_by_category')['Side'] %}
  - {{ item }}
  {% endfor %}
```

## Automation Examples

### Morning Notification

```yaml
automation:
  - alias: "Morning Lunch Menu Notification"
    trigger:
      - platform: time
        at: "07:00:00"
    action:
      - service: notify.mobile_app
        data:
          title: "Today's Lunch"
          message: >
            Emma: {{ state_attr('sensor.emma_school_lunch', 'menu_items') | join(', ') }}
```

### TTS Announcement

```yaml
automation:
  - alias: "Announce Lunch Menu"
    trigger:
      - platform: time
        at: "06:30:00"
    action:
      - service: tts.google_translate_say
        entity_id: media_player.kitchen_speaker
        data:
          message: >
            Good morning! Today's lunch is {{ states('sensor.emma_school_lunch') }}
```

## Troubleshooting

### "Cannot connect" error
- Verify building ID and district ID are correct GUIDs
- Ensure Home Assistant can reach api.linqconnect.com
- Check Home Assistant logs for detailed errors

### No menu items showing
- Menu might not be published for today yet
- Check the `menu_date` attribute to see what date was found
- Schools often only publish menus during the school year

### "Invalid data" error
- Verify IDs match a valid school in LINQ Connect system
- Check that the API is returning "Lunch" serving session data

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Credits

Created for parents who want to know what their kids are eating at school today! 🍎

## Support

If you find this integration helpful, please star the repository!

For issues and feature requests, please use the [GitHub Issues](https://github.com/thattolleyguy/ha-linq-connect/issues) page.
