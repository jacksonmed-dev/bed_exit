import subprocess

# def connect_to_wifi_network(network_ssid, network_password, wireless_interface):
#     # Generate the configuration file
#     config_text = f"""
#     ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
#     update_config=1
#     country=US
#     network={{
#         ssid="{network_ssid}"
#         psk="{network_password}"
#     }}
#     """
#
#
#
#     # Write the configuration file to disk
#     with open("/etc/wpa_supplicant/wpa_supplicant-wlan1.conf", "w") as f:
#         f.write(config_text)
#
#     # Start the wpa_supplicant process
#     process = subprocess.Popen(
#         ["sudo", "wpa_supplicant", "-i", wireless_interface, "-c", "/etc/wpa_supplicant/wpa_supplicant-wlan1.conf"])
#
#     # Wait for the process to complete
#     process.wait()
#
#     # If the process returns a non-zero exit code, there was an error
#     if process.returncode != 0:
#         print("Failed to connect to WiFi network")
#     else:
#         print("Successfully connected to WiFi network")

import subprocess


def connect_to_wifi_network(network_ssid, network_password, wireless_interface):
    # Generate the configuration file
    config_text = f"""
    ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
    update_config=1
    country=US
    network={{
        ssid="{network_ssid}"
        psk="{network_password}"
    }}
    """

    print("Writing new wpa_supplicant file")
    # Write the configuration file to disk
    with open("/etc/wpa_supplicant/wpa_supplicant-wlan1.conf", "w") as f:
        f.write(config_text)

    # Start the wpa_cli process and add the new network configuration
    subprocess.Popen(["sudo", "wpa_cli", "-i", wireless_interface, "add_network"])
    subprocess.Popen(["sudo", "wpa_cli", "-i", wireless_interface, "set_network", "0", "ssid", f'"{network_ssid}"'])
    subprocess.Popen(["sudo", "wpa_cli", "-i", wireless_interface, "set_network", "0", "psk", f'"{network_password}"'])
    subprocess.Popen(["sudo", "wpa_cli", "-i", wireless_interface, "enable_network", "0"])
    subprocess.Popen(["sudo", "wpa_cli", "-i", wireless_interface, "save_config"])

    # Wait for the new network to be connected
    while True:
        print("Checking network status...")
        status = subprocess.check_output(["sudo", "wpa_cli", "-i", wireless_interface, "status"]).decode("utf-8")
        if f'ssid="{network_ssid}"' in status:
            print("Successfully connected to WiFi network")
            break


def disconnect_from_wifi_network(wireless_interface):
    # Get the current network id for wlan1
    print("Running disconnecting wifi")

    cmd = ["sudo", "wpa_cli", "-i", wireless_interface, "list_networks"]
    output = subprocess.check_output(cmd, universal_newlines=True)
    print("Disconnecting wlan1 output: ", output)
    network_id = None
    for line in output.splitlines()[1:]:
        fields = line.split()
        if len(fields) >= 3 and fields[2] == "CURRENT":
            network_id = fields[0]
            break

    # If a network is currently connected, disconnect from it
    print("disconnecting wlan1 network connection")
    if network_id is not None:
        subprocess.Popen(["sudo", "wpa_cli", "-i", wireless_interface, "disable_network", network_id])
        subprocess.Popen(["sudo", "wpa_cli", "-i", wireless_interface, "remove_network", network_id])
        subprocess.Popen(["sudo", "wpa_cli", "-i", wireless_interface, "save_config"])
