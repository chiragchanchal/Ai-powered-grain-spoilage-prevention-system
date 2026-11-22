# AgroGuard UI/UX Master Specification (UI-UX Pro Max Blueprint)

> **Design Directive**: High-Craft Agricultural Telemetry & Grain Storage SCADA Interface.  
> **Anti-AI-Slop Guarantee**: Grounded materials, physical corrugated steel textures, authentic crop color tokens, clear visual hierarchy, and zero generic purple gradient cards.

---

## 1. Product Classification & Intent
- **Domain**: Agricultural IoT Telemetry, Bulk Storage SCADA, Mandi Quality Control
- **Primary User**: Grain warehouse managers, mandi quality inspectors, cooperative storage heads, smallholder farmers
- **Primary Job to Be Done**: Instantly answer: *"Are my grain bins safe right now, and should I turn on ventilation fans or keep intake louvers sealed against outside damp air?"*
- **Aesthetic Stance**: **Modern Industrial Bento & Tactile Agro-Engineering**. Combines clean, high-density telemetry data with physical cross-sections of storage bins.

---

## 2. Anti-AI-Slop Enforcements
1. **No Generic Purple/Cyan/Magenta Washes**: The canvas is an authentic deep obsidian earth (`#090D15`) paired with slate-zinc surfaces (`#101726`), inspired by modern industrial SCADA tools (like Grafana, Samsara, and Linear).
2. **No All-Caps Tracked Eyebrows**: Standardized on humanized sentence case (`Stack temperature`, `Grain moisture margin`) with high-contrast labels.
3. **No Cookie-Cutter Card Grids**: Uses an intentional Bento-grid rhythm with varying card weights based on operational urgency.
4. **No Emoji as UI Icons**: Standardized on crisp FontAwesome 6 SVG vector icons with explicit accessibility labels.
5. **No Jargon Soup**: Replaces raw database names ("Cassandra Partition CQL Rolling Window") with tangible agricultural concepts ("Storage Units", "Aeration Command", "24-Hour Thermal Drift").
6. **Physical Tangibility**: Silos are rendered as corrugated steel cylinders with conical roof exhaust vents, conical hoppers, crop-specific grain colors (amber wheat, golden paddy, orange maize), and center thermal probe lances.

---

## 3. Design Tokens (CSS Variables)

```css
:root {
  /* Canvas & Structural Surfaces */
  --bg-canvas: #090D15;
  --bg-surface: #101726;
  --bg-surface-elevated: #152033;
  --bg-surface-subtle: #0B111E;
  --border-subtle: #1C283F;
  --border-strong: #2A3B5C;
  --border-highlight: #3B527E;

  /* Typography */
  --font-ui: 'Plus Jakarta Sans', -apple-system, sans-serif;
  --font-mono: 'JetBrains Mono', monospace;
  --text-primary: #F8FAFC;
  --text-secondary: #94A3B8;
  --text-muted: #64748B;

  /* Agricultural & Industrial Accents */
  --accent-grain: #F59E0B;      /* Warm Harvest Wheat */
  --accent-paddy: #D97706;      /* Golden Basmati Paddy */
  --accent-maize: #EA580C;      /* Sunlit Maize */
  --accent-air: #0EA5E9;        /* Atmospheric Cyan / Dew Point */
  --accent-leaf: #10B981;       /* Safe / Normal Leaf Green */
  --accent-warning: #F59E0B;    /* Moisture Creep Advisory */
  --accent-hazard: #EF4444;     /* Critical Hotspot / Mold Alert */
}
```

---

## 4. Layout Architecture (Bento-SCADA Grid)

1. **Header Masthead**:
   - Product Brand (`AgroGuard`), Live Telemetry Pill, Facility Switcher (`Gurugram Mandi Godown A`), Language Toggle (`EN / हिन्दी`), and Quick Action Buttons (`Farm Profile`, `Add Silo`, `Simulate`, `Inspection Sheet`).
2. **Hero Bento 1: Ventilation & Aeration Command**:
   - High-contrast decision banner displaying immediate ventilation guidance (e.g. *"Safe to Run Aeration Fans Tonight"* vs *"Keep Outside Intake Vents Sealed Against Rain"*).
   - Real-time OpenWeatherMap ambient temperature, humidity, and 48-hour precipitation forecast strip.
3. **Hero Bento 2: Silo Fleet Grid**:
   - Physical structural cross-sections with grain fill percentage and center probe lances.
   - High-contrast threshold meters for Moisture %, Stack Temp °C, and Interstitial RH %.
   - Derived microclimate indicators: Dew Point, Equilibrium Moisture Content (EMC), and Thermal Drift Rate ($dT/dt$).
   - Quick Farmer Actions: `Log Handheld Reading`, `Edit Unit`, `Delete Unit`.
4. **Deep Dive Bento 3: 24-Hour Telemetry Microclimate Drift (Chart.js)**:
   - Line chart with custom tooltips tracking rate of temperature change (hotspot early detection) and interstitial moisture.
5. **Deep Dive Bento 4: Regional Climate Knowledge Graph**:
   - Interactive Canvas node visualizer exploring multi-hop regional disease and weather hazards.
6. **Farmer Toolkit Bento 5: Interactive What-If Calculator**:
   - Real-time sliders allowing farmers to test custom microclimate conditions with the trained dual-model AI ensemble.
7. **Modals & Drawers**:
   - Add Silo, Log Manual Reading, Edit Silo, Farm Profile Settings, Stress Scenarios, and Print-Ready Compliance Audit Sheet.
