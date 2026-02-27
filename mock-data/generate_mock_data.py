#!/usr/bin/env python3
"""
Fleet Connectivity Intelligence — Mock Data Generator
=====================================================

Generates realistic demo data for the MyGeotab Add-In by combining:
  1. Geotab device telemetry patterns (signal strength, GPS, faults)
  2. Aeris IoT Accelerator API response structures (cell towers, events, usage)

The output mirrors what the Add-In would receive from live API calls to both
platforms. Field names, value ranges, and data types are taken directly from
the 7 OpenAPI 3.0 specifications in the api-specs/ folder.

Data model per vehicle:
  - Geotab side:  id, name, lat/lon, speed, driving, comm status, signal (dBm)
  - Aeris side:   IMSI, IMEI, carrier, MCC/MNC, LAC, Cell ID, RAT type,
                  data usage, plan balance, network events, error log, incidents

Health tiers are assigned based on composite scoring:
  - healthy:   signal >= 70 dBm, drops <= 1, uptime >= 98%
  - minor:     signal 60-69 OR drops 2-3 OR uptime 95-98%
  - warning:   signal 50-69 AND drops 3-7 OR uptime 90-96%
  - critical:  signal < 50 OR drops >= 8 OR uptime < 90%

Usage:
  python generate_mock_data.py              # prints JSON to stdout
  python generate_mock_data.py --output mock_data.json  # saves to file

Author: Tim — Telenor IoT / Geotab Vibe Coding Challenge 2026
"""

import json
import random
import argparse
from datetime import datetime, timedelta, timezone

# ---------------------------------------------------------------------------
# Configuration — matches the real Aeris API field constraints
# ---------------------------------------------------------------------------

# Carriers observed in Iberian Peninsula fleet (MCC-MNC from Aeris Location API)
CARRIERS = [
    {"carrier": "Orange ES",    "mcc": "214", "mnc": "03", "country": "Spain"},
    {"carrier": "Vodafone PT",  "mcc": "268", "mnc": "01", "country": "Portugal"},
    {"carrier": "NOS PT",       "mcc": "268", "mnc": "03", "country": "Portugal"},
    {"carrier": "Movistar",     "mcc": "214", "mnc": "07", "country": "Spain"},
    {"carrier": "Vodafone ES",  "mcc": "214", "mnc": "01", "country": "Spain"},
]

# Cell towers per carrier (LAC + Cell ID from Aeris Subscription Location API)
CELL_SITES = {
    "Orange ES":   [{"lac": "103", "cell": "49885"}, {"lac": "803", "cell": "64084"}],
    "Vodafone PT": [{"lac": "131", "cell": "47723"}, {"lac": "954", "cell": "49145"}],
    "NOS PT":      [{"lac": "234", "cell": "18145"}, {"lac": "354", "cell": "12245"}],
    "Movistar":    [{"lac": "496", "cell": "25821"}, {"lac": "367", "cell": "26890"}],
    "Vodafone ES": [{"lac": "703", "cell": "56754"}, {"lac": "725", "cell": "40532"}],
}

# Radio Access Technology types (from Aeris Signalling Events API rat_type field)
# rat_type: 1=GSM, 2=WCDMA, 4=LTE
RAT_MAP = {1: "GSM", 2: "WCDMA", 4: "LTE"}

# Network event codes (from Aeris Subscription Signalling Events API)
EVENT_CODES = [
    "ATTACH", "DETACH", "HANDOVER", "TAU",
    "PDP_ACTIVATE", "PDP_DEACTIVATE", "SERVICE_REQUEST"
]

# Error types observed in real Aeris network diagnostics
ERROR_TYPES = [
    "CONTEXT_DEACTIVATION",  # Data session torn down by network
    "NETWORK_TIMEOUT",       # No response from SGSN/MME
    "AUTH_FAILURE",          # SIM auth rejected by visited network
    "GPRS_DETACH",           # Network-initiated GPRS detach
    "ATTACH_REJECT",         # Network attach request rejected
    "PDP_REJECT",            # Packet data session denied by GGSN
]

