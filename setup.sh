#!/bin/bash
# Create the ESPHome virtualenv and fetch the UI library submodule.
set -e
cd "$(dirname "$0")"
git submodule update --init
python3 -m venv ~/esphome-venv
source ~/esphome-venv/bin/activate
pip install --upgrade pip
pip install "esphome==2026.10.2"
