#!/usr/bin/env bash

source ./venv/bin/activate

sudo apt install python3-dbus

pip3 install -r requirements.txt

# Make the Raspberry Pi discoverable
sudo hciconfig hci0 piscan

# Run the Python program
python3 ./src/main.py --log-level DEBUG