ERROR_DESCRIPTIONS = {
    "CONTEXT_DEACTIVATION": "Data session torn down by network — congestion or admin action",
    "NETWORK_TIMEOUT":      "No response from SGSN/MME within timeout window — signalling path failure",
    "AUTH_FAILURE":          "SIM authentication rejected by visited network — possible roaming agreement issue",
    "GPRS_DETACH":          "Network-initiated GPRS detach — SIM deregistered from packet domain",
    "ATTACH_REJECT":        "Network attach request rejected — IMSI not provisioned for this PLMN",
    "PDP_REJECT":           "Packet data session activation denied by GGSN — APN config or quota exceeded",
}

# Incident types (from Aeris Incident Management API)
INCIDENT_TYPES = [
    {"type": "3G-FALLBACK",   "desc": "Persistent 3G/2G fallback in LTE coverage area", "severity": "HIGH"},
    {"type": "SIG-LOSS",      "desc": "Intermittent signal loss detected",               "severity": "CRITICAL"},
    {"type": "DATA-RETRY",    "desc": "Excessive data retransmissions",                  "severity": "CRITICAL"},
    {"type": "PERF-DEGRADE",  "desc": "Network performance degradation observed",        "severity": "MEDIUM"},
]

# Fleet locations — Iberian Peninsula depot/route coordinates
DEPOT_LOCATIONS = [
    (41.8975, -8.8574),   # Viana do Castelo depot
    (42.2348, -8.7131),   # Vigo area
    (42.1336, -8.7983),   # Redondela area
    (42.2644, -8.4569),   # Ourense area
    (42.0410, -8.6481),   # Tui border area
    (41.5283,  0.5164),   # Lleida area
    (39.4852, -0.5346),   # Valencia area
    (38.6322, -3.4661),   # Central Spain route
]

# ---------------------------------------------------------------------------
# Generator functions
# ---------------------------------------------------------------------------

def generate_imsi(index):
    """Generate IMSI in format matching Aeris Subscription Location API."""
    return f"21401{str(index).zfill(10)}"


def generate_imei(index):
    """Generate IMEI matching Aeris Device Reconnect API identifier format."""
    base = 35684900000000 + (index * 100) + random.randint(10, 99)
    return str(base)


def assign_health_tier(signal, drops, uptime):
    """Assign health tier based on composite connectivity scoring."""
    if signal < 50 or drops >= 8 or uptime < 90:
        return "critical"
    elif (50 <= signal < 65 and drops >= 3) or (drops >= 3 and uptime < 96):
        return "warning"
    elif signal < 70 or drops >= 2 or uptime < 98:
        return "minor"
    else:
        return "healthy"


