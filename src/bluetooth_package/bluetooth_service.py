#!/usr/bin/env python3

import logging

import dbus
import dbus.exceptions
import dbus.mainloop.glib
import dbus.service

# from ble import (
#     Advertisement,
#     Characteristic,
#     Service,
#     Application,
#     find_adapter,
#     Descriptor,
#     Agent,
# )
import array
from enum import Enum

from .ble import find_adapter, Advertisement, Descriptor, Characteristic, Service, Agent, Application

MainLoop = None
try:
    from gi.repository import GLib
    MainLoop = GLib.MainLoop
except ImportError:
    import gobject as GObject

    MainLoop = GObject.MainLoop

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logHandler = logging.StreamHandler()
filelogHandler = logging.FileHandler("logs.log")
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logHandler.setFormatter(formatter)
filelogHandler.setFormatter(formatter)
logger.addHandler(filelogHandler)
logger.addHandler(logHandler)


class InvalidArgsException(dbus.exceptions.DBusException):
    _dbus_error_name = "org.freedesktop.DBus.Error.InvalidArgs"


class NotSupportedException(dbus.exceptions.DBusException):
    _dbus_error_name = "org.bluez.Error.NotSupported"


class NotPermittedException(dbus.exceptions.DBusException):
    _dbus_error_name = "org.bluez.Error.NotPermitted"


class InvalidValueLengthException(dbus.exceptions.DBusException):
    _dbus_error_name = "org.bluez.Error.InvalidValueLength"


class FailedException(dbus.exceptions.DBusException):
    _dbus_error_name = "org.bluez.Error.Failed"


class JXNS1Service(Service):
    """
    Dummy test service that provides characteristics and descriptors that
    exercise various API functionality.

    """

    WIFI_SVC_UUID = "12634d89-d598-4874-8e86-7d042ee07ba7"

    def __init__(self, bus, index, callback):
        Service.__init__(self, bus, index, self.WIFI_SVC_UUID, True)
        self.add_characteristic(WifiPasswordCharacteristic(bus, 0, callback, self))


class WifiPasswordCharacteristic(Characteristic):
    uuid = "4116f8d2-9f66-4f58-a53d-fc7440e7c14e"
    description = b"Set Facility's Wifi password"

    class State(Enum):
        on = "ON"
        off = "OFF"
        unknown = "UNKNOWN"

        @classmethod
        def has_value(cls, value):
            return value in cls._value2member_map_

    power_options = {"ON", "OFF", "UNKNOWN"}

    def __init__(self, bus, index, callback, service):
        Characteristic.__init__(
            self, bus, index, self.uuid, ["encrypt-read", "encrypt-write"], service,
        )

        self.value = [0xFF]
        self.add_descriptor(CharacteristicUserDescriptionDescriptor(bus, 1, self))
        self.callback = callback

    def ReadValue(self, options):
        logger.debug("power Read: " + repr(self.value))
        res = None
        try:
            # res = requests.get(JXNBaseUrl + "/sensor")

            self.value = bytearray("Set password with format 'wifi,SSID,psk'", encoding="utf8")
        except Exception as e:
            logger.error(f"Error getting status {e}")
            self.value = bytearray(self.State.unknown, encoding="utf8")

        return self.value

    def WriteValue(self, value, options):
        logger.debug("power Write: " + repr(value))
        cmd = bytes(value).decode("utf-8")
        logger.info(f"receiving command: {cmd}")
        self.callback(cmd)
        # if self.State.has_value(cmd):
        #     # write it to machine
        #     logger.info("writing {cmd} to machine")
        #     data = {"cmd": cmd.lower()}
        #     try:
        #         logger.info(f"state written {cmd}")
        #         # res = requests.post(JXNBaseUrl + "/sensor/cmds", json=data)
        #     except Exceptions as e:
        #         logger.error(f"Error updating machine state: {e}")
        # else:
        #     logger.info(f"invalid state written {cmd}")
        #     raise NotPermittedException

        self.value = value


class CharacteristicUserDescriptionDescriptor(Descriptor):
    """
    Writable CUD descriptor.
    """
    CUD_UUID = "2901"

    def __init__(
            self, bus, index, characteristic,
    ):
        self.value = array.array("B", characteristic.description)
        self.value = self.value.tolist()
        Descriptor.__init__(self, bus, index, self.CUD_UUID, ["read"], characteristic)

    def ReadValue(self, options):
        return self.value

    def WriteValue(self, value, options):
        if not self.writable:
            raise NotPermittedException()
        self.value = value


