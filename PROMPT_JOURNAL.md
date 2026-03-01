# Fleet Connectivity Intelligence — Vibe Coding Prompt Journal

> **Author:** Tim Batzel  
> **AI Tools:** Claude (Anthropic), Geotab Add-In Architect Gem (Google Gemini), Google Firebase Studio  
> **Contest:** Geotab Vibe Coding Challenge 2026  
> **Build Period:** February 27 – March 1, 2026

This document captures the key prompts and decisions used to build Fleet Connectivity Intelligence. The entire project was built through conversational AI — no manual coding. Three AI tools were used at different stages, each for what it does best.

---

## Phase 1: Discovery & Architecture (Claude)

**The starting prompt:**
> I have a Geotab demo database ready. Connect to the API and show me what data is available. I want to build a MyGeotab Add-In for the vibe coding contest. I am a connectivity supplier for Geotab — anything on that end we can do?

Claude connected to the Geotab API, pulled device, trip, and diagnostic data from my 50-vehicle demo fleet, and identified the gap: **Geotab shows signal strength but can't explain *why* connectivity is bad.** That insight became the entire project.

**Key decision — mock data strategy:**
> I don't want to use live API credentials. I have real data I can't expose. So let's feed you the real API specifications, generate realistic mock data, and map it to the existing demo vehicles.

I uploaded 7 Aeris IoT Accelerator API specification files (.yaml) one by one. Claude parsed them and designed mock data with health tier distributions: 60% healthy, 10% minor, 10% warning, 10% critical — realistic enough to demo, safe enough to publish.

---

## Phase 2: Dashboard Build (Claude) → v1 through v3

**Feature prioritization:**
> Ranked: 1. Problem vehicle alerts (connectivity issues), 2. Network coverage heatmap, 3. Live fleet map with signal/radio overlay, 4. SIM data usage & balance per vehicle

Claude built the first version with 4 tabs, Leaflet.js maps, and color-coded vehicle markers. Then I pushed it further:

> How do I make this have the same look as the Geotab ecosystem?

Claude applied the Zenith Design System — Geotab's official CSS tokens, dark branded header, professional typography. Then I requested more depth:

> Don't need SMS. Enhance errors for further review. Add a fleet breakdown tab. Would love a way to export IMSI/IMEI by carrier or troubled operator too.

This added two more tabs (Network Diagnostics and Errors & Export with CSV download), bringing the dashboard to 6 tabs for v3.

---

## Phase 3: MyGeotab Deployment (Claude)

The hardest part of the project. Getting a self-contained HTML file to run inside MyGeotab's Add-In framework required debugging Content Security Policy restrictions, `geotab.addin` lifecycle registration patterns, and the Files upload method.

> Still not working. Here is the JSON code. What can we do? I feel we are going in circles. Do you need to look at the Geotab GitHub and figure this out?

Claude researched the Geotab SDK documentation mid-conversation, found the correct `geotab.addin['{name}-{filename}']` registration pattern, and rebuilt the file as fully self-contained (inline CSS, no external dependencies except CDN libraries that MyGeotab allows). After multiple iterations, the dashboard loaded cleanly inside MyGeotab.

---

## Phase 4: GitHub & Documentation (Claude)

> How do I address what I have done with the .yaml files? I need to show my work.

Claude organized the 10 uploaded YAML files into 7 unique deduplicated API specs, created the GitHub repository structure, wrote the README, and generated a 400-line Python mock data script (`generate_mock_data.py`) documenting exactly how the demo data was created.

---

## Phase 5: Connectivity Assistant Chatbot (Google Gem → Claude) → v4

**Strategy prompt:**
> I want to use Google tools for the Best Use of Google Tools prize. Let's use the Geotab Add-In Architect Gem — a chatbot where you can ask about network issues by vehicle, country, operator, IMSI, or IMEI.

