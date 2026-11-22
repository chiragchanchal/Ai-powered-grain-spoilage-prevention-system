/**
 * AgroGuard Product Visualizers (UI-UX Pro Max Specification)
 * - Structural corrugated steel silo cross-section with real crop fill & probe lances
 * - High-legibility threshold meters with safety baselines
 * - Audio alarm synthesizer
 */

const Visualizers = {
  /**
   * Generates a realistic structural cross-section of a corrugated steel grain silo.
   */
  createSiloCrossSectionSVG: function(fillPct, grainType, riskTier) {
    const clampedPct = Math.max(10, Math.min(100, fillPct));
    const maxHeight = 88;
    const fillHeight = (clampedPct / 100) * maxHeight;
    const grainY = 108 - fillHeight;

    let grainColor = "#D97706"; // Amber Wheat
    if (grainType.toLowerCase().includes("paddy")) grainColor = "#B45309";
    if (grainType.toLowerCase().includes("maize")) grainColor = "#EA580C";
    if (grainType.toLowerCase().includes("pulses")) grainColor = "#A16207";
    if (grainType.toLowerCase().includes("mustard")) grainColor = "#CA8A04";
    if (grainType.toLowerCase().includes("soybean")) grainColor = "#D97706";

    let probeColor = "#10B981"; // Safe probe
    if (riskTier === "HIGH") probeColor = "#EF4444";
    else if (riskTier === "MEDIUM") probeColor = "#F59E0B";

    return `
      <div class="relative w-20 h-32 flex items-center justify-center select-none">
        <svg class="w-full h-full" viewBox="0 0 80 125" fill="none" xmlns="http://www.w3.org/2000/svg">
          <!-- Silo Conical Roof & Top Exhaust Vent -->
          <rect x="36" y="4" width="8" height="6" rx="1" fill="#475569" stroke="#334155" stroke-width="1" />
          <path d="M 12 24 L 40 10 L 68 24 Z" fill="#334155" stroke="#475569" stroke-width="1.2" />
          
          <!-- Corrugated Steel Cylinder Body -->
          <rect x="12" y="24" width="56" height="84" rx="1" fill="#1E293B" stroke="#475569" stroke-width="1.2" />
          
          <!-- Grain Mass Fill -->
          <rect x="14" y="${grainY}" width="52" height="${fillHeight}" rx="1" fill="${grainColor}" opacity="0.92" />
          
          <!-- Horizontal Corrugation Ribs -->
          <line x1="12" y1="36" x2="68" y2="36" stroke="#475569" stroke-width="1" stroke-opacity="0.6" />
          <line x1="12" y1="48" x2="68" y2="48" stroke="#475569" stroke-width="1" stroke-opacity="0.6" />
          <line x1="12" y1="60" x2="68" y2="60" stroke="#475569" stroke-width="1" stroke-opacity="0.6" />
          <line x1="12" y1="72" x2="68" y2="72" stroke="#475569" stroke-width="1" stroke-opacity="0.6" />
          <line x1="12" y1="84" x2="68" y2="84" stroke="#475569" stroke-width="1" stroke-opacity="0.6" />
          <line x1="12" y1="96" x2="68" y2="96" stroke="#475569" stroke-width="1" stroke-opacity="0.6" />

          <!-- Center Thermal Probe Lance Line -->
          <line x1="40" y1="12" x2="40" y2="104" stroke="${probeColor}" stroke-width="1.5" stroke-dasharray="2,2" />
          <circle cx="40" cy="${Math.min(100, grainY + fillHeight * 0.55)}" r="3.5" fill="${probeColor}" />
          ${riskTier === 'HIGH' ? `<circle cx="40" cy="${Math.min(100, grainY + fillHeight * 0.55)}" r="6" stroke="${probeColor}" stroke-width="1" opacity="0.75" />` : ''}

          <!-- Hopper Bottom / Legs -->
          <path d="M 16 108 L 28 120 L 52 120 L 64 108 Z" fill="#1E293B" stroke="#475569" stroke-width="1" />
          <line x1="24" y1="120" x2="20" y2="124" stroke="#475569" stroke-width="2" />
          <line x1="56" y1="120" x2="60" y2="124" stroke="#475569" stroke-width="2" />
        </svg>
        <span class="absolute -bottom-1 font-numeric text-[10px] font-semibold text-slate-300 bg-slate-900 px-1 py-0.2 rounded border border-slate-700">
          ${clampedPct}%
        </span>
      </div>
    `;
  },

  /**
   * Generates a clean, readable metric cell with threshold context.
   */
  createMetricMeter: function(label, value, unit, safeThreshold, min, max, isHighDangerous = true) {
    const clampedVal = Math.max(min, Math.min(max, value));
    const pct = ((clampedVal - min) / (max - min)) * 100;
    const thresholdPct = ((safeThreshold - min) / (max - min)) * 100;

    const isExceeded = isHighDangerous ? value > safeThreshold : value < safeThreshold;
    let barColor = isExceeded ? (Math.abs(value - safeThreshold) > 1.2 ? "bg-rose-500" : "bg-amber-500") : "bg-emerald-500";
    let textColor = isExceeded ? (Math.abs(value - safeThreshold) > 1.2 ? "text-rose-400" : "text-amber-400") : "text-slate-100";

    const delta = Math.abs(value - safeThreshold).toFixed(1);
    const contextNote = isExceeded ? `${delta}${unit} over limit` : `${delta}${unit} safe buffer`;

    return `
      <div class="flex flex-col justify-between p-2.5 rounded-lg bg-[#0B111E] border border-[#1C283F]">
        <div class="flex items-center justify-between text-xs text-slate-400">
          <span>${label}</span>
          <span class="text-[10px] font-numeric text-slate-500">limit: ${safeThreshold}${unit}</span>
        </div>
        <div class="flex items-baseline gap-1 my-1">
          <span class="text-lg font-bold font-numeric ${textColor}">${typeof value === 'number' ? value.toFixed(1) : value}</span>
          <span class="text-xs text-slate-400">${unit}</span>
        </div>
        <div class="relative h-1.5 w-full bg-slate-800 rounded-full overflow-hidden my-1">
          <div class="h-full rounded-full transition-all duration-500 ${barColor}" style="width: ${Math.min(100, Math.max(5, pct))}%"></div>
          <div class="absolute top-0 bottom-0 w-0.5 bg-slate-400/80 z-10" style="left: ${thresholdPct}%" title="Safe Limit: ${safeThreshold}${unit}"></div>
        </div>
        <span class="text-[10px] text-slate-400 font-medium">${contextNote}</span>
      </div>
    `;
  },

  // Audio Beeper for High Risk Alerts
  audioContext: null,
  isMuted: false,

  playAlertSound: function() {
    if (this.isMuted) return;
    try {
      if (!this.audioContext) {
        this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
      }
      if (this.audioContext.state === "suspended") {
        this.audioContext.resume();
      }
      const osc = this.audioContext.createOscillator();
      const gain = this.audioContext.createGain();
      osc.type = "sine";
      osc.frequency.setValueAtTime(750, this.audioContext.currentTime);
      osc.frequency.exponentialRampToValueAtTime(400, this.audioContext.currentTime + 0.25);
      gain.gain.setValueAtTime(0.15, this.audioContext.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.01, this.audioContext.currentTime + 0.25);
      osc.connect(gain);
      gain.connect(this.audioContext.destination);
      osc.start();
      osc.stop(this.audioContext.currentTime + 0.3);
    } catch (e) {
      console.warn("Audio suppressed:", e);
    }
  }
};
