# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an ESPHome development workspace for building touchscreen control panels that connect to Home Assistant. It contains:

- **Standalone YAML configs** (root level and in the 'pages' subdirectory) -- device-specific configurations being actively developed
- **`esphome-modular-lvgl-buttons/`** -- a cloned library (git repo: `agillis/esphome-modular-lvgl-buttons`) providing modular, reusable LVGL UI components for ESP32 touchscreen devices. This is a **separate git repository** -- changes here should be intentional and considered for upstream contribution.
- **`tests/`** -- test and experimental configuration files
- **`secrets.yaml`** -- WiFi credentials and location data (gitignored, never commit)

## Common Commands

```bash
# Activate the virtualenv first
source ~/esphome-venv/bin/activate

# Validate a config without building (fast feedback loop)
esphome config <file>.yaml

# Build and flash a device (compile + upload)
esphome run <file>.yaml

# Compile only (no upload)
esphome compile <file>.yaml

# View device logs
esphome logs <file>.yaml

# Clean build artifacts for a device
esphome clean <file>.yaml
```

All commands run from `/home/esp32Dev/espHomeProjects/`. ESPHome is installed in a virtualenv at `/home/esp32Dev/esphome-venv/`. The installed version is 2026.5.3.

**Validation workflow:** Always run `esphome config <file>.yaml` before `esphome run` to catch YAML errors quickly. The `config` command outputs the fully merged/resolved configuration, making it useful for debugging package composition issues.

## Architecture: How Configs Compose

ESPHome YAML configs use a **package/include system** for modularity. A typical device config works like this:

1. **Root YAML file** (e.g., `waveshare-esp32-p4-wifi6-touch-lcd-7b.yaml`) -- defines the device name, substitution variables, and pulls in packages
2. **Hardware file** (`esphome-modular-lvgl-buttons/hardware/*.yaml`) -- defines chip variant, pin mappings, display driver, touchscreen, backlight, and audio hardware for a specific board
3. **Common packages** (`esphome-modular-lvgl-buttons/common/*.yaml`) -- shared configs for WiFi, OTA, colors, fonts, themes, time sync
4. **Button/widget packages** (`esphome-modular-lvgl-buttons/buttons/*.yaml`) -- reusable LVGL UI components included with `!include` + `vars:` for parameterization
5. **Page packages** (`esphome-modular-lvgl-buttons/pages/*.yaml`) -- full-screen layouts (boot screen, info screen, color picker)

The composition pattern in a root config:
```yaml
packages:
  wifi: !include esphome-modular-lvgl-buttons/common/wifi.yaml
  hardware: !include esphome-modular-lvgl-buttons/hardware/<board>.yaml
  button_1: !include
    file: esphome-modular-lvgl-buttons/buttons/switch_button.yaml
    vars:
      uid: button_1
      row: 0
      column: 0
      entity_id: "switch.my_device"
```

**Key merge behavior:** when ESPHome merges packages, **duplicate top-level keys are merged, not overwritten**. This is how multiple packages can each contribute `sensor:`, `binary_sensor:`, `lvgl:` entries that combine into one config.

### The `!extend` Pattern

Packages use `!extend` to add widgets to pages defined elsewhere. For example, each button package extends `main_page` to inject its widget into the grid:
```yaml
lvgl:
  pages:
    - id: !extend ${page_id | default("main_page")}
      widgets:
        - container: ...
```

The `| default()` filter provides fallback values for optional `vars:` parameters. Button packages typically require `uid`, `row`, `column`, `entity_id`, `text`, and `icon` but have optional params like `page_id`, `row_span`, and `column_span` with defaults.

### Script Contracts Between Packages

The `backlight_time.yaml` package calls `script.execute: time_update` every minute and on time sync. The **root config must define this script** to update any time-displaying widgets. See `waveshare-esp32-p4-wifi6-touch-lcd-7b.yaml` for the pattern.

Similarly, the root config must define `script: update_loading_page` if using the loading screen package (`pages/loading_480px.yaml`), triggered via `on_boot`.

