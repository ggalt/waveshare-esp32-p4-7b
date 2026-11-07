# Waveshare ESP32-P4-WIFI6-7inc-Touch-LCD Voice Assistant.

This is a set of files to set up the [Waveshare ESP32-P4-WIFI6-7inch-Touch-LCD(B)](https://www.waveshare.com/esp32-p4-wifi6-touch-lcd-7b.htm) as a Voice Assistant in [Home Assistant](https://www.home-assistant.io/).  

This is a personal project, set up for the way I work and it may not work for you, but may give you ideas about how to create your own Voice Assistant.  The device is set up with 3 pages: a clock, a weather page and a page that displays and allows you to control an associated Lyrion Music Player (I've used a piCorePlayer).  The Waveshare device has a few limitations, such as sharing the same bus for the mic and speaker, which means it can't play music AND listen for your commands (which is why I used the associated player approach).

## Requirements and setup

- **ESPHome 2026.7.0 or newer** (tested with 2026.10.2). Earlier versions do not support the `image:` platform format used here.
- The UI is built on [esphome-modular-lvgl-buttons](https://github.com/agillis/esphome-modular-lvgl-buttons), included as a git submodule. Clone with submodules:

```
git clone --recurse-submodules https://github.com/ggalt/waveshare-esp32-p4-7b.git
cd waveshare-esp32-p4-7b
./setup.sh          # creates ~/esphome-venv and installs ESPHome
source ~/esphome-venv/bin/activate
esphome run waveshare-esp32-p4-wifi6-touch-lcd-7b.yaml
```

The few library files that needed device-specific changes (display rotation, touch mirroring, theme handling, boot screen) are kept as copies in `local/` rather than modified inside the submodule, so the submodule stays identical to upstream.

The device also exposes **Day Colors Start / Night Colors Start** (Sunrise, Sunset, or Scheduled Time) and **Day/Night Colors Time** as configuration entities in Home Assistant, to control when the display switches between its day and night color schemes.

## Configuration

The player requires a 'secrets.yaml' file in the main directory in the form of:

```
# WiFi info
wifi_ssid: "[wifi_ssid]"
wifi_password: "[wifi_password]"

# Lat and Long for weather and determining sunset and sunrise
latitude: XX.XXXX      
longitude: XX.XXXX

# Clock display size: "small", "medium", or "large"
clock_size: "large"

# LMS Player ID (MAC address)
player_id: "[XX:XX:XX:XX:XX:XX]"        # existing MAC address of associated piCorePlayer
player_entity: "[media_player.picoreplayer]"   # entity name for associated player from Home Assistant

# Lyrion Music Server URL (e.g., http://192.168.XXX.XXX:9000)
lms_server: "[http://192.168.XXX.XXX:9000]"
```

I have included the voice commands that I use in conjunction with this device.  You may not which to used them, but they should give you a starting point for setting up similar commands.

The voice commands and player need a few HA helpers.  There are 4 that are used:

| Name | Entity ID | Type | Size | 
| --- | --- | --- | --- |
| Album Search Trigger | input_text.album_search_trigger | input text | 255 |
| last_album_search_ids | input_text.last_album_search_ids | input text | 255 |
| last_music_search_artist | input_text.last_music_search_artist | input text | 255 |
| lms_server_ip | input_text.lms_server_ip | input text | 100 |

All should be exposed to the voice assistants.


The STL files will allow you to print a stand for the screen and place the accompanying speaker somewhere that it can provide feedback.  The faceplace uses two M3 threaded inserts, and the speaker holder uses four M2.5 threaded inserts.  I also used a 90° USB-C adapter to turn the USB-C power outlet of the board so that it is pointing backward.  [This USB-C adapter](https://www.amazon.com/dp/B0BDY2ZBRP) is the one I used, but others might work.

[Here is a link to a video of the device in action.](https://youtu.be/p0bto6TRb30)