def generate_vehicle(index, now):
    """Generate one vehicle with correlated Geotab + Aeris data."""

    # Decide health profile first (drives all other values)
    # Distribution: 60% healthy, 10% minor, 10% warning, 10% critical
    roll = random.random()
    if roll < 0.10:
        profile = "critical"
    elif roll < 0.20:
        profile = "warning"
    elif roll < 0.30:
        profile = "minor"
    else:
        profile = "healthy"

    # Carrier assignment
    carrier_info = random.choice(CARRIERS)
    carrier = carrier_info["carrier"]
    site = random.choice(CELL_SITES[carrier])

    # Location — slight jitter from depot
    depot = random.choice(DEPOT_LOCATIONS)
    lat = depot[0] + random.uniform(-0.02, 0.02)
    lon = depot[1] + random.uniform(-0.02, 0.02)

    # Profile-driven parameters
    if profile == "critical":
        signal = random.randint(20, 45)
        rat_code = random.choice([1, 2])  # Fallen back to GSM/WCDMA
        drops = random.randint(8, 20)
        uptime = round(random.uniform(85, 93), 1)
        err_count = random.randint(15, 40)
        err_types = random.sample(ERROR_TYPES, k=random.randint(3, 5))
        data_used = random.randint(800, 1400)
        pdp_attempts = random.randint(100, 150)
        pdp_success = random.randint(40, 70)
        loc_updates = random.randint(200, 360)
        loc_success = random.randint(100, 220)
        num_events = random.randint(3, 12)
        num_incidents = random.randint(1, 3)
    elif profile == "warning":
        signal = random.randint(55, 68)
        rat_code = random.choice([2, 4])
        drops = random.randint(3, 7)
        uptime = round(random.uniform(90, 97), 1)
        err_count = random.randint(5, 15)
        err_types = random.sample(ERROR_TYPES, k=random.randint(2, 3))
        data_used = random.randint(400, 800)
        pdp_attempts = random.randint(50, 90)
        pdp_success = random.randint(30, 65)
        loc_updates = random.randint(200, 300)
        loc_success = random.randint(100, 180)
        num_events = random.randint(3, 6)
        num_incidents = random.randint(0, 1)
    elif profile == "minor":
        signal = random.randint(63, 76)
        rat_code = 4  # LTE
        drops = random.randint(1, 3)
        uptime = round(random.uniform(96, 99.5), 1)
        err_count = random.randint(1, 5)
        err_types = random.sample(ERROR_TYPES[:2], k=random.randint(1, 2))
        data_used = random.randint(200, 450)
        pdp_attempts = random.randint(30, 60)
        pdp_success = random.randint(25, 45)
        loc_updates = random.randint(100, 200)
        loc_success = random.randint(100, 190)
        num_events = random.randint(2, 3)
        num_incidents = 0
    else:  # healthy
        signal = random.randint(75, 106)
        rat_code = 4  # LTE
        drops = random.randint(0, 1)
        uptime = round(random.uniform(98, 100), 1)
        err_count = random.randint(0, 1)
        err_types = random.sample(ERROR_TYPES[:1], k=1) if err_count > 0 else []
        data_used = random.randint(100, 350)
        pdp_attempts = random.randint(10, 30)
        pdp_success = pdp_attempts - random.randint(0, 3)
        loc_updates = random.randint(50, 120)
        loc_success = loc_updates - random.randint(0, 5)
        num_events = 1
        num_incidents = 0

    rat = RAT_MAP[rat_code]
    plan = 2048  # MB — standard IoT plan from Consumer Connectivity API
    bal_pct = round((plan - data_used) / plan * 100, 1)
    last_disc = random.randint(5 if profile == "critical" else 300, 10000)
    driving = random.random() < 0.2
    speed = random.choice([0, random.randint(15, 95)]) if driving else 0

    # Generate network events (from Aeris Signalling Events API schema)
    events = []
    for e in range(num_events):
        evt_time = now - timedelta(hours=random.uniform(0.5, 24))
        events.append({
            "id": f"EVT-{str(index).zfill(2)}-{str(e).zfill(3)}",
            "code": random.choice(EVENT_CODES),
            "occurred_at": evt_time.isoformat(),
            "rat_type": rat_code,
            "mcc": carrier_info["mcc"],
            "mnc": carrier_info["mnc"],
            "lac": site["lac"],
            "cell_id": site["cell"],
            "pdprx": random.randint(1000, 500000),
            "pdptx": random.randint(1000, 200000),
        })
    events.sort(key=lambda x: x["occurred_at"], reverse=True)

    # Generate incidents (from Aeris Incident Management API schema)
    incidents = []
    for inc in range(num_incidents):
        inc_type = random.choice(INCIDENT_TYPES)
        inc_time = now - timedelta(hours=random.uniform(1, 72))
        incidents.append({
            "id": f"INC-{str(index).zfill(2)}-{inc_type['type']}",
            "type": inc_type["type"],
            "description": inc_type["desc"],
            "status": random.choice(["NEW", "ASSIGNED", "IN_PROGRESS"]),
            "severity": inc_type["severity"],
            "created": inc_time.isoformat(),
        })

    # Last error timestamp
    last_err = None
    if err_count > 0 and profile in ("critical", "warning", "minor"):
        last_err = (now - timedelta(minutes=random.randint(10, 300))).strftime("%Y-%m-%dT%H:%M:00Z")

    tier = assign_health_tier(signal, drops, uptime)

    return {
        # Geotab Device fields
        "id": f"b{index:x}",
        "nm": f"Demo - {str(index).zfill(2)}",
        "lat": round(lat, 7),
        "lon": round(lon, 7),
        "spd": speed,
        "drv": driving,
        "comm": True,
        # Aeris Subscription Location API fields
        "imsi": generate_imsi(index),
        "sig": signal,
        "tier": tier,
        "rat": rat,
        "carrier": carrier,
        "mcc": carrier_info["mcc"],
        "mnc": carrier_info["mnc"],
        "lac": site["lac"],
        "cell": site["cell"],
        # Aeris Consumer Connectivity API fields
        "used": data_used,
        "plan": plan,
        "balPct": bal_pct,
        # Aeris Signalling metrics
        "drops": drops,
        "uptime": uptime,
        "lastDisc": last_disc,
        # Aeris Incident Management API
        "incidents": incidents,
        # Aeris Signalling Events API
        "events": events,
        # Aeris device identifiers
        "imei": generate_imei(index),
        # Aeris Org Signaling Aggregations API metrics
        "pdpAttempts": pdp_attempts,
        "pdpSuccess": pdp_success,
        "locUpdates": loc_updates,
        "locSuccess": loc_success,
        "errCount": err_count,
        "errTypes": err_types,
        "lastErr": last_err,
        # Aeris Signalling Usages API
        "dlBytes": random.randint(70_000_000, 1_000_000_000),
        "ulBytes": random.randint(20_000_000, 420_000_000),
        "country": carrier_info["country"],
    }


