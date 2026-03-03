/**
 * fci-command-center.js
 * 3D Fleet Intelligence Experience for MyGeotab
 *
 * Author: Gemini
 * Version: 1.0.0
 *
 * CRITICAL:
 * - Lazy loaded via fleet_connectivity_v5.html
 * - Mounts into <div id="panel-command-center"></div>
 * - Uses Mapbox GL JS for 3D rendering
 * - Zenith dark mode theme
 */

const fciCommandCenter = (function() {

    // --- PRIVATEVARS ---
    let map;
    let isInitialized = false;
    let mapboxToken = 'YOUR_MAPBOX_ACCESS_TOKEN'; // <<< IMPORTANT: REPLACE WITH YOUR TOKEN LOCALLY BEFORE UPLOAD

    // --- INITIALIZATION ---
    function init() {
        if (isInitialized) {
            return;
        }
        console.log("FCI Command Center: Initializing...");
        if (mapboxToken === 'YOUR_MAPBOX_ACCESS_TOKEN' || mapboxToken === '') {
            console.error("FCI Command Center: Mapbox token not set. Please replace 'YOUR_MAPBOX_ACCESS_TOKEN' in fci-command-center.js");
            document.getElementById('panel-command-center').innerHTML = '<div class="fci-config-warning"><h3>Action Required</h3><p>A Mapbox token has not been set. The 3D Command Center cannot be displayed.</p><p>Please obtain a token from mapbox.com and add it to the <code>fci-command-center.js</code> file before uploading.</p></div>';
            return;
        }

        lazyLoadMapbox().then(() => {
            setupMap();
            isInitialized = true;
        });
    }

    // --- LAZY LOAD MAPBOX ---
    function lazyLoadMapbox() {
        return new Promise((resolve, reject) => {
            if (window.mapboxgl) {
                resolve();
                return;
            }
            const script = document.createElement('script');
            script.src = 'https://api.mapbox.com/mapbox-gl-js/v2.8.2/mapbox-gl.js';
            script.onload = resolve;
            script.onerror = reject;
            document.head.appendChild(script);

            const link = document.createElement('link');
            link.href = 'https://api.mapbox.com/mapbox-gl-js/v2.8.2/mapbox-gl.css';
            link.rel = 'stylesheet';
            document.head.appendChild(link);
        });
    }

    // --- MAP SETUP ---
    function setupMap() {
        mapboxgl.accessToken = mapboxToken;
        map = new mapboxgl.Map({
            container: 'panel-command-center',
            style: 'mapbox://styles/mapbox/dark-v10',
            center: [-98.5795, 39.8283],
            zoom: 3.5,
            pitch: 65,
            bearing: -17.6,
            antialias: true,
            projection: 'globe'
        });

        map.on('load', () => {
            console.log("FCI Command Center: Map loaded.");
            setupScene();
            loadVehicleData();
            setupInteractions();
        });
    }

    // --- 3D SCENE & ATMOSPHERE ---
    function setupScene() {
        map.setFog({
            'range': [-1, 10],
            'color': 'white',
            'horizon-blend': 0.05
        });

        map.addLayer({
            'id': '3d-buildings',
            'source': 'composite',
            'source-layer': 'building',
            'filter': ['==', 'extrude', 'true'],
            'type': 'fill-extrusion',
            'minzoom': 15,
            'paint': {
                'fill-extrusion-color': '#aaa',
                'fill-extrusion-height': [
                    "interpolate", ["linear"], ["get", "height"],
                    0, 0,
                    250, 250
                ],
                'fill-extrusion-base': [
                    "interpolate", ["linear"], ["get", "min_height"],
                    0, 0,
                    250, 250
                ],
                'fill-extrusion-opacity': 0.6
            }
        });
    }
    
    // --- DATA HANDLING ---
    function loadVehicleData() {
        // In a real app, you'd fetch data. Here we generate it.
        const data = generateRandomVehicleData(); 

        map.addSource('vehicles', {
            'type': 'geojson',
            'data': data
        });

        map.addLayer({
            'id': 'vehicle-extrusions',
            'type': 'fill-extrusion',
            'source': 'vehicles',
            'paint': {
                'fill-extrusion-color': [
                    'match',
                    ['get', 'healthTier'],
                    'critical', '#C51A11',
                    'warning', '#B8860B',
                    'minor', '#0078D3',
                    'healthy', '#2B6436',
                    /* default */ '#2B6436'
                ],
                'fill-extrusion-height': [
                    'interpolate', ['linear'], ['get', 'sig'],
                    0, 100, // min signal -> 100m height
                    100, 5000 // max signal -> 5000m height
                ],
                'fill-extrusion-base': 0,
                'fill-extrusion-opacity': 0.9
            }
        });
    }

    // --- INTERACTIONS ---
    function setupInteractions() {
        let popup = new mapboxgl.Popup({
            closeButton: false,
            closeOnClick: false
        });

        map.on('mouseenter', 'vehicle-extrusions', (e) => {
            map.getCanvas().style.cursor = 'pointer';
            const coordinates = e.features[0].geometry.coordinates.slice();
            const properties = e.features[0].properties;
            const tooltipContent = `<strong>${properties.name}</strong><br>Signal: ${properties.sig} dBm`;
            
            popup.setLngLat(coordinates).setHTML(tooltipContent).addTo(map);
        });

        map.on('mouseleave', 'vehicle-extrusions', () => {
            map.getCanvas().style.cursor = '';
            popup.remove();
        });

        map.on('click', 'vehicle-extrusions', (e) => {
            const feature = e.features[0];
            map.flyTo({
                center: feature.geometry.coordinates,
                zoom: 15,
                pitch: 60,
                speed: 0.7
            });
            showVehicleDetailPanel(feature.properties);
        });
    }
    
    function showVehicleDetailPanel(props) {
        const existingPanel = document.querySelector('.fci-detail-panel');
        if(existingPanel) existingPanel.remove();

        const panel = document.createElement('div');
        panel.className = 'fci-detail-panel';
        panel.innerHTML = `
            <div class="fci-panel-header">
                <h3>${props.name}</h3>
                <button class="fci-close-btn">&times;</button>
            </div>
            <div class="fci-panel-body">
                <p><strong>IMSI:</strong> <span>${props.imsi}</span></p>
                <p><strong>IMEI:</strong> <span>${props.imei}</span></p>
                <p><strong>Carrier:</strong> <span>${props.carrier}</span></p>
                <p><strong>Signal:</strong> <span>${props.sig} dBm</span></p>
                <p><strong>Health:</strong> <span>${props.healthTier}</span></p>
                <p><strong>Radio:</strong> <span>${props.rat}</span></p>
                <p><strong>Country:</strong> <span>${props.country}</span></p>
            </div>
        `;
        document.getElementById('panel-command-center').appendChild(panel);
        
        panel.querySelector('.fci-close-btn').onclick = () => {
            panel.remove();
        }
    }

    // This is a placeholder for actual vehicle data
    function generateRandomVehicleData() {
        const features = [];
        const healthTiers = ['healthy', 'minor', 'warning', 'critical'];
        const rats = ['LTE', 'WCDMA', 'GSM'];
        const carriers = ['AT&T', 'Verizon', 'T-Mobile', 'Rogers'];
        const countries = ['USA', 'Canada', 'Mexico'];

        for (let i = 0; i < 50; i++) {
            features.push({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [ -125 + Math.random() * 60, 25 + Math.random() * 25 ]
                },
                "properties": {
                    "id": `veh_${i}`,
                    "name": `Vehicle ${1000 + i}`,
                    "imsi": `310410123456${i.toString().padStart(3, '0')}`,
                    "imei": `358567031234${i.toString().padStart(3, '0')}`,
                    "sig": Math.floor(Math.random() * 101),
                    "healthTier": healthTiers[Math.floor(Math.random() * healthTiers.length)],
                    "rat": rats[Math.floor(Math.random() * rats.length)],
                    "carrier": carriers[Math.floor(Math.random() * carriers.length)],
                    "country": countries[Math.floor(Math.random() * countries.length)],
                }
            });
        }
        return { "type": "FeatureCollection", "features": features };
    }

    // --- CLEANUP ---
    function destroy() {
        if (!isInitialized) {
            return;
        }
        console.log("FCI Command Center: Destroying...");
        if (map) {
            map.remove();
            map = null;
        }
        isInitialized = false;
        
        // Clear the panel content
        document.getElementById('panel-command-center').innerHTML = '';
    }


    // --- PUBLIC INTERFACE ---
    return {
        initialize: init,
        destroy: destroy,
        isLoaded: () => isInitialized
    };

})();