## ESPHome YAML Conventions

- **`name:`** under `esphome:` is required and must be **31 characters or fewer** (hostname limit)
- **`friendly_name:`** can be longer and appears in Home Assistant UI
- **`substitutions:`** define variables referenced as `${var}` or `$var` throughout the config
- **`!secret`** references pull values from `secrets.yaml` (WiFi credentials, API keys)
- Hardware files define chip-specific settings (`esp32:`, `psram:`, `i2c:`, `spi:`, `display:`, `touchscreen:`)
- LVGL pages use a grid layout system (`layout: 4x7`) where buttons specify `row`/`column` positions
- The root config's `substitutions:` block sets theming variables (`button_on_color`, `icon_font`, `text_font`, etc.) that button packages reference via `$var`

## ESP32-P4 Specifics

The Waveshare ESP32-P4 boards (the primary hardware being developed for) have unique requirements:
- Use `esp-idf` framework (not Arduino)
- Require `esp32_hosted:` section for the ESP32-C6 WiFi co-processor (the P4 has no native WiFi)
- Need `psram:` configuration (hex mode, 200MHz)
- Need `esp_ldo:` for voltage regulation
- Use `mipi_dsi` display platform
- Require `enable_idf_experimental_features: true`

### Audio Pipeline (P4 7B board)

The hardware file sets up a multi-stage audio pipeline: `ES8311 DAC` + `ES7210 ADC` over I2C, with I2S bus for speaker/microphone data. The speaker chain is: `i2s_audio speaker` → `mixer` (announcement + media inputs) → `resampler` stages. A GPIO switch (`GPIO53`) controls the hardware amplifier. The `media_player-voice_assistant.yaml` package builds on these hardware primitives for voice assistant and media playback.

## Image Encoding for LVGL Displays

The LVGL display runs at **`color_depth: 16`** (RGB565) with **`byte_order: little_endian`**. This affects how images must be declared in ESPHome:

### Critical: byte_order must match LVGL

**ESPHome's image encoder defaults to big-endian**, but this LVGL display is configured for **little-endian**. If `byte_order` is not explicitly set on `image:` declarations, the pixel data will be byte-swapped, causing severe green/magenta color corruption.

**Always set `byte_order: little_endian`** on image declarations using `defaults:`:
```yaml
image:
  defaults:
    byte_order: little_endian
  rgb565:
    alpha_channel:
      - file: path/to/image.png
        id: my_image
        resize: 100x100
```

This applies to all `image:` blocks in any package file. SVG icons with flat colors may appear to work without it (the corruption is less visible on saturated colors), but photographic images will be severely corrupted.

### Image type guidelines

- **SVG icons and graphics:** Use `rgb565:` with `alpha_channel:` transparency.

- **Photographic or near-grayscale images (e.g., moon phases):** Use `rgb565:` with `alpha_channel:`, but **pre-convert the source to true grayscale** (R=G=B=luminance) in the RGBA PNG. This avoids the subtle green tint that RGB565's unequal 5-6-5 bit depth causes on warm-toned photos.
  - **Do NOT use `grayscale:` type** -- LVGL on this device does not render GRAYSCALE images (they appear invisible).
  - See `pages/images/Moon/generate_phases.py` for the conversion pattern.

- **Online/dynamic JPEG images (e.g., album art):** Use the `online_image:` component with `type: RGB565` and `byte_order: little_endian`.
  ```yaml
  online_image:
    - url: "http://server/image.jpg"
      id: my_image
      format: JPEG
      type: RGB565
      byte_order: little_endian
      resize: 200x200
      update_interval: never
  ```

## Desktop Testing with SDL

Configs can be tested without hardware using the SDL display platform on Linux/macOS. Use `hardware/SDL-lvgl.yaml` as the hardware package. Requires `libsdl2-dev` installed. Run with `esphome run <sdl-config>.yaml` to open a simulated display window. Use `sensors/sensors_base-SDL.yaml` instead of `sensors_base.yaml` for SDL builds (no WiFi/CPU sensors).