def generate_cell_towers(count=90):
    """Generate cell tower locations for the coverage map."""
    towers = []
    for _ in range(count):
        lat = random.uniform(41.0, 43.5)
        lon = random.uniform(-9.5, -6.5)
        carrier_info = random.choice(CARRIERS)
        carrier = carrier_info["carrier"]
        rat = random.choice(["LTE", "WCDMA", "GSM"])
        weak = random.random() < 0.15  # 15% chance of weak coverage
        towers.append({
            "lat": round(lat, 5),
            "lon": round(lon, 5),
            "rat": rat,
            "carrier": carrier,
            "mcc": carrier_info["mcc"],
            "mnc": carrier_info["mnc"],
            "lac": str(random.randint(100, 999)),
            "cell": str(random.randint(10000, 65000)),
            "weak": weak,
        })
    return towers


def generate_error_log(vehicles, now):
    """Generate error log entries for vehicles with errors."""
    errors = []
    for v in vehicles:
        if v["tier"] == "healthy":
            continue
        if not v["lastErr"]:
            continue
        for err_type in v["errTypes"]:
            errors.append({
                "ts": v["lastErr"],
                "vehicle": v["nm"],
                "imsi": v["imsi"],
                "imei": v["imei"],
                "carrier": v["carrier"],
                "country": v["country"],
                "rat": v["rat"],
                "errCode": err_type,
                "errDesc": ERROR_DESCRIPTIONS.get(err_type, "Unknown error"),
                "cell": f"{v['mcc']}-{v['mnc']}-{v['lac']}-{v['cell']}",
                "tier": v["tier"],
            })
    # Sort by timestamp descending (most recent first)
    errors.sort(key=lambda x: x["ts"], reverse=True)
    return errors


def main():
    parser = argparse.ArgumentParser(description="Generate Fleet Connectivity Intelligence mock data")
    parser.add_argument("--vehicles", type=int, default=50, help="Number of vehicles (default: 50)")
    parser.add_argument("--towers", type=int, default=90, help="Number of cell towers (default: 90)")
    parser.add_argument("--output", type=str, default=None, help="Output file (default: stdout)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    args = parser.parse_args()

    random.seed(args.seed)
    now = datetime.now(timezone.utc)

    # Generate fleet
    vehicles = [generate_vehicle(i + 1, now) for i in range(args.vehicles)]

    # Generate cell towers for coverage map
    towers = generate_cell_towers(args.towers)

    # Generate error log
    errors = generate_error_log(vehicles, now)

    # Assemble output — matches the MOCK object structure in the Add-In HTML
    output = {
        "v": vehicles,      # vehicles array
        "t": towers,        # cell towers array
        "errors": errors,   # error log array
    }

    result = json.dumps(output, indent=2)

    if args.output:
        with open(args.output, "w") as f:
            f.write(result)
        print(f"Written {len(vehicles)} vehicles, {len(towers)} towers, {len(errors)} errors to {args.output}")
    else:
        print(result)

    # Print summary
    tiers = {}
    for v in vehicles:
        tiers[v["tier"]] = tiers.get(v["tier"], 0) + 1
    print(f"\n--- Fleet Summary ---", file=__import__('sys').stderr)
    print(f"Vehicles: {len(vehicles)}", file=__import__('sys').stderr)
    print(f"Towers:   {len(towers)}", file=__import__('sys').stderr)
    print(f"Errors:   {len(errors)}", file=__import__('sys').stderr)
    print(f"Tiers:    {tiers}", file=__import__('sys').stderr)


if __name__ == "__main__":
    main()