Claude wrote a detailed prompt for the Gem, which I pasted into the [Geotab Add-In Architect Gem](https://gemini.google.com/gem/1Y6IvbBj4ALgS9G3SgGodepM2dfArInrO). The Gem generated a MyGeotab Add-In config with embedded HTML.

I brought the output back to Claude, who extracted the HTML, improved the search logic (flexible vehicle name matching, IMSI/IMEI lookup, fleet summary, error breakdown, help command), and integrated it as a 7th tab in the main dashboard. This became v4.

---

## Phase 6: 3D Command Center (Firebase Studio → Claude) → v5

**The vision:**
> I want something visually impressive and unique for the contest that shows connectivity in 3D.

I used [Google Firebase Studio](https://firebase.studio) (powered by Gemini 2.5 Pro) to prototype a 3D map concept using Mapbox GL JS. Firebase generated `fci-command-center.js` and `fci-command-center.css` — a dark-themed globe with 3D extruded vehicle columns, atmospheric fog, and interactive popups.

The prototype looked great in isolation but couldn't run inside MyGeotab: it used separate files, generated random American data instead of my fleet, and had an empty MOCK data object. I brought the concept back to Claude:

> I need your help. Firebase made a 3D map but I can't get anything to load in the Geotab database. The data is empty.

Claude took the working v4 file and rebuilt the 3D Command Center inline — using my real 50-vehicle dataset in Spain/Portugal, proper Mapbox v3.4.0 (v2.8.2 didn't support globe projection), and all self-contained for MyGeotab's Files upload method.

> The map starts showing the whole globe. Any options for a user to quickly get to critical areas?

Claude added quick-fly navigation buttons for each cluster: Critical (Vigo), Warning (Valencia), Minor (Galicia), Healthy (NOS Portugal). The map now opens centered on Spain/Portugal with auto-rotation, and users can jump to problem areas in one click. This became v5 — 8 tabs total.

---

## Summary

| Phase | AI Tool | What Was Built |
|-------|---------|---------------|
| Discovery & Architecture | Claude | API exploration, connectivity gap identification, mock data strategy |
| Dashboard v1–v3 | Claude | 6-tab dashboard with maps, alerts, diagnostics, CSV export |
| MyGeotab Deployment | Claude | Self-contained HTML, lifecycle debugging, Files upload method |
| GitHub & Docs | Claude | Repo structure, README, API specs, mock data generator |
| Chatbot (v4) | Google Gem → Claude | Connectivity Assistant with natural language fleet queries |
| 3D Command Center (v5) | Firebase Studio → Claude | Interactive 3D globe with fly-to navigation and signal visualization |

| Metric | Value |
|--------|-------|
| AI tools used | 3 (Claude, Google Gem, Firebase Studio) |
| Total sessions with Claude | 12 |
| Lines of code written manually | 0 |
| Total HTML generated | ~135 KB (v5 main file) |
| API specs documented | 7 Aeris APIs, 40+ endpoints |
| Mock vehicles | 50 with realistic health distributions |
| Tabs in final Add-In | 8 |
| Build time | ~3 days (Feb 27 – Mar 1) |

---

## How Each AI Tool Was Used

**Claude (Anthropic)** — The primary builder. Every line of HTML, CSS, and JavaScript was generated through conversation. Claude also handled API exploration, Geotab SDK research, deployment debugging, documentation, and integration of outputs from the other two tools.

**Geotab Add-In Architect Gem (Google Gemini)** — Generated the initial chatbot Add-In from a natural language description. The output was a MyGeotab-compatible config with embedded HTML that Claude then refined and integrated.

**Google Firebase Studio (Gemini 2.5 Pro)** — Prototyped the 3D Command Center concept. Generated the Mapbox GL JS code, dark theme styling, and interactive vehicle popup architecture. The concept was then rebuilt by Claude to work inline with the real fleet data.

The workflow was: **specialized tools for ideation and prototyping → Claude for production integration.** Each tool contributed its strength to the final product.
