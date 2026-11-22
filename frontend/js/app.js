/**
 * AgroGuard Product Controller with Farmer Customization
 * Allows farmers and operators to:
 * - Register custom storage units & bins
 * - Log manual moisture meter & temperature probe readings
 * - Customize farm & facility profiles
 * - Receive instant AI risk classification & ventilation guidance
 */

let state = {
  facilityData: null,
  weatherData: null,
  activeSiloId: "SILO_01",
  chartInstance: null,
  kgCanvasInstance: null,
  pollingInterval: null,
  isSoundMuted: false,
};

document.addEventListener("DOMContentLoaded", () => {
  initApp();
});

async function initApp() {
  setupEventListeners();
  await fetchWeatherData();
  await fetchSilosData();
  await initKnowledgeGraph();
  await loadHistoricalChart(state.activeSiloId);

  // Polling every 6 seconds for continuous telemetry
  state.pollingInterval = setInterval(async () => {
    await fetchSilosData();
  }, 6000);
}

function setupEventListeners() {
  // Language switcher
  document.getElementById("btnLangEn")?.addEventListener("click", () => {
    setLanguage("en");
    updateLanguageButtons("en");
    renderSiloCards();
    updateDecisionBanner();
  });
  document.getElementById("btnLangHi")?.addEventListener("click", () => {
    setLanguage("hi");
    updateLanguageButtons("hi");
    renderSiloCards();
    updateDecisionBanner();
  });

  // Sound toggle
  const soundBtn = document.getElementById("btnSoundToggle");
  soundBtn?.addEventListener("click", () => {
    Visualizers.isMuted = !Visualizers.isMuted;
    state.isSoundMuted = Visualizers.isMuted;
    soundBtn.innerHTML = state.isSoundMuted
      ? '<i class="fas fa-volume-mute text-rose-400"></i>'
      : '<i class="fas fa-volume-up text-emerald-400"></i>';
  });

  // Modal open/close controls
  document.getElementById("btnOpenAddSiloModal")?.addEventListener("click", openAddSiloModal);
  document.getElementById("btnCloseAddSiloModal")?.addEventListener("click", closeAddSiloModal);
  document.getElementById("btnCloseLogReadingModal")?.addEventListener("click", closeLogReadingModal);
  document.getElementById("btnCloseEditSiloModal")?.addEventListener("click", closeEditSiloModal);
  document.getElementById("btnOpenProfileModal")?.addEventListener("click", openProfileModal);
  document.getElementById("btnCloseProfileModal")?.addEventListener("click", closeProfileModal);

  document.getElementById("btnOpenSimModal")?.addEventListener("click", openSimModal);
  document.getElementById("btnCloseSimModal")?.addEventListener("click", closeSimModal);
  document.getElementById("btnOpenMetricsModal")?.addEventListener("click", openMetricsModal);
  document.getElementById("btnCloseMetricsModal")?.addEventListener("click", closeMetricsModal);
  document.getElementById("btnOpenReportModal")?.addEventListener("click", openReportModal);
  document.getElementById("btnCloseReportModal")?.addEventListener("click", closeReportModal);
  document.getElementById("btnPrintReport")?.addEventListener("click", () => window.print());

  // Farmer Form Submissions
  document.getElementById("addSiloForm")?.addEventListener("submit", handleAddSiloSubmit);
  document.getElementById("logReadingForm")?.addEventListener("submit", handleLogReadingSubmit);
  document.getElementById("editSiloForm")?.addEventListener("submit", handleEditSiloSubmit);
  document.getElementById("farmProfileForm")?.addEventListener("submit", handleFarmProfileSubmit);

  // Scenario Triggers
  document.querySelectorAll("[data-scenario]").forEach(btn => {
    btn.addEventListener("click", async () => {
      const scenarioKey = btn.getAttribute("data-scenario");
      await triggerSimulation(scenarioKey);
    });
  });

  document.getElementById("btnResetSim")?.addEventListener("click", async () => {
    await resetSimulation();
  });

  // What-If Form
  document.getElementById("whatIfForm")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    await runWhatIfPrediction();
  });
}

