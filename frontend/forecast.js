/**
 * KrishiMitra AI - Dedicated All-India Crop Yield Prediction Controller
 * Dynamically loads all 35 States/UTs, 736 Districts, 72 Crops, and 5 Seasons from /api/config,
 * connects the Yield Prediction form to POST /api/analyze, and renders Tonnes/Ha, Quintals/Ha,
 * Quintals/Acre, Soil & Weather Profiles, Previous-Year Comparison, and Feature Importances.
 */

document.addEventListener("DOMContentLoaded", () => {
    const fullPlotForm = document.getElementById("fullPlotForm");
    const stateSelect = document.getElementById("stateSelect");
    const districtSelect = document.getElementById("districtSelect");
    const seasonSelect = document.getElementById("seasonSelect");
    const cropYearSelect = document.getElementById("cropYearSelect");
    const cropRadioBtns = document.querySelectorAll(".crop-radio-btn");
    const plotAcresInput = document.getElementById("plotAcres");
    const acreChips = document.querySelectorAll(".acre-chip");
    const inputN = document.getElementById("inputN");
    const nValText = document.getElementById("nValText");
    const inputP = document.getElementById("inputP");
    const inputK = document.getElementById("inputK");
    const inputRain = document.getElementById("inputRain");
    const inputMarchTemp = document.getElementById("inputMarchTemp");
    const tempValText = document.getElementById("tempValText");
    const forecastCropSelect = document.getElementById("forecastCropSelect");

    let STATE_DISTRICTS = {
        "Uttar Pradesh": ["Meerut", "Agra", "Aligarh", "Prayagraj", "Bareilly", "Bijnor", "Bulandshahr", "Gorakhpur", "Hardoi", "Hathras", "Jhansi", "Kanpur Nagar", "Lucknow", "Mathura", "Moradabad", "Muzaffarnagar", "Saharanpur", "Shahjahanpur", "Sitapur", "Varanasi"],
        "Madhya Pradesh": ["Bhopal", "Indore", "Ujjain", "Sehore", "Vidisha", "Gwalior", "Jabalpur", "Sagar", "Rewa", "Dewas", "Morena", "Bhind"],
        "Bihar": ["Patna", "Gaya", "Muzaffarpur", "Bhagalpur", "Nalanda", "Rohtas", "Bhojpur", "Samastipur", "Begusarai", "Purnia", "Vaishali", "Darbhanga"],
        "Rajasthan": ["Jaipur", "Sri Ganganagar", "Hanumangarh", "Alwar", "Bharatpur", "Kota", "Bundi", "Baran", "Sikar", "Nagaur", "Jodhpur", "Udaipur"],
        "Punjab": ["Ludhiana", "Patiala", "Sangrur", "Bathinda", "Amritsar", "Jalandhar", "Moga", "Ferozepur", "Gurdaspur", "Hoshiarpur", "Kapurthala", "Mansa"],
        "Haryana": ["Karnal", "Kurukshetra", "Hisar", "Sirsa", "Ambala", "Panipat", "Sonipat", "Rohtak", "Jind", "Kaithal", "Fatehabad", "Yamunanagar"]
    };
    let ALL_CROPS = [];
    let ALL_SEASONS = ["Rabi", "Kharif", "Summer", "Whole Year", "Autumn", "Winter"];

    function populateStates(statesList, selectedState = "Uttar Pradesh") {
        if (!stateSelect || !Array.isArray(statesList) || !statesList.length) return;
        stateSelect.innerHTML = "";
        statesList.forEach(st => {
            const opt = document.createElement("option");
            opt.value = st;
            opt.textContent = st;
            if (st === selectedState) opt.selected = true;
            stateSelect.appendChild(opt);
        });
    }

    function populateDistrictsForState(stateName, selectedDistrict = null) {
        if (!districtSelect) return;
        const districts = STATE_DISTRICTS[stateName] || STATE_DISTRICTS["Uttar Pradesh"] || ["Meerut"];
        districtSelect.innerHTML = "";
        districts.forEach((dist, idx) => {
            const opt = document.createElement("option");
            opt.value = dist;
            opt.textContent = dist;
            if ((selectedDistrict && dist === selectedDistrict) || (!selectedDistrict && (dist === "Meerut" || idx === 0))) {
                opt.selected = true;
            }
            districtSelect.appendChild(opt);
        });
    }

    function populateCrops(cropsList, selectedCrop = "Wheat") {
        if (!forecastCropSelect || !Array.isArray(cropsList) || !cropsList.length) return;
        const currentVal = forecastCropSelect.value || selectedCrop;
        forecastCropSelect.innerHTML = "";
        cropsList.forEach(c => {
            const opt = document.createElement("option");
            opt.value = c;
            opt.textContent = c;
            if (c === currentVal) opt.selected = true;
            forecastCropSelect.appendChild(opt);
        });
    }

    async function loadDynamicConfig() {
        try {
            const res = await fetch("/api/config");
            if (!res.ok) return;
            const cfg = await res.json();
            if (cfg.state_districts && Object.keys(cfg.state_districts).length > 0) {
                STATE_DISTRICTS = cfg.state_districts;
            }
            if (Array.isArray(cfg.supported_states) && cfg.supported_states.length > 0) {
                populateStates(cfg.supported_states, stateSelect ? stateSelect.value : "Uttar Pradesh");
            }
            populateDistrictsForState(stateSelect ? stateSelect.value : "Uttar Pradesh", districtSelect ? districtSelect.value : "Meerut");
            if (Array.isArray(cfg.all_india_crops) && cfg.all_india_crops.length > 0) {
                ALL_CROPS = cfg.all_india_crops;
                populateCrops(ALL_CROPS, "Wheat");
            }
            if (Array.isArray(cfg.seasons) && cfg.seasons.length > 0 && seasonSelect) {
                ALL_SEASONS = cfg.seasons;
                const curSeason = seasonSelect.value || "Rabi";
                seasonSelect.innerHTML = "";
                ALL_SEASONS.forEach(s => {
                    const opt = document.createElement("option");
                    opt.value = s;
                    opt.textContent = s;
                    if (s === curSeason) opt.selected = true;
                    seasonSelect.appendChild(opt);
                });
            }
        } catch (err) {
            console.warn("Dynamic config fallback used:", err);
        }
    }

    if (stateSelect) {
        stateSelect.addEventListener("change", () => {
            populateDistrictsForState(stateSelect.value);
            runAnalysis();
        });
    }

    if (districtSelect) {
        districtSelect.addEventListener("change", () => {
            runAnalysis();
        });
    }

    if (seasonSelect) {
        seasonSelect.addEventListener("change", () => {
            runAnalysis();
        });
    }

    const resCropHeader = document.getElementById("resCropHeader");
    const fYieldVal = document.getElementById("fYieldVal");
    const fYieldHaVal = document.getElementById("fYieldHaVal");
    const fYieldTonneHa = document.getElementById("fYieldTonneHa");
    const fTotalHarvest = document.getElementById("fTotalHarvest");
    const fBenchmarkBadge = document.getElementById("fBenchmarkBadge");
    const fConfText = document.getElementById("fConfText");
    const fBaselineText = document.getElementById("fBaselineText");
    const fSoilConditionsBox = document.getElementById("fSoilConditionsBox");
    const fWeatherConditionsBox = document.getElementById("fWeatherConditionsBox");
    const fFeatureBarsList = document.getElementById("fFeatureBarsList");
    const fDataAvailabilityBadge = document.getElementById("fDataAvailabilityBadge");
    const fLimitationNoteBox = document.getElementById("fLimitationNoteBox");
    const alertsBox = document.getElementById("alertsBox");
    const advisoryBox = document.getElementById("advisoryBox");
    const formErrorBanner = document.getElementById("formErrorBanner");
    const btnSubmitForecast = document.getElementById("btnSubmitForecast");

    const syncAria = (el) => {
        if (!el || typeof el.matches !== "function") return;
        try {
            el.setAttribute("aria-invalid", el.matches(":user-invalid") ? "true" : "false");
        } catch (_) {
            el.setAttribute("aria-invalid", !el.checkValidity() ? "true" : "false");
        }
    };

    document.addEventListener("blur", (e) => {
        if (e.target && e.target.form === fullPlotForm) syncAria(e.target);
    }, true);

    document.addEventListener("input", (e) => {
        if (e.target && e.target.hasAttribute && e.target.hasAttribute("aria-invalid")) {
            syncAria(e.target);
        }
    });

    cropRadioBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            cropRadioBtns.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            const radio = btn.querySelector('input[type="radio"]');
            if (radio) {
                radio.checked = true;
                if (forecastCropSelect) forecastCropSelect.value = radio.value;
                if (radio.value === "Mustard") {
                    inputN.value = 32;
                    nValText.textContent = "32 kg/acre";
                    if (inputP) inputP.value = 16;
                    if (inputK) inputK.value = 8;
                } else {
                    inputN.value = 48;
                    nValText.textContent = "48 kg/acre";
                    if (inputP) inputP.value = 22;
                    if (inputK) inputK.value = 15;
                }
                runAnalysis();
            }
        });
    });

    if (forecastCropSelect) {
        forecastCropSelect.addEventListener("change", (e) => {
            const val = e.target.value;
            cropRadioBtns.forEach(b => {
                const r = b.querySelector('input[type="radio"]');
                if (r && r.value === val) {
                    r.checked = true;
                    b.classList.add("active");
                } else {
                    b.classList.remove("active");
                }
            });
            runAnalysis();
        });
    }

    acreChips.forEach(chip => {
        chip.addEventListener("click", () => {
            acreChips.forEach(c => c.classList.remove("active"));
            chip.classList.add("active");
            plotAcresInput.value = parseFloat(chip.dataset.acres).toFixed(1);
            plotAcresInput.setAttribute("aria-invalid", "false");
            if (formErrorBanner) formErrorBanner.style.display = "none";
            runAnalysis();
        });
    });

    if (inputN) {
        inputN.addEventListener("input", (e) => {
            nValText.textContent = `${e.target.value} kg/acre`;
        });
    }

    if (inputMarchTemp) {
        inputMarchTemp.addEventListener("input", (e) => {
            tempValText.textContent = `${e.target.value} °C`;
        });
    }

    async function runAnalysis() {
        const acresRaw = parseFloat(plotAcresInput.value);
        if (isNaN(acresRaw) || acresRaw < 0.1 || acresRaw > 500) {
            if (formErrorBanner) {
                formErrorBanner.textContent = "Please enter a valid plot size between 0.1 and 500.0 acres.";
                formErrorBanner.style.display = "block";
            }
            plotAcresInput.focus();
            return;
        }
        if (formErrorBanner) formErrorBanner.style.display = "none";

        const checkedCropEl = document.querySelector('input[name="crop"]:checked');
        const selectedCrop = forecastCropSelect ? forecastCropSelect.value : (checkedCropEl ? checkedCropEl.value : "Wheat");
        const selectedState = stateSelect ? stateSelect.value : "Uttar Pradesh";
        const district = districtSelect ? districtSelect.value : "Meerut";
        const selectedSeason = seasonSelect ? seasonSelect.value : "Rabi";
        const selectedYear = cropYearSelect ? (parseInt(cropYearSelect.value, 10) || 2026) : 2026;
        const soilType = document.getElementById("soilSelect").value;
        const irrigation = document.getElementById("irrigationSelect").value;
        const sowing = document.getElementById("sowingSelect").value;

        const payload = {
            crop: selectedCrop,
            state: selectedState,
            district: district,
            season: selectedSeason,
            crop_year: selectedYear,
            all_india_mode: true,
            plot_acres: acresRaw,
            soil_type: soilType,
            irrigation_source: irrigation,
            sowing_window: sowing,
            seasonal_rainfall_mm: inputRain ? (parseFloat(inputRain.value) || 65.0) : 65.0,
            march_max_temp_c: parseFloat(inputMarchTemp.value) || 31.5,
            nitrogen_kg_acre: parseFloat(inputN.value) || 48.0,
            phosphorus_kg_acre: inputP ? (parseFloat(inputP.value) || 22.0) : 22.0,
            potassium_kg_acre: inputK ? (parseFloat(inputK.value) || 15.0) : 15.0
        };

        if (btnSubmitForecast) {
            btnSubmitForecast.disabled = true;
            btnSubmitForecast.innerHTML = `<span>Calculating All-India Yield Prediction...</span>`;
        }

        try {
            const res = await fetch("/api/analyze", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });

            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const data = await res.json();
            const y = data.yield || {};
            const adv = data.advisory;

            if (y.supported === false) {
                if (formErrorBanner) {
                    formErrorBanner.textContent = y.message_en || "Sufficient historical or agronomic data is unavailable for this selection.";
                    formErrorBanner.style.display = "block";
                }
                return;
            }

            const qPerAcre = Number(y.predicted_yield_per_acre || 0).toFixed(1);
            const qPerHa = Number(y.predicted_yield_q_ha || (Number(y.predicted_yield_per_acre || 0) * 2.471)).toFixed(1);
            const tPerHa = Number(y.predicted_yield_tonne_ha || (Number(qPerHa) / 10.0)).toFixed(2);

            if (resCropHeader) {
                resCropHeader.textContent = `Estimated Yield • ${selectedCrop} (${y.season || selectedSeason} • ${district}, ${selectedState})`;
            }
            if (fYieldVal) fYieldVal.textContent = qPerAcre;
            if (fYieldHaVal) fYieldHaVal.textContent = `(${tPerHa} t/ha • ${qPerHa} q/ha)`;
            if (fYieldTonneHa) fYieldTonneHa.textContent = `${tPerHa} t/ha`;
            if (fTotalHarvest) fTotalHarvest.textContent = `${y.total_harvest_quintals} Quintals (${y.total_harvest_tonnes || (y.total_harvest_quintals / 10).toFixed(2)} t)`;

            const diff = Number(y.performance_vs_regional_mean_pct || 0);
            const isAbove = diff >= 0;

            if (fBenchmarkBadge) {
                fBenchmarkBadge.textContent = `${isAbove ? "+" : ""}${diff}% vs District Baseline`;
                fBenchmarkBadge.style.color = isAbove ? "#86efac" : "#fde047";
            }

            if (fConfText && y.confidence_interval_90) {
                fConfText.textContent = `${y.confidence_interval_90.lower} – ${y.confidence_interval_90.upper} q/acre`;
            }

            if (fBaselineText) {
                const prevComp = y.previous_year_comparison;
                if (prevComp && prevComp.previous_yield_q_acre) {
                    fBaselineText.textContent = `${prevComp.previous_yield_q_acre} q/ac (${prevComp.previous_year})`;
                } else if (y.regional_benchmark_mean) {
                    fBaselineText.textContent = `${y.regional_benchmark_mean} q/acre`;
                }
            }

            // Populate Soil & Weather Conditions
            const sc = y.soil_conditions || {};
            const da = y.data_availability || {};
            if (fSoilConditionsBox) {
                const phVal = sc.soil_ph || sc.pH || 7.1;
                const ocVal = sc.soil_oc_pct || sc.organic_carbon_pct || 0.58;
                fSoilConditionsBox.innerHTML = `
                    <strong style="color: var(--km-primary); display: block; margin-bottom: 4px;">Soil Conditions (${da.soil_data_available ? "District Survey" : "Regional Profile"})</strong>
                    <span>${sc.soil_type || soilType} • pH: <strong>${phVal}</strong> • OC: <strong>${ocVal}%</strong> • N:${payload.nitrogen_kg_acre}, P:${payload.phosphorus_kg_acre}, K:${payload.potassium_kg_acre} kg/ac</span>
                `;
            }

            const wc = y.weather_conditions || {};
            if (fWeatherConditionsBox) {
                const rainVal = wc.weather_rain_mm || wc.seasonal_rainfall_mm || payload.seasonal_rainfall_mm;
                const tempVal = wc.weather_temp_c || wc.max_temp_c || payload.march_max_temp_c;
                const rhVal = wc.weather_humidity_pct || wc.humidity_pct || 58;
                const solVal = wc.weather_solar_mj_m2 || wc.solar_radiation_mj_m2 || 18.2;
                fWeatherConditionsBox.innerHTML = `
                    <strong style="color: var(--km-primary); display: block; margin-bottom: 4px;">Weather &amp; Rainfall (${da.weather_data_available ? "District Station" : "Regional Profile"})</strong>
                    <span>Rain: <strong>${rainVal} mm</strong> • Temp: <strong>${tempVal}°C</strong> • RH: <strong>${rhVal}%</strong> • Solar: <strong>${solVal} MJ/m²</strong></span>
                `;
            }

            if (fFeatureBarsList) {
                fFeatureBarsList.innerHTML = `
                    <span class="chart-badge-tag">${y.district || district} Historical ${y.crop || selectedCrop} Trend</span>
                    <span class="chart-badge-tag">${y.season || selectedSeason} Rainfall &amp; Thermal Window</span>
                    <span class="chart-badge-tag">Balanced Soil NPK &amp; Irrigation (${irrigation})</span>
                `;
            }

            if (fDataAvailabilityBadge) {
                fDataAvailabilityBadge.textContent = (da.exact_district_crop_records > 0)
                    ? `Verified (${da.exact_district_crop_records} District Records)`
                    : "Regional Calibrated Profile";
            }
            if (fLimitationNoteBox) {
                const lims = Array.isArray(da.limitations) && da.limitations.length > 0
                    ? da.limitations.join(" ")
                    : "District-level crop, soil, and weather data matched from verified All-India records.";
                fLimitationNoteBox.innerHTML = `<strong>Note:</strong> ${lims}`;
            }

            renderEnglishAdvisories(adv);
        } catch (err) {
            console.error("Yield analysis error:", err);
            if (formErrorBanner) {
                formErrorBanner.textContent = "Unable to reach the prediction service right now. Please check your connection and try again.";
                formErrorBanner.style.display = "block";
            }
        } finally {
            if (btnSubmitForecast) {
                btnSubmitForecast.disabled = false;
                btnSubmitForecast.innerHTML = `<span>Calculate Crop Yield &amp; Generate Advisory</span><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>`;
            }
        }
    }

    function renderEnglishAdvisories(adv) {
        if (!adv) return;

        if (alertsBox) {
            alertsBox.innerHTML = "";
            const alerts = adv.alerts_en || [];
            alerts.forEach(text => {
                const div = document.createElement("div");
                div.style.background = "#FEF2F2";
                div.style.borderLeft = "4px solid #DC2626";
                div.style.padding = "12px 16px";
                div.style.borderRadius = "10px";
                div.style.color = "#991B1B";
                div.style.fontWeight = "600";
                div.style.fontSize = "0.9rem";
                div.innerHTML = `<strong>Critical Field Alert:</strong> ${text}`;
                alertsBox.appendChild(div);
            });
        }

        if (advisoryBox) {
            advisoryBox.innerHTML = "";
            const items = adv.advisories_en || [];
            if (items.length === 0) {
                advisoryBox.innerHTML = `<div style="padding:14px; background:var(--km-bg); border-radius:10px; color:var(--km-text-muted);">No additional stage warnings for the current configuration.</div>`;
                return;
            }
            items.forEach((item, idx) => {
                const card = document.createElement("div");
                card.style.background = "var(--km-bg)";
                card.style.border = "1px solid var(--km-border)";
                card.style.borderLeft = "4px solid var(--km-primary)";
                card.style.padding = "14px 18px";
                card.style.borderRadius = "10px";
                card.style.fontSize = "0.92rem";
                card.style.lineHeight = "1.55";
                card.style.color = "var(--km-text-body)";
                card.innerHTML = `<strong style="color: var(--km-primary);">Recommendation ${idx + 1}:</strong> ${item}`;
                advisoryBox.appendChild(card);
            });
        }
    }

    if (fullPlotForm) {
        fullPlotForm.addEventListener("submit", (e) => {
            e.preventDefault();
            runAnalysis();
        });
    }

    loadDynamicConfig().then(() => {
        runAnalysis();
    });
});
