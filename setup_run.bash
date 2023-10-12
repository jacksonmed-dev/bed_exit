#!/usr/bin/env bash
# List of packages to install
required_packages=("python3-dbus" "libglib2.0-dev" "libgirepository1.0-dev" "libcairo2-dev" "python3-venv")

# Check and install missing packages
for package in "${required_packages[@]}"; do
    if ! dpkg -l | grep -q "^ii  $package"; then
        echo "Installing $package..."
        sudo apt install -y "$package"
    else
        echo "$package is already installed."
    fi
done

# Check if the venv directory exists
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate the virtual environment
source venv/bin/activate

pip3 install -r requirements.txt

# Make the Raspberry Pi discoverable
sudo hciconfig hci0 piscan

# Run the Python program
python3 ./src/main.py --log-level INFO
