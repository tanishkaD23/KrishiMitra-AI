/**
 * KrishiMitra AI - Dedicated Crop Yield Prediction Controller
 * Connects the Yield Prediction form to POST /api/analyze with full English formatting,
 * accessible form validation (:user-invalid / aria-invalid sync), and dual unit display (q/acre & q/ha).
 */

document.addEventListener("DOMContentLoaded", () => {
    const fullPlotForm = document.getElementById("fullPlotForm");
    const stateSelect = document.getElementById("stateSelect");
    const districtSelect = document.getElementById("districtSelect");
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

    const STATE_DISTRICTS = {
        "Uttar Pradesh": [
            "Meerut", "Agra", "Aligarh", "Allahabad", "Ambedkar Nagar", "Amethi", "Amroha", "Auraiya",
            "Azamgarh", "Baghpat", "Bahraich", "Ballia", "Balrampur", "Banda", "Barabanki", "Bareilly",
            "Basti", "Bijnor", "Budaun", "Bulandshahr", "Chandauli", "Chitrakoot", "Deoria", "Etah",
            "Etawah", "Faizabad", "Farrukhabad", "Fatehpur", "Firozabad", "Gautam Buddha Nagar",
            "Ghaziabad", "Ghazipur", "Gonda", "Gorakhpur", "Hamirpur", "Hapur", "Hardoi", "Hathras",
            "Jalaun", "Jaunpur", "Jhansi", "Kannauj", "Kanpur Dehat", "Kanpur Nagar", "Kasganj",
            "Kaushambi", "Kheri", "Kushi Nagar", "Lalitpur", "Lucknow", "Maharajganj", "Mahoba",
            "Mainpuri", "Mathura", "Mau", "Mirzapur", "Moradabad", "Muzaffarnagar", "Pilibhit",
            "Pratapgarh", "Prayagraj", "Rae Bareli", "Rampur", "Saharanpur", "Sambhal",
            "Sant Kabeer Nagar", "Sant Ravidas Nagar", "Shahjahanpur", "Shamli", "Shravasti",
            "Siddharth Nagar", "Sitapur", "Sonbhadra", "Sultanpur", "Unnao", "Varanasi"
        ],
        "Madhya Pradesh": [
            "Bhopal", "Agar Malwa", "Alirajpur", "Anuppur", "Ashoknagar", "Balaghat", "Barwani",
            "Betul", "Bhind", "Burhanpur", "Chhatarpur", "Chhindwara", "Damoh", "Datia", "Dewas",
            "Dhar", "Dindori", "Guna", "Gwalior", "Harda", "Hoshangabad", "Indore", "Jabalpur",
            "Jhabua", "Katni", "Khandwa", "Khargone", "Mandla", "Mandsaur", "Morena", "Narmadapuram",
            "Narsinghpur", "Neemuch", "Niwari", "Panna", "Raisen", "Rajgarh", "Ratlam", "Rewa",
            "Sagar", "Satna", "Sehore", "Seoni", "Shahdol", "Shajapur", "Sheopur", "Shivpuri",
            "Sidhi", "Singrauli", "Tikamgarh", "Ujjain", "Umaria", "Vidisha"
        ],
        "Bihar": [
            "Patna", "Araria", "Arwal", "Aurangabad", "Banka", "Begusarai", "Bhagalpur", "Bhojpur",
            "Buxar", "Darbhanga", "Gaya", "Gopalganj", "Jamui", "Jehanabad", "Kaimur (Bhabua)",
            "Katihar", "Khagaria", "Kishanganj", "Lakhisarai", "Madhepura", "Madhubani", "Munger",
            "Muzaffarpur", "Nalanda", "Nawada", "Pashchim Champaran", "Purbi Champaran", "Purnia",
            "Rohtas", "Saharsa", "Samastipur", "Saran", "Sheikhpura", "Sheohar", "Sitamarhi",
            "Siwan", "Supaul", "Vaishali"
        ],
        "Rajasthan": [
            "Jaipur", "Ajmer", "Alwar", "Banswara", "Baran", "Barmer", "Bharatpur", "Bhilwara",
            "Bikaner", "Bundi", "Chittorgarh", "Churu", "Dausa", "Dholpur", "Dungarpur",
            "Ganganagar", "Hanumangarh", "Jaisalmer", "Jalore", "Jhalawar", "Jhunjhunu", "Jodhpur",
            "Karauli", "Kota", "Nagaur", "Pali", "Pratapgarh", "Rajsamand", "Sawai Madhopur",
            "Sikar", "Sirohi", "Sri Ganganagar", "Tonk", "Udaipur"
        ],
        "Punjab": [
            "Ludhiana", "Amritsar", "Barnala", "Bathinda", "Faridkot", "Fatehgarh Sahib", "Fazilka",
            "Ferozepur", "Firozepur", "Gurdaspur", "Hoshiarpur", "Jalandhar", "Kapurthala",
            "Malerkotla", "Mansa", "Moga", "Muktsar", "Nawanshahr", "Pathankot", "Patiala",
            "Rupnagar", "S.A.S Nagar", "Sangrur", "Tarn Taran"
        ],
        "Haryana": [
            "Karnal", "Ambala", "Bhiwani", "Charki Dadri", "Faridabad", "Fatehabad", "Gurgaon",
            "Hisar", "Jhajjar", "Jind", "Kaithal", "Karnal", "Kurukshetra", "Mahendragarh", "Mewat",
            "Palwal", "Panchkula", "Panipat", "Rewari", "Rohtak", "Sirsa", "Sonipat", "Yamunanagar"
        ]
    };

    function populateDistrictsForState(stateName, selectedDistrict = null) {
        if (!districtSelect) return;
        const districts = STATE_DISTRICTS[stateName] || STATE_DISTRICTS["Uttar Pradesh"];
        districtSelect.innerHTML = "";
        districts.forEach((dist, idx) => {
            const opt = document.createElement("option");
            opt.value = dist;
            opt.textContent = dist;
            if ((selectedDistrict && dist === selectedDistrict) || (!selectedDistrict && idx === 0)) {
                opt.selected = true;
            }
            districtSelect.appendChild(opt);
        });
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

    const resCropHeader = document.getElementById("resCropHeader");
    const fYieldVal = document.getElementById("fYieldVal");
    const fYieldHaVal = document.getElementById("fYieldHaVal");
    const fTotalHarvest = document.getElementById("fTotalHarvest");
    const fBenchmarkBadge = document.getElementById("fBenchmarkBadge");
    const fConfText = document.getElementById("fConfText");
    const fBaselineText = document.getElementById("fBaselineText");
    const alertsBox = document.getElementById("alertsBox");
    const advisoryBox = document.getElementById("advisoryBox");
    const formErrorBanner = document.getElementById("formErrorBanner");
    const btnSubmitForecast = document.getElementById("btnSubmitForecast");

    // Modern Web Guidance: Sync aria-invalid with CSS :user-invalid state
    const syncAria = (el) => {
        if (!el || typeof el.matches !== "function") return;
        try {
            el.setAttribute("aria-invalid", el.matches(":user-invalid") ? "true" : "false");
        } catch (_) {
            // Fallback for older engines
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

    // Crop radio card & dropdown toggle
    const forecastCropSelect = document.getElementById("forecastCropSelect");
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

    // Quick Acre Chips
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
        if (isNaN(acresRaw) || acresRaw < 0.1 || acresRaw > 100) {
            if (formErrorBanner) {
                formErrorBanner.textContent = "Please enter a valid plot size between 0.1 and 100.0 acres.";
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
        const soilType = document.getElementById("soilSelect").value;
        const irrigation = document.getElementById("irrigationSelect").value;
        const sowing = document.getElementById("sowingSelect").value;

        const payload = {
            crop: selectedCrop,
            state: selectedState,
            district: district,
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
            btnSubmitForecast.innerHTML = `<span>Calculating Yield Prediction...</span>`;
        }

        try {
            const res = await fetch("/api/analyze", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });

            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const data = await res.json();
            const y = data.yield;
            const adv = data.advisory;

            const qPerAcre = Number(y.predicted_yield_per_acre || 0).toFixed(1);
            const qPerHa = (Number(y.predicted_yield_per_acre || 0) * 2.471).toFixed(1);

            if (resCropHeader) {
                resCropHeader.textContent = `Estimated Yield • ${selectedCrop} (${district}, ${selectedState})`;
            }
            if (fYieldVal) fYieldVal.textContent = qPerAcre;
            if (fYieldHaVal) fYieldHaVal.textContent = `(${qPerHa} q/ha)`;
            if (fTotalHarvest) fTotalHarvest.textContent = `${y.total_harvest_quintals} Quintals`;

            const diff = Number(y.performance_vs_regional_mean_pct || 0);
            const isAbove = diff >= 0;

            if (fBenchmarkBadge) {
                fBenchmarkBadge.textContent = `${isAbove ? "+" : ""}${diff}% vs District Average`;
                fBenchmarkBadge.style.color = isAbove ? "#86efac" : "#fde047";
            }

            if (fConfText && y.confidence_interval_90) {
                fConfText.textContent = `${y.confidence_interval_90.lower} – ${y.confidence_interval_90.upper} q/acre`;
            }

            if (fBaselineText && y.regional_benchmark_mean) {
                fBaselineText.textContent = `${y.regional_benchmark_mean} q/acre`;
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
                btnSubmitForecast.innerHTML = `<span>Generate Crop Yield Prediction &amp; Advisory</span><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>`;
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
                div.innerHTML = `<strong>⚠️ Critical Field Alert:</strong> ${text}`;
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

    // Run initial prediction on load
    runAnalysis();
});
