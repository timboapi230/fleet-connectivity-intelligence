# Fleet Connectivity Intelligence

**A MyGeotab Add-In that bridges device telemetry and cellular network intelligence — built for the [Geotab Vibe Coding Challenge 2026](https://luma.com/h6ldbaxp).**

> **The Problem:** Geotab tells fleet managers *that* a vehicle has weak signal. But it can't tell them *why*. Is it the tower? The SIM? The carrier? A network outage? Today, that answer lives in a completely separate platform that fleet managers never see.
>
> **The Solution:** Fleet Connectivity Intelligence correlates Geotab device data with Aeris IoT Accelerator network intelligence to give fleet managers root-cause connectivity diagnostics — all inside MyGeotab, where they already work.

![Architecture Diagram](architecture.svg)

---

## Why This Exists

I work as a cellular connectivity supplier through **Telenor IoT**. Geotab is one of our customers — their GO9 telematics devices connect to cellular networks through SIM cards that we provision and manage on the Aeris platform.


Every day, I see both sides of the connectivity story:

- **Inside MyGeotab**, fleet managers see a signal strength number (e.g., 37 dBm) and device fault codes — but they have no idea which cell tower is serving the vehicle, what carrier is active, or whether the SIM is about to run out of data.

- **Inside the Aeris/Telenor IoT portal**, I see cell tower identities, network signaling events, data consumption, error logs, and incident tickets — but I have no GPS coordinates, no vehicle names, and no fleet context.

**Neither platform alone can answer the question: "Why is Demo-31 dropping data?"**

This Add-In brings both perspectives together for the first time.

---

## What It Does

Fleet Connectivity Intelligence is a single-file HTML Add-In that is installed as a new page inside MyGeotab. It provides **6 tabs** of combined intelligence:


### Tab 1: Problem Alerts
Vehicles scored into health tiers (Critical / Warning / Minor / Healthy) based on combined Geotab + Aeris data. Each alert card shows signal strength, radio technology (LTE/3G/2G), connection drops, uptime, error codes, active incidents, and a full network event log — all on one card.

### Tab 2: Coverage Heatmap
GPS coordinates from Geotab overlaid with signal strength and cell tower locations from Aeris. Shows dead zones, 3G fallback areas, and tower quality — a map that neither platform can produce alone.

### Tab 3: Fleet Map
All 50 vehicles with dual-ring markers showing health tier and radio technology. Click any vehicle for full connectivity details including IMSI, IMEI, carrier, cell ID, and data usage.

### Tab 4: Data Usage
SIM data consumption per vehicle with downloaded/uploaded split, balance percentage, and usage bars. Flags vehicles approaching their data cap.

### Tab 5: Network Diagnostics *(mirrors the Telenor IoT real-time diagnostics view)*
Fleet-wide session setup success rate, location update success rate, error counts, and active subscription count. Includes sub-tabs for breakdowns by **Carrier**, **Country**, and **Radio Technology** — each with per-group export.

### Tab 6: Errors & Export
Detailed error log with plain-English descriptions of each error type (AUTH_FAILURE, PDP_REJECT, ATTACH_REJECT, etc.). Three export buttons to download IMSI/IMEI lists as CSV for support escalation or Aeris portal lookup.

---

## The Data Sources

### From Geotab (already in the ecosystem)

| API | Data | Volume (demo DB) |
|-----|------|-------------------|
| StatusData | Cellular signal strength (dBm) | 47,096 records / 7 days |
| StatusData | Radio access technology | 47,063 records / 7 days |
| StatusData | GPS fix validity | 6,102 records / 7 days |
| StatusData | Device voltage | 23,613 records / 7 days |
| FaultData | Device unplugged, power removed, GPS antenna faults | 859 faults / 30 days |
| Device | Vehicle name, serial, type, position | 50 vehicles |
| DeviceStatusInfo | Communication status, driving state | Real-time |

### From Aeris IoT Accelerator (new integration — 7 APIs, 40 endpoints)

| API | What It Provides | Spec |
|-----|-----------------|------|
| [Subscription Location](api-specs/subscription-location.yaml) | Cell tower identity (MCC/MNC/LAC/CellID), carrier name, radio type | v1.0.2 |
| [Subscription Signalling Events](api-specs/subscription-signalling-events.yaml) | Low-level network events: ATTACH, DETACH, HANDOVER, PDP_ACTIVATE/DEACTIVATE, TAU | v2.1.4 |
| [Subscription Signalling Usages](api-specs/subscription-signalling-usages.yaml) | Data uploaded/downloaded per SIM per billing cycle | v2.0.9 |
| [Consumer Connectivity](api-specs/consumer-connectivity.yaml) | SIM data balance, plan details, low-volume alerts | v2.0.1 |
| [Incident Management](api-specs/incident-management.yaml) | Network trouble tickets with full lifecycle (NEW → ASSIGNED → RESOLVED) | v0.2.2 |
| [Org Signaling Aggregations](api-specs/org-signaling-aggregations.yaml) | Fleet-wide traffic stats by carrier, country, APN | v1.0.0 |
| [Device Reconnect](api-specs/subscription-device-reconnect.yaml) | Remote SIM re-attach to force network re-registration | v1.0.2 |

The OpenAPI specification files in `api-specs/` are the actual API contracts from the Aeris IoT Accelerator platform. Every field in the Add-In's data model maps to a real API response field.

---

## About the Demo Data

This Add-In uses **mock data** for the contest demonstration. Here's why, and what that means:

**The Geotab side** runs against a standard Geotab demo database with 50 simulated vehicles. The demo database provides continuously streaming GPS, diagnostics, and fault data — it's the same sandbox Geotab provides to all developers.

**The Aeris side** uses realistic mock data generated from the actual OpenAPI specifications. The mock data:

Mock data is used because using a live API carries a significant amount of risk for demo purposes. I uploaded .yaml files for your review, and have made Mock scenarios to tie into the demo environment.

- Maps each of the 50 Geotab demo vehicles to an Aeris SIM subscription (by IMSI)
- Uses real carrier names, MCC/MNC codes, and cell tower structures from the Iberian Peninsula (where the demo fleet operates)
- Simulates realistic failure scenarios: 5 critical vehicles with weak signal on 2G fallback, 5 warning vehicles with intermittent 3G, 5 minor issues, and 35 healthy
- Generates network signaling events (ATTACH, DETACH, PDP_ACTIVATE, HANDOVER) with realistic data volumes and timing
- Creates incident tickets with proper status workflows matching the Aeris API schema
- Produces error logs with real error codes (AUTH_FAILURE, PDP_REJECT, ATTACH_REJECT, etc.)

**In production**, the Add-In would make live API calls to both Geotab and Aeris. The mock data faithfully represents the data structures, field names, and value ranges from the real APIs — including the kinds of connectivity failures that actual fleets experience.

The mock data generation script is included at [`mock-data/generate_mock_data.py`](mock-data/generate_mock_data.py) for full transparency.

---

## How It Ties Together

The key insight is that every Geotab GO device contains a cellular modem with a SIM card. That SIM has an IMSI (International Mobile Subscriber Identity). This is the link:

| Geotab Side | Link | Aeris Side |
|------------|------|------------|
| Device ID + Serial | ↔ IMSI / ICC | Subscription ID |
| GPS position (lat/lon) | ↔ CGI lookup | Cell tower (MCC/MNC/LAC/CellID) |
| Signal strength (dBm) | ↔ radio type | LTE / 3G / 2G technology |
| Device faults (unplug/restart) | ↔ events | Network DETACH/ATTACH events |
| Communication status | ↔ incidents | Trouble tickets + root cause |

By correlating these two perspectives, the Add-In can answer questions that neither platform can answer alone:

> *"Vehicle Demo-31 has weak signal (37 dBm) because it's stuck on a 2G GSM tower (Orange ES #64084) in an area with LTE coverage available — likely a modem issue, not a coverage gap. It has had 25 connection drops in 24 hours, 2 active incidents, and its SIM has consumed 1,296 MB of its 2 GB plan due to excessive retransmissions."*

That's a root-cause diagnosis. Geotab alone would say "37 dBm." Aeris alone would say "SIM is on cell #64084." Only the combination tells the whole story.

---


### Add-In Configuration
```json
{
  "name": "Fleet Connectivity Intelligence",
  "supportEmail": "support@example.com",
  "version": "3.0.1",
  "items": [
    {
      "url": "fleet_connectivity_v3.html",
      "path": "ActivityLink/",
      "menuName": { "en": "Connectivity Intelligence" }
    }
  ],
  "isSigned": false
}
```

---

## Technical Details

- **Single-file architecture**: Self-contained HTML with embedded CSS, JavaScript, and mock data (~123 KB)
- **Zenith Design System**: Styled using Geotab's official design tokens — Roboto/Roboto Mono fonts, Geotab color palette, component patterns
- **CSS class prefixing**: All classes prefixed with `fci-` per Geotab's Add-In CSS naming requirements
- **MyGeotab lifecycle**: Implements `initialize` (with required `callback()`), `focus`, and `blur` methods via `window.geotab.addin.fleetConnectivity`
- **Standalone fallback**: Detects whether MyGeotab API is available; falls back to standalone mode for demo/testing
- **Mapping**: Leaflet.js with OpenStreetMap tiles
- **No build tools required**: No npm, no webpack, no framework — just one HTML file
- **Export**: Client-side CSV generation with `Blob` and `URL.createObjectURL`

---

## Repository Structure

```
fleet-connectivity-intelligence/
├── fleet_connectivity_v3.html              # The Add-In (install this)
├── addin_config_v3.json                    # MyGeotab configuration
├── architecture.svg                        # Data flow diagram
├── README.md                               # This file
├── LICENSE                                 # Apache 2.0
├── api-specs/                              # Aeris IoT Accelerator OpenAPI specs
│   ├── consumer-connectivity.yaml          #   Data balance & plans (18 endpoints)
│   ├── incident-management.yaml            #   Trouble ticket management (15 endpoints)
│   ├── org-signaling-aggregations.yaml     #   Fleet-wide traffic aggregations (1 endpoint)
│   ├── subscription-signalling-usages.yaml #   Data usage reports (2 endpoints)
│   ├── subscription-signalling-events.yaml #   Network signalling events (2 endpoints)
│   ├── subscription-location.yaml          #   Cell tower identity (1 endpoint)
│   └── subscription-device-reconnect.yaml  #   Remote SIM reconnect (1 endpoint)
└── mock-data/
    └── generate_mock_data.py               # Mock data generation script
```

---

## What's Next (Production Roadmap)

This contest submission demonstrates the concept with mock data. A production version would add:

1. **Live Aeris API integration** — Replace mock data with real-time calls to all 7 APIs
2. **Remote Reconnect button** — Use the Device Reconnect API to fix stuck SIMs directly from MyGeotab
3. **Automated alerting** — Create Geotab Rules that trigger when connectivity health drops below threshold
4. **Historical trending** — Track signal strength, error rates, and data usage over time
5. **Multi-fleet support** — Scale to multiple Geotab databases with carrier-level aggregations
6. **Geotab Marketplace listing** — Package for distribution to all 100,000+ Geotab customers

---

## Built With

- **AI-Assisted Development**: Claude (Anthropic) for code generation, architecture design, and documentation
- **Geotab API**: Device, StatusData, FaultData, DeviceStatusInfo
- **Aeris IoT Accelerator**: 7 OpenAPI-documented REST APIs (40 endpoints total)
- **Geotab Zenith Design System**: Official component library tokens and patterns
- **Leaflet.js**: Interactive mapping
- **Geotab Vibe Coding Starter Kit**: [github.com/fhoffa/geotab-vibe-guide](https://github.com/fhoffa/geotab-vibe-guide)

---

## About

**Tim Batzel** — Cellular connectivity supplier via Telenor IoT, serving Geotab and their fleet customers on the Aeris IoT Accelerator platform.

Built for the [Geotab Vibe Coding Challenge 2026](https://luma.com/h6ldbaxp) ($25,000 in prizes, Feb 12 – Mar 2, 2026).

*This Add-In doesn't compete with anything in MyGeotab — it fills a blind spot that no existing page addresses.*