function updateLanguageButtons(lang) {
  const enBtn = document.getElementById("btnLangEn");
  const hiBtn = document.getElementById("btnLangHi");
  if (lang === "en") {
    enBtn?.classList.add("bg-emerald-700", "text-white");
    enBtn?.classList.remove("text-slate-400");
    hiBtn?.classList.remove("bg-emerald-700", "text-white");
    hiBtn?.classList.add("text-slate-400");
  } else {
    hiBtn?.classList.add("bg-emerald-700", "text-white");
    hiBtn?.classList.remove("text-slate-400");
    enBtn?.classList.remove("bg-emerald-700", "text-white");
    enBtn?.classList.add("text-slate-400");
  }
}

async function fetchWeatherData() {
  try {
    const res = await fetch("/api/weather/current");
    const data = await res.json();
    state.weatherData = data;
    renderWeather(data);
  } catch (e) {
    console.error("Weather fetch failed:", e);
  }
}

async function fetchSilosData() {
  try {
    const res = await fetch("/api/silos");
    const data = await res.json();
    state.facilityData = data;
    renderSummaryStats(data);
    renderSiloCards();
    updateDecisionBanner();

    if (data.high_risk_count > 0) {
      Visualizers.playAlertSound();
    }
  } catch (e) {
    console.error("Silos fetch failed:", e);
  }
}

function renderSummaryStats(data) {
  document.getElementById("statSafeCount").innerText = data.low_risk_count || 0;
  document.getElementById("statWarningCount").innerText = data.medium_risk_count || 0;
  document.getElementById("statCriticalCount").innerText = data.high_risk_count || 0;

  // Update header badges
  const headerBadge = document.getElementById("facilityHeaderBadge");
  if (headerBadge && data.facility_name) {
    headerBadge.innerText = `${data.facility_name} (${data.region || 'Haryana'})`;
  }
  const countBadge = document.getElementById("facilitySiloCountBadge");
  if (countBadge) {
    countBadge.innerText = `${data.total_silos || 0} Silos Connected`;
  }
}

function renderWeather(weather) {
  if (!weather) return;
  document.getElementById("weatherTemp").innerText = `${weather.current_temp_c}°C`;
  document.getElementById("weatherRH").innerText = `${weather.current_rh}% RH`;
  document.getElementById("weatherPop").innerText = `${Math.round(weather.current_precip_prob * 100)}% Rain`;
  document.getElementById("weatherCondition").innerText = `${weather.current_condition} · 48h Max: ${weather.max_rh_48h}% RH`;
}

function updateDecisionBanner() {
  if (!state.weatherData) return;
  const weather = state.weatherData;
  const isHindi = currentLang === "hi";

  const badge = document.getElementById("aerationStatusBadge");
  const headline = document.getElementById("aerationMainHeadline");
  const subtext = document.getElementById("aerationSubtext");
  const banner = document.getElementById("heroDecisionBanner");

  const shouldSeal = weather.current_rh >= 70.0 || weather.current_precip_prob >= 0.35;

  if (shouldSeal) {
    banner.className = "product-card p-5 border-l-4 border-l-rose-500 bg-[#121624]";
    badge.className = "px-2.5 py-0.5 rounded text-xs font-semibold bg-rose-950 text-rose-300 border border-rose-800";
    badge.innerText = isHindi ? "खिड़कियां व पंखे बंद रखें" : "Keep Intake Vents Sealed";
    headline.innerText = isHindi
      ? `बाहरी आर्द्रता (${weather.current_rh}%) अधिक है — पंखे बंद रखें`
      : `High Ambient Humidity (${weather.current_rh}%) — Keep Aeration Vents Sealed`;
    subtext.innerText = isHindi
      ? `बाहरी हवा में नमी अधिक है और वर्षा की संभावना (${Math.round(weather.current_precip_prob * 100)}%) है। इस समय पंखे चलाने से अनाज नमी सोख लेगा।`
      : `Outside air humidity exceeds the 70% safe threshold with rain forecast (${Math.round(weather.current_precip_prob * 100)}%). Ventilating now will force moisture into grain stacks.`;
  } else {
    banner.className = "product-card p-5 border-l-4 border-l-emerald-500 bg-[#101726]";
    badge.className = "px-2.5 py-0.5 rounded text-xs font-semibold bg-emerald-950 text-emerald-300 border border-emerald-800";
    badge.innerText = isHindi ? "हवा देना सुरक्षित है" : "Safe to Run Aeration Fans";
    headline.innerText = isHindi
      ? `हवा का अनुकूल समय: बाहर का मौसम सूखा है (${weather.current_rh}%)`
      : `Optimal Aeration Window Active (Outside RH: ${weather.current_rh}%)`;
    subtext.innerText = isHindi
      ? `बाहरी हवा ठंडी और सूखी है। रात में पंखे चलाकर अनाज के कोर तापमान और नमी को सुरक्षित सीमा में लाएं।`
      : `Outside air is drier than internal grain storage. Running intake fans will safely purge core stack heat and moisture.`;
  }
}

