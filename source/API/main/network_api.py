from fastapi import APIRouter, HTTPException
import dbus
import asyncio
import logging
import time
import traceback
from typing import List, Dict
from dataClasses import NetworkCredentials
from db import DB

router = APIRouter(prefix="/network", tags=["Network"])


def handle_error(e: Exception, message: str) -> HTTPException:
    """Utility function for consistent error handling."""
    tb = traceback.extract_tb(e.__traceback__)
    filename, line_no, func, text = tb[-1]
    error_loc = f"File: {filename}, Line: {line_no}, Function: {func}"
    logging.error(f"{message}: {str(e)} at {error_loc}")
    return HTTPException(status_code=500, detail=f"{message}: {str(e)} at {error_loc}")


def get_wifi_device():
    """Get WiFi device with error handling."""
    try:
        if not DB["bus"]:
            raise ValueError("DBus not initialized")

        nm = DB["bus"].get_object(
            "org.freedesktop.NetworkManager", "/org/freedesktop/NetworkManager"
        )
        nm_props = dbus.Interface(nm, "org.freedesktop.DBus.Properties")
        devices = nm_props.Get("org.freedesktop.NetworkManager", "AllDevices")

        for device_path in devices:
            device = DB["bus"].get_object("org.freedesktop.NetworkManager", device_path)
            props = dbus.Interface(device, "org.freedesktop.DBus.Properties")
            device_type = props.Get(
                "org.freedesktop.NetworkManager.Device", "DeviceType"
            )
            if device_type == 2:  # WiFi device
                return device_path
        raise ValueError("No WiFi device found")
    except Exception as e:
        raise handle_error(e, "Failed to get WiFi device")


@router.get("/scan", response_model=List[Dict])
async def scan_networks():
    """Scan for available WiFi networks."""
    try:
        device_path = get_wifi_device()
        if not DB["bus"]:
            raise HTTPException(
                status_code=500, detail="Network system not initialized"
            )

        device = DB["bus"].get_object("org.freedesktop.NetworkManager", device_path)
        wireless = dbus.Interface(
            device, "org.freedesktop.NetworkManager.Device.Wireless"
        )

        try:
            access_points = wireless.GetAccessPoints()
        except dbus.exceptions.DBusException:
            # Trigger new scan if no APs found
            wireless.RequestScan({})
            await asyncio.sleep(2)  # Wait for scan
            access_points = wireless.GetAccessPoints()

        networks = []
        for ap_path in access_points:
            try:
                ap = DB["bus"].get_object("org.freedesktop.NetworkManager", ap_path)
                props = dbus.Interface(ap, "org.freedesktop.DBus.Properties")

                ssid = props.Get("org.freedesktop.NetworkManager.AccessPoint", "Ssid")
                strength = props.Get(
                    "org.freedesktop.NetworkManager.AccessPoint", "Strength"
                )

                if ssid:  # Only add if SSID exists
                    networks.append(
                        {
                            "ssid": bytes(ssid).decode("utf-8"),
                            "strength": int(strength),
                        }
                    )
            except Exception as e:
                logging.warning(f"Failed to get AP info: {e}")
                continue

        return {"networks": sorted(networks, key=lambda x: x["strength"], reverse=True)}

    except HTTPException:
        raise
    except Exception as e:
        raise handle_error(e, "Network scan failed")


@router.get("/access-points")
async def get_access_points():
    wifi_device = get_wifi_device()
    if not wifi_device:
        raise HTTPException(status_code=404, detail="No WiFi device found")

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
        try:
            ap_obj = DB["bus"].get_object("org.freedesktop.NetworkManager", ap)
            ap_props = dbus.Interface(ap_obj, "org.freedesktop.DBus.Properties")

            ssid = ap_props.Get("org.freedesktop.NetworkManager.AccessPoint", "Ssid")
            strength = ap_props.Get(
                "org.freedesktop.NetworkManager.AccessPoint", "Strength"
            )
            id = ap_props.Get("org.freedesktop.NetworkManager.AccessPoint", "HwAddress")

            if not bytearray(ssid).decode() == "":
                networks.append(
                    {"ssid": bytearray(ssid).decode(), "strength": strength, "id": id}
                )
        except Exception as e:
            print(f"Error processing access point: {e}")
            continue

    return networks


@router.post("/connect")
async def connect_network(credentials: NetworkCredentials):
    """Connect to WiFi network."""
    try:
        device_path = get_wifi_device()
        global DB
        # Get NetworkManager interface
        nm = DB["bus"].get_object(
            "org.freedesktop.NetworkManager", "/org/freedesktop/NetworkManager"
        )
        settings = DB["bus"].get_object(
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
        raise handle_error(e, "Network connection failed")
