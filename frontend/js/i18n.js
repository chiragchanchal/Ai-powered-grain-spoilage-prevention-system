/**
 * Internationalization (i18n) Module: English & Hindi (हिन्दी)
 * Grounded in grain warehousing terminology per Chapter 9 operator feedback.
 */

const translations = {
  en: {
    productName: "AgroGuard",
    productTagline: "Grain Storage Intelligence & Spoilage Prevention",
    facilityLabel: "Facility",
    allSilos: "Storage Silos",
    statusSafe: "Normal",
    statusWarning: "Advisory",
    statusCritical: "Action Required",
    aerationAdvisorTitle: "Ventilation & Aeration Advisor",
    sealVentsRecommendation: "Keep Outside Intake Vents Sealed",
    openVentsRecommendation: "Safe to Run Aeration Fans",
    tempLabel: "Temperature",
    humidityLabel: "Interstitial RH",
    moistureLabel: "Grain Moisture",
    dewPointLabel: "Dew Point",
    emcLabel: "Equilibrium Moisture",
    driftLabel: "Thermal Drift Rate",
    playbookTitle: "Operator Playbook",
    simModalTitle: "Stress-Test Simulation",
    metricsModalTitle: "Evaluation Benchmarks & SDG Impact",
    reportModalTitle: "Facility Compliance Report",
    trendTitle: "24-Hour Telemetry Trends",
    switchLang: "हिन्दी में बदलें",
    printReportBtn: "Print Inspection Sheet",
    resetBtn: "Reset to Baseline",
    closeBtn: "Close",
    addSiloBtn: "Add Storage Silo",
    farmProfileBtn: "Farm Profile",
    addSiloModalTitle: "Register New Storage Silo / Godown",
    logReadingBtn: "Log Reading",
    editSiloBtn: "Edit",
    deleteSiloBtn: "Delete",
  },
  hi: {
    productName: "एग्रोगार्ड (AgroGuard)",
    productTagline: "अनाज भंडारण सुरक्षा एवं सड़न रोकथाम प्रणाली",
    facilityLabel: "भंडारण केंद्र",
    allSilos: "अनाज साइलो",
    statusSafe: "सुरक्षित",
    statusWarning: "सतर्कता",
    statusCritical: "त्वरित कार्रवाई",
    aerationAdvisorTitle: "वेंटिलेशन एवं पंखा संचालन सलाह",
    sealVentsRecommendation: "बाहरी वेंटिलेशन और खिड़कियां पूरी तरह बंद रखें",
    openVentsRecommendation: "पंखे चलाकर अनाज ठंडा व सूखा करना सुरक्षित है",
    tempLabel: "अनाज तापमान",
    humidityLabel: "आंतरिक आर्द्रता",
    moistureLabel: "अनाज की नमी",
    dewPointLabel: "ओस बिंदु (Dew Point)",
    emcLabel: "संतुलित नमी (EMC)",
    driftLabel: "ताप वृद्धि दर",
    playbookTitle: "ऑपरेटर कार्य निर्देश",
    simModalTitle: "सिमुलेशन परीक्षण",
    metricsModalTitle: "मूल्यांकन मानक एवं एसडीजी प्रभाव",
    reportModalTitle: "भंडारण निरीक्षण प्रमाणपत्र",
    trendTitle: "24 घंटे का टेलीमेट्री रुझान",
    switchLang: "Switch to English",
    printReportBtn: "निरीक्षण रिपोर्ट प्रिंट करें",
    resetBtn: "रीसेट करें",
    closeBtn: "बंद करें",
    addSiloBtn: "नया साइलो जोड़ें",
    farmProfileBtn: "फार्म प्रोफाइल",
    addSiloModalTitle: "नया अनाज साइलो / गोदाम दर्ज करें",
    logReadingBtn: "रीडिंग दर्ज करें",
    editSiloBtn: "संपादित करें",
    deleteSiloBtn: "हटाएं",
  }
};

let currentLang = "en";

function t(key) {
  return translations[currentLang][key] || key;
}

function setLanguage(lang) {
  if (translations[lang]) {
    currentLang = lang;
    document.querySelectorAll("[data-i18n]").forEach(el => {
      const k = el.getAttribute("data-i18n");
      if (translations[lang][k]) {
        el.innerText = translations[lang][k];
      }
    });
    window.dispatchEvent(new CustomEvent("languageChanged", { detail: lang }));
  }
}
