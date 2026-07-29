"""
ndiem_transformer.py
====================================================================
Core NDIEM transformation module.

Contains:
  - Protocol Adapters      : map_crazyflie / map_hexacopter / map_tello
  - Message Handler Layer  : build_tree  (native -> NDIEM XML tree)
  - Serialization          : serialize   (tree -> bytes)
  - Validator              : SCHEMA.validate
  - Receiver / GCS         : parse, receiver_can_consume

Requires: lxml, and schema/drone.xsd
"""

import json
from lxml import etree

NS = "http://finalNdiem/1.0"
NSMAP = {None: NS}

# Schema path is resolved by the caller; default assumes schema/drone.xsd
SCHEMA_PATH = "schema/drone.xsd"

NDIEM_ELEMENT = {"battery_pct": "chargePercent", "battery_voltage": "chargeValue"}

INFO = {
    "crazyflie":  ("CF-01",    "Bitcraze",  "Crazyflie 2.1", "Micro-quadrotor"),
    "hexacopter": ("HEX-01",   "ArduPilot", "Hexacopter",    "Hexarotor"),
    "tello":      ("TELLO-01", "Ryze/DJI",  "Tello EDU",     "Micro-quadrotor"),
}


# ---------------------------------------------------------------------
# PROTOCOL ADAPTERS  (native protocol fields -> common NDIEM fields)
# ---------------------------------------------------------------------
def map_crazyflie(r):
    t = r["telemetry"]
    return {"roll": t["stabilizer.roll"], "pitch": t["stabilizer.pitch"],
            "yaw": t["stabilizer.yaw"]}


def map_tello(r):
    t = r["telemetry"]
    return {"roll": t["roll"], "pitch": t["pitch"], "yaw": t["yaw"],
            "vx": t["vgx"], "vy": t["vgy"], "vz": t["vgz"],
            "alt": t["h"], "battery_pct": t["bat"]}


def map_hexacopter(r):
    t = r["telemetry"]
    m = t.get("mavpackettype")
    if m == "ATTITUDE":
        return {"roll": t["roll"], "pitch": t["pitch"], "yaw": t["yaw"]}
    if m == "LOCAL_POSITION_NED":
        return {"lat": t["x"], "lon": t["y"], "alt": -t["z"],
                "vx": t["vx"], "vy": t["vy"], "vz": t["vz"]}
    if m == "SYS_STATUS":
        return {"battery_pct": max(t["battery_remaining"], 0),
                "battery_voltage": t["voltage_battery"] / 1000.0}
    if m == "BATTERY_STATUS":
        return {"battery_pct": max(t["battery_remaining"], 0)}
    if m == "VFR_HUD":
        return {"alt": t["alt"]}
    if m == "ALTITUDE":
        return {"alt": t["altitude_relative"]}
    return {}


MAPPERS = {"crazyflie": map_crazyflie,
           "hexacopter": map_hexacopter,
           "tello": map_tello}


# ---------------------------------------------------------------------
# MESSAGE HANDLER LAYER  (transformation + serialization)
# ---------------------------------------------------------------------
def S(parent, tag, txt=None):
    e = etree.SubElement(parent, f"{{{NS}}}{tag}")
    if txt is not None:
        e.text = str(txt)
    return e


def build_tree(platform, mp, mid):
    """
    Transformation stage: native UAV message -> NDIEM XML tree
    (in memory). Excludes serialization and validation.
    """
    i = INFO[platform]
    root = etree.Element(f"{{{NS}}}NDIEMMessage", nsmap=NSMAP)
    S(root, "messageID", mid)
    S(root, "timestamp", "2025-01-01T00:00:00")
    h = S(root, "Header")
    S(h, "senderID", platform)
    S(h, "receiverID", "GCS")
    idn = S(root, "UavIdentificationData")
    S(idn, "uavID", i[0]); S(idn, "uavManufacturer", i[1])
    S(idn, "uavModel", i[2]); S(idn, "uavType", i[3])

    ori = all(k in mp for k in ("roll", "pitch", "yaw"))
    vel = all(k in mp for k in ("vx", "vy", "vz"))
    pos = any(k in mp for k in ("lat", "lon", "alt"))
    bat = "battery_pct" in mp

    if ori or vel or pos or bat:
        tel = S(root, "UavTelemetryData")
        S(tel, "telemetryTimestamp", "2025-01-01T00:00:00")
        S(tel, "status", "OK")
        if bat:
            b = S(tel, "UavBattery")
            S(b, "chargeValue", mp.get("battery_voltage", mp["battery_pct"]))
            S(b, "chargePercent", int(mp["battery_pct"]))
        if ori:
            o = S(tel, "UavOrientation")
            S(o, "pitch", mp["pitch"]); S(o, "yaw", mp["yaw"]); S(o, "roll", mp["roll"])
        if vel:
            v = S(tel, "UavVelocity")
            S(v, "vx", mp["vx"]); S(v, "vy", mp["vy"]); S(v, "vz", mp["vz"])
        if pos:
            ps = S(tel, "UavPosition")
            S(ps, "lat", mp.get("lat", 0.0)); S(ps, "lon", mp.get("lon", 0.0))
            S(ps, "alt", mp.get("alt", 0.0))
    return root


def serialize(root):
    """Serialization stage: XML tree -> byte string."""
    return etree.tostring(root)


def build(platform, mp, mid):
    """Transform + serialize, for callers that need bytes."""
    return serialize(build_tree(platform, mp, mid))


# ---------------------------------------------------------------------
# RECEIVER / GCS
# ---------------------------------------------------------------------
def parse(xb):
    root = etree.fromstring(xb)
    out = {}
    for el in root.iter():
        tag = etree.QName(el).localname
        if el.text and el.text.strip():
            out[tag] = el.text.strip()
    return out


def receiver_can_consume(parsed, truth, cfg):
    if cfg == "no_xml_schema":
        return False
    exp = list(truth.keys())
    return bool(exp) and all(NDIEM_ELEMENT.get(k, k) in parsed for k in exp)


def values_match(pv, sv):
    if pv is None:
        return False
    try:
        return abs(float(pv) - float(sv)) < 1e-6
    except (ValueError, TypeError):
        return str(pv) == str(sv)


def load_schema(path=SCHEMA_PATH):
    return etree.XMLSchema(etree.parse(path))


def load_dataset(path):
    return json.load(open(path))
