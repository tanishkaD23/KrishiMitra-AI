/**
 * KrishiMitra AI - Dedicated Forecast Page Controller
 */

document.addEventListener("DOMContentLoaded", () => {
    const fullPlotForm = document.getElementById("fullPlotForm");
    const cropRadioBtns = document.querySelectorAll(".crop-radio-btn");
    const plotAcresInput = document.getElementById("plotAcres");
    const acreChips = document.querySelectorAll(".acre-chip");
    const inputN = document.getElementById("inputN");
    const nValText = document.getElementById("nValText");
    const inputMarchTemp = document.getElementById("inputMarchTemp");
    const tempValText = document.getElementById("tempValText");

    const fYieldVal = document.getElementById("fYieldVal");
    const fTotalHarvest = document.getElementById("fTotalHarvest");
    const fBenchmarkBadge = document.getElementById("fBenchmarkBadge");
    const fConfText = document.getElementById("fConfText");
    const alertsBox = document.getElementById("alertsBox");
    const advisoryBox = document.getElementById("advisoryBox");

    let currentAdvisoriesData = null;

    cropRadioBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            cropRadioBtns.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            const radio = btn.querySelector('input[type="radio"]');
            radio.checked = true;

            if (radio.value === "Mustard") {
                inputN.value = 32;
                nValText.textContent = "32 kg/एकड़";
            } else {
                inputN.value = 48;
                nValText.textContent = "48 kg/एकड़";
            }
        });
    });

    acreChips.forEach(chip => {
        chip.addEventListener("click", () => {
            acreChips.forEach(c => c.classList.remove("active"));
            chip.classList.add("active");
            plotAcresInput.value = parseFloat(chip.dataset.acres);
        });
    });

    inputN.addEventListener("input", (e) => {
        nValText.textContent = `${e.target.value} kg/एकड़`;
    });

    inputMarchTemp.addEventListener("input", (e) => {
        tempValText.textContent = `${e.target.value} °C`;
    });

    async function runAnalysis() {
        const selectedCrop = document.querySelector('input[name="crop"]:checked').value;
        const district = document.getElementById("districtSelect").value;
        const acres = parseFloat(plotAcresInput.value) || 2.0;
        const soilType = document.getElementById("soilSelect").value;
        const irrigation = document.getElementById("irrigationSelect").value;
        const sowing = document.getElementById("sowingSelect").value;

        const payload = {
            crop: selectedCrop,
            district: district,
            plot_acres: acres,
            soil_type: soilType,
            irrigation_source: irrigation,
            sowing_window: sowing,
            seasonal_rainfall_mm: 65.0,
            march_max_temp_c: parseFloat(inputMarchTemp.value),
            nitrogen_kg_acre: parseFloat(inputN.value),
            phosphorus_kg_acre: selectedCrop === "Wheat" ? 22.0 : 16.0,
            potassium_kg_acre: selectedCrop === "Wheat" ? 15.0 : 8.0,
            state: "Uttar Pradesh"
        };

        try {
            const res = await fetch("/api/analyze", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });

            if (!res.ok) throw new Error("Analysis failed");
            const data = await res.json();
            const y = data.yield;
            currentAdvisoriesData = data.advisory;

            fYieldVal.textContent = y.predicted_yield_per_acre;
            fTotalHarvest.textContent = `${y.total_harvest_quintals} Q`;

            const diff = y.performance_vs_regional_mean_pct;
            const isAbove = diff >= 0;
            const lang = window.krishiI18n ? window.krishiI18n.getCurrentLang() : "hi";

            if (lang === "hi") {
                fBenchmarkBadge.textContent = `${isAbove ? '+' : ''}${diff}% जिला औसत से ${isAbove ? 'ऊपर' : 'नीचे'}`;
                fConfText.textContent = `${y.confidence_interval_90.lower} - ${y.confidence_interval_90.upper} क्विंटल`;
            } else {
                fBenchmarkBadge.textContent = `${isAbove ? '+' : ''}${diff}% vs District Average`;
                fConfText.textContent = `${y.confidence_interval_90.lower} - ${y.confidence_interval_90.upper} Quintals`;
            }

            fBenchmarkBadge.style.color = isAbove ? "#86efac" : "#fca5a5";

            renderAdvisories(lang);
        } catch (err) {
            console.error(err);
        }
    }

    function renderAdvisories(lang) {
        if (!currentAdvisoriesData) return;

        alertsBox.innerHTML = "";
        const alerts = lang === "hi" ? currentAdvisoriesData.alerts_hi : currentAdvisoriesData.alerts_en;
        if (alerts && alerts.length > 0) {
            alerts.forEach(text => {
                const div = document.createElement("div");
                div.style.background = "#fee2e2";
                div.style.borderLeft = "4px solid #ef4444";
                div.style.padding = "12px 16px";
                div.style.borderRadius = "8px";
                div.style.color = "#991b1b";
                div.style.fontWeight = "600";
                div.style.fontSize = "0.92rem";
                div.innerHTML = `<span style="display:inline-flex; align-items:center; vertical-align:middle; margin-right:6px;"><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polygon points="7.86 2 16.14 2 22 7.86 22 16.14 16.14 22 7.86 22 2 16.14 2 7.86 7.86 2"></polygon><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg></span><b>${lang === 'hi' ? 'महत्वपूर्ण चेतावनी:' : 'Critical Alert:'}</b> ${text}`;
                alertsBox.appendChild(div);
            });
        }

        advisoryBox.innerHTML = "";
        const items = lang === "hi" ? currentAdvisoriesData.advisories_hi : currentAdvisoriesData.advisories_en;
        items.forEach((item, idx) => {
            const card = document.createElement("div");
            card.style.background = "#f8fafc";
            card.style.border = "1px solid var(--border-light)";
            card.style.borderLeft = "4px solid var(--green-primary)";
            card.style.padding = "14px 18px";
            card.style.borderRadius = "10px";
            card.style.fontSize = "0.95rem";
            card.style.lineHeight = "1.5";
            card.innerHTML = `<b>${idx + 1}.</b> ${item}`;
            advisoryBox.appendChild(card);
        });
    }

    fullPlotForm.addEventListener("submit", (e) => {
        e.preventDefault();
        runAnalysis();
    });

    window.addEventListener("krishimitra:languageChanged", (e) => {
        renderAdvisories(e.detail.lang);
    });

    // Initial run
    runAnalysis();
});