function renderSiloCards() {
  if (!state.facilityData || !state.facilityData.silos) return;
  const container = document.getElementById("siloGrid");
  if (!container) return;

  const isHindi = currentLang === "hi";

  container.innerHTML = state.facilityData.silos.map(silo => {
    const risk = silo.risk_assessment;
    const telem = silo.telemetry;
    const isCritical = risk.risk_tier === "HIGH";
    const isWarning = risk.risk_tier === "MEDIUM";

    let borderClass = "border-[#1E2B45]";
    let statusBadge = `<span class="px-2.5 py-0.5 rounded text-xs font-semibold bg-emerald-950 text-emerald-300 border border-emerald-800">Normal</span>`;

    if (isCritical) {
      borderClass = "border-rose-500/70 shadow-lg shadow-rose-950/30";
      statusBadge = `<span class="px-2.5 py-0.5 rounded text-xs font-semibold bg-rose-950 text-rose-300 border border-rose-800">Action Required</span>`;
    } else if (isWarning) {
      borderClass = "border-amber-500/60";
      statusBadge = `<span class="px-2.5 py-0.5 rounded text-xs font-semibold bg-amber-950 text-amber-300 border border-amber-800">Advisory</span>`;
    }

    const commandText = isHindi ? risk.primary_command_hi : risk.primary_command;
    const safeMoistureLimit = silo.safe_moisture_limit || (silo.grain_type === "paddy" ? 13.0 : 14.0);

    return `
      <div class="product-card p-5 ${borderClass} flex flex-col justify-between">
        
        <!-- Silo Header -->
        <div class="flex items-start justify-between pb-3 border-b border-[#1E2B45]">
          <div>
            <div class="flex items-center gap-2">
              <span class="text-xs font-numeric font-bold px-2 py-0.5 rounded bg-[#162034] text-slate-300 border border-[#213052]">
                ${silo.silo_id}
              </span>
              <h3 class="text-base font-bold text-white">${silo.name}</h3>
            </div>
            <div class="flex items-center gap-2 mt-1 text-xs text-slate-400">
              <span class="capitalize font-semibold text-amber-400">${silo.grain_type}</span>
              <span>·</span>
              <span>${silo.current_fill_tonnes} / ${silo.capacity_tonnes} Tonnes (${silo.fill_percentage}%)</span>
            </div>
          </div>

          <div class="flex items-center gap-2">
            ${statusBadge}
            <button onclick="openEditSiloModal('${silo.silo_id}', '${silo.name}', '${silo.grain_type}', ${silo.capacity_tonnes}, ${silo.current_fill_tonnes})" class="text-slate-400 hover:text-white p-1 text-xs" title="Edit Unit Parameters">
              <i class="fas fa-pencil"></i>
            </button>
            <button onclick="deleteSilo('${silo.silo_id}', '${silo.name}')" class="text-slate-400 hover:text-rose-400 p-1 text-xs" title="Delete Storage Unit">
              <i class="fas fa-trash"></i>
            </button>
          </div>
        </div>

        <!-- Physical Visualizer + 3 Critical Metric Meters -->
        <div class="grid grid-cols-4 gap-3 items-center my-4">
          <div class="col-span-1 flex justify-center">
            ${Visualizers.createSiloCrossSectionSVG(silo.fill_percentage, silo.grain_type, risk.risk_tier)}
          </div>
          <div class="col-span-3 grid grid-cols-3 gap-2">
            ${Visualizers.createMetricMeter(isHindi ? "नमी (MC)" : "Moisture", telem.grain_moisture_pct, "%", safeMoistureLimit, 8, 22)}
            ${Visualizers.createMetricMeter(isHindi ? "तापमान" : "Stack Temp", telem.temp_c, "°C", 26.0, 10, 48)}
            ${Visualizers.createMetricMeter(isHindi ? "आर्द्रता" : "Air RH", telem.rel_humidity, "%", 65.0, 20, 100)}
          </div>
        </div>

        <!-- Derived Microclimate Safety Margins -->
        <div class="grid grid-cols-3 gap-2 text-center text-xs bg-[#0B101C] rounded-lg p-2.5 mb-3 border border-[#1E2B45]">
          <div>
            <div class="text-[11px] text-slate-400">${isHindi ? "ओस बिंदु" : "Dew Point"}</div>
            <div class="font-numeric font-bold text-sky-400">${telem.dew_point_c}°C</div>
          </div>
          <div>
            <div class="text-[11px] text-slate-400">${isHindi ? "संतुलित नमी (EMC)" : "Eq. Moisture"}</div>
            <div class="font-numeric font-bold text-amber-400">${telem.emc_pct}%</div>
          </div>
          <div>
            <div class="text-[11px] text-slate-400">${isHindi ? "ताप वृद्धि दर" : "Heating Rate"}</div>
            <div class="font-numeric font-bold ${telem.dt_dt > 0.3 ? 'text-rose-400' : 'text-emerald-400'}">
              ${telem.dt_dt >= 0 ? '+' : ''}${telem.dt_dt.toFixed(2)}°C/h
            </div>
          </div>
        </div>

        <!-- Operator Action Playbook Box -->
        <div class="p-3 rounded-lg bg-[#0E1526] border border-[#1E2B45] text-xs">
          <div class="flex items-center justify-between pb-1.5 mb-1.5 border-b border-[#1E2B45]">
            <span class="font-bold text-slate-200 flex items-center gap-1.5">
              <i class="fas fa-clipboard-check text-emerald-400"></i>
              <span>${isHindi ? "ऑपरेटर निर्देश" : "Intervention Playbook"}</span>
            </span>
            <span class="font-numeric text-[11px] font-semibold px-2 py-0.5 rounded ${risk.can_aerate ? 'bg-emerald-950 text-emerald-300 border border-emerald-800' : 'bg-rose-950 text-rose-300 border border-rose-800'}">
              ${risk.fan_action === 'ON' ? '🌀 FANS ON' : (risk.fan_action === 'OFF' ? '🛑 FANS OFF' : '⚡ CONTROLLED')}
            </span>
          </div>

          <p class="font-semibold text-slate-100 mb-1.5 leading-snug">${commandText}</p>
          <p class="text-[11px] text-slate-400 leading-relaxed">${risk.window_to_act} · ${risk.aeration_reason}</p>
        </div>

        <!-- Footer: Inspection Trigger & Farmer Quick Reading Log -->
        <div class="flex items-center justify-between mt-3 pt-2.5 border-t border-[#1E2B45] text-xs">
          <button onclick="openLogReadingModal('${silo.silo_id}', '${silo.name}', '${silo.grain_type}', ${safeMoistureLimit}, ${telem.grain_moisture_pct}, ${telem.temp_c}, ${telem.rel_humidity})" class="px-2.5 py-1 rounded bg-sky-950/80 hover:bg-sky-900 text-sky-200 text-xs font-semibold border border-sky-800/80 transition flex items-center gap-1.5">
            <i class="fas fa-pen-to-square"></i>
            <span>${isHindi ? "रीडिंग दर्ज करें" : "Log Reading"}</span>
          </button>
          
          <button onclick="loadHistoricalChart('${silo.silo_id}')" class="px-2.5 py-1 rounded bg-[#162034] hover:bg-[#213052] text-slate-200 text-xs font-semibold border border-[#213052] transition">
            <i class="fas fa-chart-line mr-1 text-sky-400"></i>${isHindi ? "ग्राफ देखें" : "View Trends"}
          </button>
        </div>

      </div>
    `;
  }).join("");
}

