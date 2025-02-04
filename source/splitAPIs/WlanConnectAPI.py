import dbus
from dbus.mainloop.glib import DBusGMainLoop
import time
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import socket
import asyncio
import random
from typing import Optional


class NetworkCredentials(BaseModel):
    ssid: str
    password: str


app = FastAPI()

# Initialize DBus
try:
    DBusGMainLoop(set_as_default=True)
    bus = dbus.SystemBus()
except Exception as e:
    print(f"Failed to initialize DBus: {e}")
    bus = None


def get_wifi_device():
    if not bus:
        raise HTTPException(status_code=500, detail="DBus not initialized")

    nm = bus.get_object(
        "org.freedesktop.NetworkManager", "/org/freedesktop/NetworkManager"
    )
    nm_props = dbus.Interface(nm, "org.freedesktop.DBus.Properties")
    devices = nm_props.Get("org.freedesktop.NetworkManager", "AllDevices")

    for device_path in devices:
        device = bus.get_object("org.freedesktop.NetworkManager", device_path)
        device_props = dbus.Interface(device, "org.freedesktop.DBus.Properties")
        device_type = device_props.Get(
            "org.freedesktop.NetworkManager.Device", "DeviceType"
        )
        if device_type == 2:  # WiFi device
            return device
    return None


@app.get("/access-points")
def get_access_points():
    wifi_device = get_wifi_device()
    if not wifi_device:
        return "No WiFi device found"

    # Request scan
    wifi_interface = dbus.Interface(
        wifi_device, "org.freedesktop.NetworkManager.Device.Wireless"
    )
    wifi_interface.RequestScan({})

    # Wait for scan to complete
    time.sleep(2)

    # Get access points
    access_points = wifi_interface.GetAllAccessPoints()

    networks = []

    for ap in access_points:
        ap_obj = bus.get_object("org.freedesktop.NetworkManager", ap)
        ap_props = dbus.Interface(ap_obj, "org.freedesktop.DBus.Properties")

        ssid = ap_props.Get("org.freedesktop.NetworkManager.AccessPoint", "Ssid")
        strength = ap_props.Get(
            "org.freedesktop.NetworkManager.AccessPoint", "Strength"
        )

        if not bytearray(ssid).decode() == "":
            networks.append({"ssid": bytearray(ssid).decode(), "strength": strength})

    return networks


@app.post("/connect")
async def connect_to_network(credentials: NetworkCredentials):
    try:
        # Get NetworkManager interface
        nm = bus.get_object(
            "org.freedesktop.NetworkManager", "/org/freedesktop/NetworkManager"
        )
        settings = bus.get_object(
            "org.freedesktop.NetworkManager", "/org/freedesktop/NetworkManager/Settings"
        )
        settings_interface = dbus.Interface(
            settings, "org.freedesktop.NetworkManager.Settings"
        )

        connection_settings = dbus.Dictionary(
            {
                "connection": dbus.Dictionary(
                    {
                        "id": dbus.String(credentials.ssid),
                        "type": dbus.String("802-11-wireless"),
                        "autoconnect": dbus.Boolean(True),
                    },
                    signature="sv",
                ),
                "802-11-wireless": dbus.Dictionary(
                    {
                        "ssid": dbus.ByteArray(credentials.ssid.encode()),
                        "mode": dbus.String("infrastructure"),
                        "security": dbus.String("802-11-wireless-security"),
                    },
                    signature="sv",
                ),
                "802-11-wireless-security": dbus.Dictionary(
                    {
                        "key-mgmt": dbus.String("wpa-psk"),
                        "psk": dbus.String(credentials.password),
                    },
                    signature="sv",
                ),
                "ipv4": dbus.Dictionary(
                    {"method": dbus.String("auto")}, signature="sv"
                ),
                "ipv6": dbus.Dictionary(
                    {"method": dbus.String("auto")}, signature="sv"
                ),
            },
            signature="sa{sv}",
        )

        new_connection = settings_interface.AddConnection(connection_settings)

        # Activate the connection
        nm_interface = dbus.Interface(nm, "org.freedesktop.NetworkManager")
        wifi_device = get_wifi_device()
        nm_interface.ActivateConnection(new_connection, wifi_device, "/")

        return {"status": "success", "message": f"Connected to {credentials.ssid}"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
