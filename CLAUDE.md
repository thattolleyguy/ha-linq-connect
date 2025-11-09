# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Purpose

This repository is for managing custom-built plugins and utilities for Home Assistant. It serves as a development workspace for Home Assistant custom components and related tools.

## Environment Setup

- **Python Version**: Python 3.13
- **Virtual Environment**: `.venv/` (activate with `source .venv/bin/activate`)
- Install dependencies: `pip install -r requirements.txt` (when requirements.txt exists)

## Current Contents

### spotcast-auth.py

A Spotify OAuth PKCE authentication script that generates access and refresh tokens for the Spotcast Home Assistant integration.

**Usage**:
```bash
python spotcast-auth.py [-p PORT] [-i]
```

Options:
- `-p, --port`: Local port for OAuth redirect (default: 8080)
- `-i, --interactive`: Interactive mode with clipboard output

The script:
1. Starts a local HTTP server on the specified port
2. Opens a browser for Spotify authentication
3. Receives the OAuth callback with authorization code
4. Exchanges the code for access and refresh tokens
5. Outputs the tokens and tests connectivity by listing Spotify devices

**Note**: This script references `custom_components.spotcast.const.SPOTIFY_CLIENT_ID`, which should be available from the Spotcast integration.

## Home Assistant Custom Component Structure

When creating custom components, follow this standard structure:

```
custom_components/
└── component_name/
    ├── __init__.py           # Component initialization
    ├── manifest.json         # Component metadata and dependencies
    ├── const.py             # Constants
    ├── config_flow.py       # Configuration UI (optional)
    ├── sensor.py            # Sensor platform (if applicable)
    ├── switch.py            # Switch platform (if applicable)
    └── strings.json         # Localization strings
```

## Key Architecture Notes

### Home Assistant Integration Patterns

- **Custom Components**: Located in `custom_components/` directory
- **manifest.json**: Required for all integrations, defines dependencies, version, and requirements
- **Config Flow**: Preferred method for user configuration (vs YAML)
- **Platforms**: Separate files for sensor, switch, binary_sensor, etc.

### Development Best Practices

- Follow Home Assistant's integration quality scale requirements
- Use `homeassistant.helpers` utilities for common tasks
- Implement proper error handling and logging using `_LOGGER`
- Support both UI configuration (config_flow) and YAML when appropriate
- Use async/await patterns for I/O operations

## Testing Custom Components

To test components in a Home Assistant installation:

1. Copy the component to your Home Assistant `custom_components/` directory:
   ```bash
   cp -r custom_components/your_component /path/to/homeassistant/custom_components/
   ```

2. Restart Home Assistant:
   ```bash
   # Via CLI
   ha core restart

   # Or restart the container/service as appropriate
   ```

3. Check logs for errors:
   ```bash
   tail -f /path/to/homeassistant/home-assistant.log
   ```

## Running Python Scripts

Scripts in this repository should be run with the virtual environment activated:

```bash
source .venv/bin/activate
python script_name.py
```