/* ======================================================== */
/* FARMER CUSTOMIZATION MODALS HANDLERS                     */
/* ======================================================== */

function openAddSiloModal() {
  document.getElementById("addSiloModal")?.classList.remove("hidden");
}

function closeAddSiloModal() {
  document.getElementById("addSiloModal")?.classList.add("hidden");
}

async function handleAddSiloSubmit(e) {
  e.preventDefault();
  const form = e.target;
  const payload = {
    name: form.name.value,
    grain_type: form.grain_type.value,
    capacity_tonnes: parseFloat(form.capacity_tonnes.value),
    current_fill_tonnes: parseFloat(form.current_fill_tonnes.value),
    region: form.region.value,
    initial_moisture_pct: parseFloat(form.initial_moisture_pct.value),
    initial_temp_c: parseFloat(form.initial_temp_c.value),
    initial_rh: parseFloat(form.initial_rh.value),
  };

  try {
    const res = await fetch("/api/silos", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (res.ok) {
      showToast(data.message || "Storage unit registered successfully.");
      closeAddSiloModal();
      form.reset();
      await fetchSilosData();
    } else {
      alert(data.detail || "Failed to register silo.");
    }
  } catch (err) {
    console.error("Add silo failed:", err);
  }
}

function openLogReadingModal(siloId, name, crop, safeLimit, currentMC, currentTemp, currentRH) {
  document.getElementById("logModalSiloId").value = siloId;
  document.getElementById("logModalSiloTitle").innerText = `Log Reading · ${name}`;
  document.getElementById("logModalSiloBadge").innerText = siloId;
  document.getElementById("logModalCropBadge").innerText = crop;
  document.getElementById("logModalSafeLimit").innerText = `${safeLimit.toFixed(1)}%`;

  document.getElementById("logInputMoisture").value = currentMC.toFixed(1);
  document.getElementById("logInputTemp").value = currentTemp.toFixed(1);
  document.getElementById("logInputRH").value = currentRH.toFixed(1);

  document.getElementById("logReadingModal")?.classList.remove("hidden");
}

function closeLogReadingModal() {
  document.getElementById("logReadingModal")?.classList.add("hidden");
}

async function handleLogReadingSubmit(e) {
  e.preventDefault();
  const form = e.target;
  const siloId = form.silo_id.value;
  const payload = {
    grain_moisture_pct: parseFloat(form.grain_moisture_pct.value),
    temp_c: parseFloat(form.temp_c.value),
    rel_humidity: parseFloat(form.rel_humidity.value),
    notes: form.notes.value,
  };

  try {
    const res = await fetch(`/api/silos/${siloId}/reading`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (res.ok) {
      showToast(`Reading saved! Risk: ${data.prediction.risk_tier}`);
      closeLogReadingModal();
      await fetchSilosData();
      await loadHistoricalChart(siloId);
    } else {
      alert(data.detail || "Failed to save reading.");
    }
  } catch (err) {
    console.error("Log reading failed:", err);
  }
}

function openEditSiloModal(siloId, name, crop, capacity, fill) {
  document.getElementById("editModalSiloId").value = siloId;
  document.getElementById("editModalName").value = name;
  document.getElementById("editModalCrop").value = crop.toLowerCase();
  document.getElementById("editModalCapacity").value = capacity;
  document.getElementById("editModalFill").value = fill;

  document.getElementById("editSiloModal")?.classList.remove("hidden");
}

function closeEditSiloModal() {
  document.getElementById("editSiloModal")?.classList.add("hidden");
}

async function handleEditSiloSubmit(e) {
  e.preventDefault();
  const form = e.target;
  const siloId = form.silo_id.value;
  const payload = {
    name: form.name.value,
    grain_type: form.grain_type.value,
    capacity_tonnes: parseFloat(form.capacity_tonnes.value),
    current_fill_tonnes: parseFloat(form.current_fill_tonnes.value),
  };

  try {
    const res = await fetch(`/api/silos/${siloId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (res.ok) {
      showToast(data.message || "Storage unit updated.");
      closeEditSiloModal();
      await fetchSilosData();
    } else {
      alert(data.detail || "Failed to update silo.");
    }
  } catch (err) {
    console.error("Edit silo failed:", err);
  }
}

async function deleteSilo(siloId, name) {
  const isHindi = currentLang === "hi";
  const confirmMsg = isHindi
    ? `क्या आप वाकई साइलो "${name}" को हटाना चाहते हैं?`
    : `Are you sure you want to delete storage unit "${name}" (${siloId})?`;
  if (!confirm(confirmMsg)) return;

  try {
    const res = await fetch(`/api/silos/${siloId}`, { method: "DELETE" });
    const data = await res.json();
    if (res.ok) {
      showToast(`Silo ${siloId} deleted.`);
      await fetchSilosData();
    }
  } catch (err) {
    console.error("Delete failed:", err);
  }
}

async function openProfileModal() {
  try {
    const res = await fetch("/api/silos/facility/profile");
    const data = await res.json();
    document.getElementById("profileInputName").value = data.name || "Gurugram Central Agro-Mandi Godown";
    document.getElementById("profileInputFarmer").value = data.farmer_name || "Farmer In-Charge";
    document.getElementById("profileInputPhone").value = data.contact_phone || "+91 98765 43210";
    document.getElementById("profileInputRegion").value = data.region || "Haryana";
    document.getElementById("profileInputLat").value = data.lat || 28.4595;
    document.getElementById("profileInputLon").value = data.lon || 77.0266;
  } catch (e) {
    console.error("Profile fetch error:", e);
  }
  document.getElementById("farmProfileModal")?.classList.remove("hidden");
}

function closeProfileModal() {
  document.getElementById("farmProfileModal")?.classList.add("hidden");
}

async function handleFarmProfileSubmit(e) {
  e.preventDefault();
  const form = e.target;
  const payload = {
    name: form.name.value,
    farmer_name: form.farmer_name.value,
    contact_phone: form.contact_phone.value,
    region: form.region.value,
    lat: parseFloat(form.lat.value),
    lon: parseFloat(form.lon.value),
  };

  try {
    const res = await fetch("/api/silos/facility/profile", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (res.ok) {
      showToast("Farm profile updated!");
      closeProfileModal();
      await fetchWeatherData();
      await fetchSilosData();
    } else {
      alert(data.detail || "Failed to update profile.");
    }
  } catch (err) {
    console.error("Profile update failed:", err);
  }
}

/* ======================================================== */
/* HISTORICAL TRENDS, DIAGNOSTICS & SIMULATIONS             */
/* ======================================================== */

async function loadHistoricalChart(siloId) {
  state.activeSiloId = siloId;
  try {
    const res = await fetch(`/api/telemetry/history/${siloId}?limit=24`);
    const data = await res.json();
    const history = data.history || [];

    const labels = history.map(h => {
      const d = new Date(h.event_ts);
      return `${d.getHours()}:00`;
    });
    const temps = history.map(h => h.temp_c);
    const rhs = history.map(h => h.rel_humidity);
    const mcs = history.map(h => h.grain_moisture_pct);

    const ctx = document.getElementById("telemetryChart")?.getContext("2d");
    if (!ctx) return;

    if (state.chartInstance) {
      state.chartInstance.destroy();
    }

    document.getElementById("chartActiveSiloName").innerText = `${siloId} · 24-Hour Microclimate Drift`;

    state.chartInstance = new Chart(ctx, {
      type: "line",
      data: {
        labels: labels,
        datasets: [
          {
            label: "Stack Temp (°C)",
            data: temps,
            borderColor: "#EF4444",
            backgroundColor: "rgba(239, 68, 68, 0.08)",
            borderWidth: 2,
            tension: 0.25,
            yAxisID: "y",
            pointRadius: 2,
          },
          {
            label: "Internal RH (%)",
            data: rhs,
            borderColor: "#0EA5E9",
            backgroundColor: "rgba(14, 165, 233, 0.08)",
            borderWidth: 2,
            tension: 0.25,
            yAxisID: "y1",
            pointRadius: 2,
          },
          {
            label: "Grain Moisture (%)",
            data: mcs,
            borderColor: "#EAB308",
            backgroundColor: "rgba(234, 179, 8, 0.08)",
            borderWidth: 2,
            tension: 0.25,
            yAxisID: "y2",
            pointRadius: 2,
          },
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: "index", intersect: false },
        plugins: {
          legend: { labels: { color: "#CBD5E1", font: { family: "Plus Jakarta Sans", size: 11 } } }
        },
        scales: {
          x: { ticks: { color: "#94A3B8", font: { family: "JetBrains Mono" } }, grid: { color: "rgba(255,255,255,0.04)" } },
          y: {
            type: "linear",
            position: "left",
            ticks: { color: "#EF4444", font: { family: "JetBrains Mono" } },
            grid: { color: "rgba(255,255,255,0.04)" },
            title: { display: true, text: "Temp (°C)", color: "#EF4444", font: { size: 10 } }
          },
          y1: {
            type: "linear",
            position: "right",
            ticks: { color: "#0EA5E9", font: { family: "JetBrains Mono" } },
            grid: { drawOnChartArea: false },
            title: { display: true, text: "RH (%)", color: "#0EA5E9", font: { size: 10 } }
          },
          y2: {
            type: "linear",
            position: "right",
            ticks: { color: "#EAB308", font: { family: "JetBrains Mono" } },
            grid: { drawOnChartArea: false },
            title: { display: true, text: "MC (%)", color: "#EAB308", font: { size: 10 } }
          }
        }
      }
    });

  } catch (e) {
    console.error("Failed to render telemetry chart:", e);
  }
}

async function initKnowledgeGraph() {
  try {
    const res = await fetch("/api/graph/visualization");
    const graphData = await res.json();
    state.kgCanvasInstance = new KnowledgeGraphCanvas("kgCanvas");
    state.kgCanvasInstance.setData(graphData);
  } catch (e) {
    console.error("Knowledge Graph init failed:", e);
  }
}

async function triggerSimulation(scenarioKey) {
  try {
    const res = await fetch("/api/simulation/trigger", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ scenario_key: scenarioKey })
    });
    const result = await res.json();
    showToast(`Injected: ${result.scenario}`);
    closeSimModal();
    await fetchSilosData();
    await loadHistoricalChart(result.silo_id);
  } catch (e) {
    console.error("Simulation error:", e);
  }
}

async function resetSimulation() {
  try {
    const res = await fetch("/api/simulation/reset", { method: "POST" });
    const result = await res.json();
    showToast(result.message);
    closeSimModal();
    await fetchSilosData();
    await loadHistoricalChart(state.activeSiloId);
  } catch (e) {
    console.error("Reset error:", e);
  }
}

async function runWhatIfPrediction() {
  const form = document.getElementById("whatIfForm");
  const temp = parseFloat(form.temp_c.value);
  const rh = parseFloat(form.rh.value);
  const mc = parseFloat(form.mc.value);
  const dt = parseFloat(form.dt_dt.value);
  const grain = form.grain_type.value;

  try {
    const res = await fetch("/api/predict", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        grain_type: grain,
        temp_c: temp,
        rel_humidity: rh,
        grain_moisture_pct: mc,
        dt_dt: dt,
      })
    });
    const data = await res.json();
    const pred = data.prediction;
    const play = data.playbook;

    const resultBox = document.getElementById("whatIfResult");
    resultBox.classList.remove("hidden");
    resultBox.innerHTML = `
      <div class="p-4 rounded-xl border ${pred.risk_tier === 'HIGH' ? 'bg-rose-950/40 border-rose-500/50' : (pred.risk_tier === 'MEDIUM' ? 'bg-amber-950/40 border-amber-500/50' : 'bg-emerald-950/40 border-emerald-500/50')} text-xs">
        <div class="flex items-center justify-between mb-2">
          <span class="text-sm font-bold text-white uppercase">${pred.risk_tier} RISK TIER</span>
          <span class="font-numeric text-slate-300">P(spoil): ${(pred.p_high * 100).toFixed(1)}%</span>
        </div>
        <p class="text-slate-200 font-semibold mb-2">${play.primary_command}</p>
        <div class="grid grid-cols-2 gap-2 text-slate-300 text-[11px] mb-2 font-numeric">
          <div>Random Forest: ${(pred.rf_probabilities.high * 100).toFixed(1)}%</div>
          <div>Neural Net: ${(pred.nn_probabilities.high * 100).toFixed(1)}%</div>
          <div>Dew Point: ${play.dew_point_c}°C</div>
          <div>EMC: ${play.equilibrium_moisture_pct}%</div>
        </div>
        <div class="text-[11px] text-slate-400">Aeration Status: <span class="font-bold text-white">${play.fan_action}</span> (${play.aeration_reason})</div>
      </div>
    `;
  } catch (e) {
    console.error("What-If failed:", e);
  }
}

async function openMetricsModal() {
  document.getElementById("metricsModal")?.classList.remove("hidden");
  try {
    const res = await fetch("/api/metrics/summary");
    const data = await res.json();

    const bTable = document.getElementById("benchmarksTableBody");
    if (bTable) {
      bTable.innerHTML = data.benchmarks.map(b => `
        <tr class="border-b border-[#213052] text-slate-300">
          <td class="py-2.5 font-medium text-white">${b.dimension}</td>
          <td class="py-2.5 font-numeric text-sky-400">${b.target}</td>
          <td class="py-2.5 font-numeric font-bold text-emerald-400">${b.observed}</td>
          <td class="py-2.5 text-slate-400">${b.method}</td>
          <td class="py-2.5 text-emerald-400 font-semibold"><i class="fas fa-check-circle mr-1"></i>${b.status}</td>
        </tr>
      `).join("");
    }

    const sdgContainer = document.getElementById("sdgCardsContainer");
    if (sdgContainer) {
      sdgContainer.innerHTML = data.sdg_impact.map(s => `
        <div class="p-4 rounded-xl bg-[#131B2E] border border-[#213052] text-xs">
          <div class="flex items-center gap-2 mb-2">
            <span class="px-2 py-0.5 rounded font-bold text-white text-[10px]" style="background-color: ${s.color}">${s.sdg_code}</span>
            <span class="font-bold text-white text-sm">${s.title}</span>
          </div>
          <div class="text-[11px] text-slate-400 mb-2 font-numeric">${s.targets}</div>
          <div class="mb-2"><span class="text-rose-400 font-medium">Baseline:</span> <span class="text-slate-300">${s.baseline}</span></div>
          <div><span class="text-emerald-400 font-medium">Outcome:</span> <span class="text-slate-200">${s.outcome}</span></div>
        </div>
      `).join("");
    }
  } catch (e) {
    console.error("Failed to fetch metrics:", e);
  }
}

function closeMetricsModal() {
  document.getElementById("metricsModal")?.classList.add("hidden");
}

function openSimModal() {
  document.getElementById("simModal")?.classList.remove("hidden");
}

function closeSimModal() {
  document.getElementById("simModal")?.classList.add("hidden");
}

function openReportModal() {
  document.getElementById("reportModal")?.classList.remove("hidden");
  const now = new Date();
  document.getElementById("reportDate").innerText = now.toLocaleString();
  document.getElementById("reportFacility").innerText = state.facilityData?.facility_name || "Gurugram Central Agro-Mandi (Haryana)";

  const body = document.getElementById("reportTableBody");
  if (body && state.facilityData && state.facilityData.silos) {
    body.innerHTML = state.facilityData.silos.map(s => `
      <tr class="border-b border-slate-200 text-xs">
        <td class="py-2 font-bold">${s.silo_id} - ${s.name}</td>
        <td class="py-2 uppercase font-semibold text-slate-800">${s.grain_type}</td>
        <td class="py-2 font-numeric">${s.telemetry.temp_c}°C</td>
        <td class="py-2 font-numeric">${s.telemetry.rel_humidity}%</td>
        <td class="py-2 font-numeric font-bold">${s.telemetry.grain_moisture_pct}%</td>
        <td class="py-2 font-bold ${s.risk_assessment.risk_tier === 'HIGH' ? 'text-rose-600' : (s.risk_assessment.risk_tier === 'MEDIUM' ? 'text-amber-600' : 'text-emerald-600')}">
          ${s.risk_assessment.risk_tier}
        </td>
        <td class="py-2 text-[11px]">${s.risk_assessment.primary_command}</td>
      </tr>
    `).join("");
  }
}

function closeReportModal() {
  document.getElementById("reportModal")?.classList.add("hidden");
}

function showToast(msg) {
  const toast = document.createElement("div");
  toast.className = "fixed bottom-5 right-5 z-50 px-4 py-2.5 rounded-lg bg-emerald-700 text-white font-medium text-xs shadow-2xl flex items-center gap-2";
  toast.innerHTML = `<i class="fas fa-check-circle"></i> ${msg}`;
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 3500);
}