class JXNAdvertisement(Advertisement):
    def __init__(self, bus, index):
        Advertisement.__init__(self, bus, index, "peripheral")
        self.add_manufacturer_data(
            0xFFFF, [0x70, 0x74],
        )
        self.add_service_uuid(JXNS1Service.WIFI_SVC_UUID)

        self.add_local_name("JXN")
        self.include_tx_power = True


class JXNBluetoothService:
    def __int__(self):
        self.bus = dbus.SystemBus()
        self.adapter = find_adapter(self.bus)
        if not self.adapter:
            logger.critical("GattManager1 interface not found")
            return


class BluetoothService:
    AGENT_PATH = "/com/punchthrough/agent"
    BLUEZ_SERVICE_NAME = "org.bluez"
    GATT_MANAGER_IFACE = "org.bluez.GattManager1"
    LE_ADVERTISEMENT_IFACE = "org.bluez.LEAdvertisement1"
    LE_ADVERTISING_MANAGER_IFACE = "org.bluez.LEAdvertisingManager1"

    def __init__(self, callback):
        self.mainloop = None
        self.callback = callback

    def start(self):
        print("starting")
        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

        # Get the system bus
        bus = dbus.SystemBus()

        # Get the BLE controller
        adapter = self.find_adapter(bus, self.BLUEZ_SERVICE_NAME, self.LE_ADVERTISING_MANAGER_IFACE)
        if not adapter:
            logger.critical("GattManager1 interface not found")
            return

        adapter_obj = bus.get_object(self.BLUEZ_SERVICE_NAME, adapter)
        adapter_props = dbus.Interface(adapter_obj, "org.freedesktop.DBus.Properties")

        # Set powered property on the controller to on
        adapter_props.Set("org.bluez.Adapter1", "Powered", dbus.Boolean(1))

        # Get manager objects
        service_manager = dbus.Interface(adapter_obj, self.GATT_MANAGER_IFACE)
        ad_manager = dbus.Interface(adapter_obj, self.LE_ADVERTISING_MANAGER_IFACE)

        advertisement = JXNAdvertisement(bus, 0)
        obj = bus.get_object(self.BLUEZ_SERVICE_NAME, "/org/bluez")

        agent = Agent(bus, self.AGENT_PATH)

        app = Application(bus)
        app.add_service(JXNS1Service(bus, 2, self.callback))

        self.mainloop = GLib.MainLoop()

        agent_manager = dbus.Interface(obj, "org.bluez.AgentManager1")
        agent_manager.RegisterAgent(self.AGENT_PATH, "NoInputNoOutput")

        ad_manager.RegisterAdvertisement(
            advertisement.get_path(),
            {},
            reply_handler=self.register_ad_cb,
            error_handler=self.register_ad_error_cb,
        )

        logger.info("Registering GATT application...")

        service_manager.RegisterApplication(
            app.get_path(),
            {},
            reply_handler=self.register_app_cb,
            error_handler=[self.register_app_error_cb],
        )

        agent_manager.RequestDefaultAgent(self.AGENT_PATH)

        self.mainloop.run()

    @staticmethod
    def find_adapter(bus, BLUEZ_SERVICE_NAME, LE_ADVERTISING_MANAGER_IFACE):
        manager_obj = bus.get_object(BLUEZ_SERVICE_NAME, "/")
        manager = dbus.Interface(manager_obj, "org.freedesktop.DBus.ObjectManager")
        objects = manager.GetManagedObjects()

        for obj, ifaces in objects.items():
            adapter = ifaces.get(LE_ADVERTISING_MANAGER_IFACE)
            if adapter:
                return obj

        return None

    def register_ad_cb(self):
        # Register Advertisement callback logic
        logger.info("Advertisement registered")
        pass

    def register_ad_error_cb(self, error):
        logger.critical("Failed to register advertisement: " + str(error))
        self.mainloop.quit()
        pass

    def register_app_cb(self):
        # Register Application callback logic
        logger.info("GATT application registered")
        pass

    def register_app_error_cb(self, error):
        # Register Application error callback logic
        logger.critical("Failed to register application: " + str(error))
        self.mainloop.quit()
        pass
