import subprocess


def connect_to_wifi_network(network_ssid, network_password, wireless_interface):
    # Generate the configuration file
    config_text = f"""
    ctrl_interface=/run/wpa_supplicant
    ctrl_interface_group=0
    update_config=1
    network={{
        ssid="{network_ssid}"
        psk="{network_password}"
    }}
    """

    # Write the configuration file to disk
    with open("/etc/wpa_supplicant/wpa_supplicant-wlan1.conf", "w") as f:
        f.write(config_text)

    # Start the wpa_supplicant process
    process = subprocess.Popen(
        ["sudo", "wpa_supplicant", "-i", wireless_interface, "-c", "/etc/wpa_supplicant/wpa_supplicant-wlan1.conf"])

    # Wait for the process to complete
    process.wait()

    # If the process returns a non-zero exit code, there was an error
    if process.returncode != 0:
        print("Failed to connect to WiFi network")
    else:
        print("Successfully connected to WiFi network")
