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


def init_dbus():
    """Initialize DBus connection."""
    try:
        if "bus" not in DB or not DB["bus"]:
            DB["bus"] = dbus.SystemBus()
        return DB["bus"]
    except Exception as e:
        raise handle_error(e, "Failed to initialize DBus")


def get_wifi_device():
    """Get WiFi device with error handling."""
    try:
        bus = init_dbus()  # Initialize DBus before use
        if not bus:
            raise ValueError("DBus not initialized")

        nm = bus.get_object(
            "org.freedesktop.NetworkManager", "/org/freedesktop/NetworkManager"
        )
        nm_props = dbus.Interface(nm, "org.freedesktop.DBus.Properties")
        devices = nm_props.Get("org.freedesktop.NetworkManager", "AllDevices")

        for device_path in devices:
            device = bus.get_object("org.freedesktop.NetworkManager", device_path)
            props = dbus.Interface(device, "org.freedesktop.DBus.Properties")
            device_type = props.Get(
                "org.freedesktop.NetworkManager.Device", "DeviceType"
            )
            if device_type == 2:  # WiFi device
                return device_path
        raise ValueError("No WiFi device found")
    except Exception as e:
        raise handle_error(e, "Failed to get WiFi device")


def get_access_points(bus, device_path):
    """Get list of WiFi access points."""
    try:
        device = bus.get_object("org.freedesktop.NetworkManager", device_path)
        wifi_device = dbus.Interface(
            device, "org.freedesktop.NetworkManager.Device.Wireless"
        )

        # Request scan
        wifi_device.RequestScan({})
        time.sleep(2)  # Wait for scan completion

        # Get access points
        aps = wifi_device.GetAccessPoints()
        networks = []

        for ap_path in aps:
            ap = bus.get_object("org.freedesktop.NetworkManager", ap_path)
            ap_props = dbus.Interface(ap, "org.freedesktop.DBus.Properties")

            ssid = ap_props.Get("org.freedesktop.NetworkManager.AccessPoint", "Ssid")
            strength = ap_props.Get(
                "org.freedesktop.NetworkManager.AccessPoint", "Strength"
            )

            networks.append(
                {"ssid": bytes(ssid).decode("utf-8"), "strength": int(strength)}
            )

        return networks
    except Exception as e:
        raise handle_error(e, "Failed to get access points")


@router.get("/scan", response_model=List[Dict[str, str]])
async def scan_networks():
    """Scan for available WiFi networks."""
    try:
        logging.info("Starting network scan...")
        bus = init_dbus()
        device_path = get_wifi_device()
        networks = get_access_points(bus, device_path)
        return networks
    except Exception as e:
        raise handle_error(e, "Network scan failed")


@router.get("/access-points")
async def get_access_points():
    """Get available WiFi access points and check if connected."""
    try:
        # Get system bus
        bus = init_dbus()

        # Get WiFi device path
        device_path = get_wifi_device()
        if not device_path:
            raise HTTPException(status_code=404, detail="No WiFi device found")

        # Create device object and interface
        device = bus.get_object("org.freedesktop.NetworkManager", device_path)
        wifi_interface = dbus.Interface(
            device, "org.freedesktop.NetworkManager.Device.Wireless"
        )
        device_props = dbus.Interface(device, "org.freedesktop.DBus.Properties")

        # Get active connection
        active_ap_path = device_props.Get(
            "org.freedesktop.NetworkManager.Device.Wireless", "ActiveAccessPoint"
        )

        # Request scan
        wifi_interface.RequestScan(dbus.Dictionary({}, signature="sv"))
        time.sleep(2)  # Wait for scan completion

        # Get access points
        access_points = wifi_interface.GetAccessPoints()
        networks = []

        for ap_path in access_points:
            ap = bus.get_object("org.freedesktop.NetworkManager", ap_path)
            ap_props = dbus.Interface(ap, "org.freedesktop.DBus.Properties")

            ssid = bytes(
                ap_props.Get("org.freedesktop.NetworkManager.AccessPoint", "Ssid")
            ).decode("utf-8")
            strength = ap_props.Get(
                "org.freedesktop.NetworkManager.AccessPoint", "Strength"
            )
            hwAddress = ap_props.Get(
                "org.freedesktop.NetworkManager.AccessPoint", "HwAddress"
            )
            # Check if this is the active access point
            connected = ap_path == active_ap_path

            networks.append(
                {
                    "ssid": ssid,
                    "strength": int(strength),
                    "connected": connected,
                    "id": f"{hwAddress}_{ssid}",  # Create a unique __ID__ by combining hwAddress and ssid
                }
            )

        return networks
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        filename, line_no, func, text = tb[-1]
        error_loc = f"File: {filename}, Line: {line_no}, Function: {func}"
        logging.error(f"Failed to get access points: {str(e)} at {error_loc}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get access points: {str(e)} at {error_loc}",
        )


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
