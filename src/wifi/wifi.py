import subprocess
import time


def restart_wireless_interface(wireless_interface):
    subprocess.run(["sudo", "systemctl", "restart", f"wpa_supplicant@{wireless_interface}"])
    time.sleep(2)

    # Disable the wireless interface
    subprocess.run(["sudo", "wpa_cli", "-i", wireless_interface, "reconfigure"])
    time.sleep(2)

    subprocess.run(["sudo", "ifconfig", "-i", wireless_interface, "reconfigure"])
    time.sleep(2)

    enable_wireless_interface("wlan0")
    time.sleep(2)

    enable_wireless_interface("wlan1")
    time.sleep(2)


def enable_wireless_interface(wireless_interface):
    # Enable the wireless interface
    subprocess.run(["sudo", "ifconfig", wireless_interface, "up"])


def connect_to_wifi_network(network_ssid, network_password, wireless_interface):
    # Generate the configuration file
    print("network ssid: ", network_ssid)
    config_text = \
        f"""
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1
country=US
network={{
    ssid="{network_ssid}"
    psk="{network_password}"
}}"""

    print("Writing new wpa_supplicant file")
    # Write the configuration file to disk
    with open("/etc/wpa_supplicant/wpa_supplicant-wlan1.conf", "w") as f:
        f.write(config_text)

    # Restart the wireless interface
    restart_wireless_interface(wireless_interface)

    # Wait until the connection is established
    while True:
        status = subprocess.check_output(["sudo", "wpa_cli", "-i", wireless_interface, "status"]).decode("utf-8")
        status_dict = dict(line.split("=") for line in status.splitlines() if "=" in line)
        if status_dict.get("ssid") == network_ssid:
            print("Successfully connected to WiFi network")
            break
        time.sleep(1)


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
