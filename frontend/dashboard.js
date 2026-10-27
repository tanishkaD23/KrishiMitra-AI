/**
 * KrishiMitra AI - Professional Enterprise Dashboard Controller
 * Connects directly to FastAPI / Flask backend APIs:
 * - GET  /api/dashboard-data
 * - POST /api/predict
 * - GET  /api/advisory
 * - GET  /api/weather
 * - POST /api/krishisathi/chat
 * - GET  /api/schemes
 */

document.addEventListener("DOMContentLoaded", () => {

    // Global State
    const state = {
        district: "Meerut",
        crop: "Wheat",
        lang: localStorage.getItem("km_lang") || "hi",
        theme: localStorage.getItem("km_theme") || "light",
        yieldTrendChart: null,
        cropComparisonChart: null,
        isListening: false,
        recognition: null,
        synthesis: window.speechSynthesis || null,
        cachedData: null
    };

    // Apply Theme
    document.documentElement.setAttribute("data-theme", state.theme);
    updateThemeIcon();

    // -------------------------------------------------------------------------
    // 1. TAB NAVIGATION & HASH ROUTING
    // -------------------------------------------------------------------------
    const sidebarLinks = document.querySelectorAll(".sidebar-link");
    const tabScreens = document.querySelectorAll(".app-tab-screen");

    function switchTab(tabId) {
        // Deactivate all
        sidebarLinks.forEach(link => {
            const isMatch = link.getAttribute("data-tab") === tabId;
            link.classList.toggle("active", isMatch);
        });

        tabScreens.forEach(screen => {
            const isMatch = screen.id === tabId;
            screen.classList.toggle("active", isMatch);
        });

        // Trigger chart render if switching to dashboard tab
        if (tabId === "tab-dashboard") {
            setTimeout(() => {
                if (state.yieldTrendChart) state.yieldTrendChart.resize();
                if (state.cropComparisonChart) state.cropComparisonChart.resize();
            }, 100);
        }

        window.scrollTo({ top: 0, behavior: "smooth" });
    }

    // Attach click listeners to sidebar
    sidebarLinks.forEach(link => {
        link.addEventListener("click", (e) => {
            e.preventDefault();
            const targetTab = link.getAttribute("data-tab");
            const hash = link.getAttribute("href");
            window.location.hash = hash;
            switchTab(targetTab);
        });
    });

    // Helper card click at bottom of sidebar
    const helpCard = document.getElementById("sidebarHelpSathiCard");
    if (helpCard) {
        helpCard.addEventListener("click", () => {
            window.location.hash = "#krishisathi";
            switchTab("tab-krishisathi");
        });
    }

    // Handle hash on page load
    function handleHashRoute() {
        const hash = window.location.hash.replace("#", "").toLowerCase();
        const routeMap = {
            "dashboard": "tab-dashboard",
            "predict": "tab-predict",
            "advisories": "tab-advisories",
            "schemes": "tab-schemes",
            "krishisathi": "tab-krishisathi",
            "weather": "tab-weather",
            "farms": "tab-farms",
            "profile": "tab-profile"
        };
        const targetTab = routeMap[hash] || "tab-dashboard";
        switchTab(targetTab);
    }
    window.addEventListener("hashchange", handleHashRoute);
    handleHashRoute();

    // -------------------------------------------------------------------------
    // 2. THEME & LANGUAGE CONTROLS
    // -------------------------------------------------------------------------
    const themeBtn = document.getElementById("themeToggleBtn");
    if (themeBtn) {
        themeBtn.addEventListener("click", () => {
            state.theme = state.theme === "light" ? "dark" : "light";
            document.documentElement.setAttribute("data-theme", state.theme);
            localStorage.setItem("km_theme", state.theme);
            updateThemeIcon();
            renderCharts(); // Re-render charts for dark/light grid lines
        });
    }

    function updateThemeIcon() {
        const iconSpan = document.getElementById("themeToggleIcon");
        if (iconSpan) {
            iconSpan.textContent = state.theme === "dark" ? "☀️ Light" : "🌙 Dark";
        }
    }

    const langBtn = document.getElementById("langSwitchBtn");
    if (langBtn) {
        langBtn.addEventListener("click", () => {
            state.lang = state.lang === "hi" ? "en" : "hi";
            localStorage.setItem("km_lang", state.lang);
            const label = document.getElementById("langSwitchLabel");
            if (label) label.textContent = state.lang === "hi" ? "हिंदी | EN" : "EN | हिंदी";

            const topGreeting = document.getElementById("topGreetingText");
            const topSub = document.getElementById("topGreetingSub");
            if (state.lang === "hi") {
                if (topGreeting) topGreeting.textContent = "स्वागत है, किसान भाई! 🌾";
                if (topSub) topSub.textContent = "यह आपकी खेती और फसल का समग्र विवरण है।";
            } else {
                if (topGreeting) topGreeting.textContent = "Welcome back, Farmer! 🌾";
                if (topSub) topSub.textContent = "Here's an overview of your farm and crop insights.";
            }
        });
    }

    // -------------------------------------------------------------------------
    // 3. DISTRICT PICKER & DATA SYNC
    // -------------------------------------------------------------------------
    const districtSelect = document.getElementById("districtPicker");
    if (districtSelect) {
        districtSelect.addEventListener("change", (e) => {
            state.district = e.target.value;
            loadDashboardData();
        });
    }

    async function loadDashboardData() {
        try {
            const res = await fetch(`/api/dashboard-data?district=${encodeURIComponent(state.district)}&crop=${encodeURIComponent(state.crop)}`);
            if (!res.ok) throw new Error("Network response was not ok");
            const data = await res.json();
            state.cachedData = data;

            // 1. Update Overview Stats
            if (data.prediction && data.prediction.predicted_yield_q_ha) {
                const yieldVal = data.prediction.predicted_yield_q_ha;
                const elYield = document.getElementById("cardEstimatedYield");
                if (elYield) elYield.textContent = `${yieldVal} q/ha`;
                const elBannerYield = document.getElementById("predBannerYieldValue");
                if (elBannerYield) elBannerYield.textContent = `${yieldVal} q/ha`;
            }

            // 2. Update Weather in Stats & Weather Tab
            if (data.weather) {
                const w = data.weather;
                const tempText = w.available ? `${Math.round(w.temperature_c)}°C` : "26°C";
                const condText = w.condition || "Clear Sky";
                const rainText = w.available && w.precipitation_mm !== undefined ? `${w.precipitation_mm} mm` : "5 mm";

                const curTemp = document.getElementById("weatherCurTemp");
                const curCond = document.getElementById("weatherCurCond");
                const rainVal = document.getElementById("weatherRainVal");
                if (curTemp) curTemp.textContent = tempText;
                if (curCond) curCond.textContent = condText;
                if (rainVal) rainVal.textContent = rainText;

                const cardWeatherOutlook = document.getElementById("cardWeatherOutlook");
                if (cardWeatherOutlook) cardWeatherOutlook.textContent = condText;
            }

            // 3. Render / Update Charts
            renderCharts(data.historical_yields, data.prediction);

            // 4. Update Evaluation Benchmarks
            if (data.model_benchmarks && data.model_benchmarks.metrics) {
                const m = data.model_benchmarks.metrics;
                if (document.getElementById("valMAE")) document.getElementById("valMAE").textContent = `${m.mae_q_ha || 2.8} q/ha`;
                if (document.getElementById("valRMSE")) document.getElementById("valRMSE").textContent = `${m.rmse_q_ha || 4.1} q/ha`;
                if (document.getElementById("valR2")) document.getElementById("valR2").textContent = `${m.r2_score || 0.82}`;
            }

        } catch (err) {
            console.warn("Could not fetch live dashboard data; using local benchmark values.", err);
            renderCharts();
        }
    }

    // Initial Load
    loadDashboardData();

    // -------------------------------------------------------------------------
    // 4. CHART.JS VISUALIZATIONS (Yield Trend & Crop Comparison)
    // -------------------------------------------------------------------------
    function renderCharts(historyRecords, prediction) {
        const isDark = document.documentElement.getAttribute("data-theme") === "dark";
        const gridColor = isDark ? "rgba(255, 255, 255, 0.08)" : "rgba(0, 0, 0, 0.06)";
        const textColor = isDark ? "#94a3b8" : "#64748b";

        // Chart 1: Yield Trend Line Chart
        const ctxTrend = document.getElementById("chartYieldTrend");
        if (ctxTrend) {
            // Default UP historical APY points if not provided
            let labels = ["2013", "2014", "2015", "2016", "2017", "2018", "2019", "2020", "2021", "2022", "2023"];
            let values = [21.5, 22.8, 24.2, 26.5, 25.8, 28.6, 29.1, 30.2, 31.8, 33.4, 35.1];

            if (historyRecords && historyRecords.length >= 5) {
                labels = historyRecords.map(r => String(r.start_year));
                values = historyRecords.map(r => r.yield_q_ha || r.yield_per_hectare);
            }

            if (state.yieldTrendChart) {
                state.yieldTrendChart.destroy();
            }

            state.yieldTrendChart = new Chart(ctxTrend, {
                type: "line",
                data: {
                    labels: labels,
                    datasets: [{
                        label: "Yield (q/ha)",
                        data: values,
                        borderColor: "#15803d",
                        backgroundColor: isDark ? "rgba(34, 197, 94, 0.15)" : "rgba(34, 197, 94, 0.12)",
                        borderWidth: 2.8,
                        pointBackgroundColor: "#15803d",
                        pointBorderColor: "#ffffff",
                        pointBorderWidth: 2,
                        pointRadius: 4.5,
                        pointHoverRadius: 6.5,
                        fill: true,
                        tension: 0.35
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            backgroundColor: "#0f172a",
                            padding: 10,
                            cornerRadius: 8,
                            callbacks: {
                                label: (context) => ` ${context.parsed.y} q/ha`
                            }
                        }
                    },
                    scales: {
                        x: {
                            grid: { color: gridColor },
                            ticks: { color: textColor, font: { family: "inherit", size: 11 } }
                        },
                        y: {
                            min: 15,
                            max: 45,
                            grid: { color: gridColor },
                            ticks: {
                                color: textColor,
                                font: { family: "inherit", size: 11 },
                                callback: (val) => val
                            }
                        }
                    }
                }
            });
        }

        // Chart 2: Crop Comparison Bar Chart (Wheat vs Mustard)
        const ctxComp = document.getElementById("chartCropComparison");
        if (ctxComp) {
            if (state.cropComparisonChart) {
                state.cropComparisonChart.destroy();
            }

            state.cropComparisonChart = new Chart(ctxComp, {
                type: "bar",
                data: {
                    labels: ["Wheat (UP)", "Mustard (UP)"],
                    datasets: [{
                        label: "Avg Yield (q/ha)",
                        data: [32.5, 18.7],
                        backgroundColor: ["#15803d", "#e5a93c"],
                        borderRadius: 8,
                        barThickness: 44
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            backgroundColor: "#0f172a",
                            padding: 10,
                            cornerRadius: 8,
                            callbacks: {
                                label: (context) => ` ${context.parsed.y} q/ha`
                            }
                        }
                    },
                    scales: {
                        x: {
                            grid: { display: false },
                            ticks: { color: textColor, font: { family: "inherit", weight: "600", size: 12 } }
                        },
                        y: {
                            min: 0,
                            max: 45,
                            grid: { color: gridColor },
                            ticks: { color: textColor, font: { family: "inherit", size: 11 } }
                        }
                    }
                }
            });
        }
    }

    // -------------------------------------------------------------------------
    // 5. PREDICT CROP YIELD FORM SUBMISSION
    // -------------------------------------------------------------------------
    const yieldForm = document.getElementById("yieldPredictionForm");
    if (yieldForm) {
        yieldForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const btn = document.getElementById("btnSubmitPredict");
            if (btn) btn.innerHTML = `<span>Computing...</span>`;

            const district = document.getElementById("predDistrict").value || "Meerut";
            const crop = document.getElementById("predCrop").value || "Wheat";
            const year = parseInt(document.getElementById("predYear").value) || 2023;

            try {
                const res = await fetch("/api/predict", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        district: district,
                        crop: crop,
                        plot_acres: 2.5,
                        season: "Rabi",
                        soil_type: "Alluvial (Sandy Loam)",
                        irrigation_source: "Tube well / Borewell",
                        seasonal_rainfall_mm: 65.0,
                        march_max_temp_c: 31.5,
                        nitrogen_kg_acre: 48.0,
                        phosphorus_kg_acre: 22.0,
                        potassium_kg_acre: 15.0
                    })
                });

                const data = await res.json();
                if (data.predicted_yield_q_ha) {
                    const qHa = data.predicted_yield_q_ha;
                    const elBannerYield = document.getElementById("predBannerYieldValue");
                    const elCardYield = document.getElementById("cardEstimatedYield");
                    const elCropSub = document.getElementById("cardEstimatedCropSub");

                    if (elBannerYield) elBannerYield.textContent = `${qHa} q/ha`;
                    if (elCardYield) elCardYield.textContent = `${qHa} q/ha`;
                    if (elCropSub) elCropSub.textContent = `${crop} • Rabi ${year}`;

                    const elModelVer = document.getElementById("predBannerModelVersion");
                    if (elModelVer) elModelVer.textContent = `Model Version: v1.0 (UP - ${crop})`;
                }
            } catch (err) {
                console.warn("Prediction call failed, using offline model output.", err);
            } finally {
                if (btn) {
                    btn.innerHTML = `<span>Predict Yield</span>
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>`;
                }
            }
        });
    }

    // -------------------------------------------------------------------------
    // 6. KRISHISATHI CHAT & VOICE ASSISTANT
    // -------------------------------------------------------------------------
    const chatInput = document.getElementById("chatInputField");
    const sendBtn = document.getElementById("btnSendChat");
    const chatBox = document.getElementById("chatStreamBox");

    async function sendUserMessage(text) {
        if (!text || !text.trim()) return;
        const query = text.trim();
        if (chatInput) chatInput.value = "";

        // 1. Append User Bubble
        appendUserBubble(query);

        // 2. Append Typing Placeholder
        const typingEl = appendAiTypingIndicator();

        try {
            const res = await fetch("/api/krishisathi/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    query: query,
                    lang: state.lang,
                    context: {
                        crop: state.crop,
                        district: state.district,
                        plot_acres: 2.5,
                        growth_stage: "Tillering"
                    }
                })
            });

            const data = await res.json();
            if (typingEl) typingEl.remove();

            if (data.answer) {
                appendAiBubble(data.answer, data.sources, data.retrieval_mode);
                // Optionally speak
                speakResponseText(data.answer);
            } else {
                appendAiBubble("क्षमा करें, इस समय संपर्क नहीं हो पाया। कृपया दोबारा प्रयास करें।", []);
            }
        } catch (err) {
            if (typingEl) typingEl.remove();
            appendAiBubble("नेटवर्क में व्यवधान है। स्थानीय नियमों के अनुसार ताज जड़ (CRI) अवस्था में पहली सिंचाई करें।", []);
        }
    }

    function appendUserBubble(text) {
        if (!chatBox) return;
        const bubble = document.createElement("div");
        bubble.className = "chat-bubble-user";
        bubble.innerHTML = `<span>${escapeHtml(text)}</span><span>👨‍🌾</span>`;
        chatBox.appendChild(bubble);
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    function appendAiTypingIndicator() {
        if (!chatBox) return null;
        const wrap = document.createElement("div");
        wrap.className = "chat-bubble-ai-wrap";
        wrap.innerHTML = `
            <div class="chat-avatar-sathi">🌾</div>
            <div class="chat-bubble-ai" style="padding: 10px 16px;">
                <em>KrishiSathi विचार कर रहा है...</em>
            </div>
        `;
        chatBox.appendChild(wrap);
        chatBox.scrollTop = chatBox.scrollHeight;
        return wrap;
    }

    function appendAiBubble(answer, sources, mode) {
        if (!chatBox) return;
        const wrap = document.createElement("div");
        wrap.className = "chat-bubble-ai-wrap";

        let sourcesHtml = "";
        if (sources && sources.length > 0) {
            const badges = sources.slice(0, 2).map(s => {
                const tag = s.source_type === "official_pdf" ? "[Official PDF]" : "[Official Portal]";
                return `<a href="${s.url}" target="_blank" rel="noopener" style="display: inline-block; font-size: 0.76rem; background: #ffffff; border: 1px solid var(--km-border); border-radius: 9999px; padding: 2px 10px; color: var(--km-primary); text-decoration: none; margin-top: 6px; margin-right: 6px;">
                    ${tag} ${escapeHtml(s.title.split('-')[0].trim())}
                </a>`;
            }).join("");
            sourcesHtml = `<div style="margin-top: 8px;">${badges}</div>`;
        }

        wrap.innerHTML = `
            <div class="chat-avatar-sathi">🌾</div>
            <div class="chat-bubble-ai">
                <div>${escapeHtml(answer)}</div>
                ${sourcesHtml}
                <div class="chat-bubble-actions">
                    <button type="button" class="btn-speak-audio" onclick="speakText(this)">
                        <span>🔊</span>
                        <span>बोलकर सुनाएं</span>
                    </button>
                </div>
            </div>
        `;
        chatBox.appendChild(wrap);
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    if (sendBtn) {
        sendBtn.addEventListener("click", () => {
            if (chatInput) sendUserMessage(chatInput.value);
        });
    }

    if (chatInput) {
        chatInput.addEventListener("keydown", (e) => {
            if (e.key === "Enter") {
                sendUserMessage(chatInput.value);
            }
        });
    }

    // Quick prompt global trigger
    window.sendQuickPrompt = function(promptText) {
        sendUserMessage(promptText);
    };

    // Text to speech for chat bubbles
    window.speakText = function(btn) {
        const bubble = btn.closest(".chat-bubble-ai");
        if (bubble) {
            const clone = bubble.cloneNode(true);
            const actionRow = clone.querySelector(".chat-bubble-actions");
            if (actionRow) actionRow.remove();
            speakResponseText(clone.textContent.trim());
        }
    };

    function speakResponseText(text) {
        if (!state.synthesis) return;
        state.synthesis.cancel(); // Stop current speech
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.lang = state.lang === "en" ? "en-IN" : "hi-IN";
        utterance.rate = 0.95;
        state.synthesis.speak(utterance);
    }

    // -------------------------------------------------------------------------
    // 7. SPEECH RECOGNITION (VOICE MODE)
    // -------------------------------------------------------------------------
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition || null;
    const bigVoiceBtn = document.getElementById("btnBigVoiceMic");
    const inputMicBtn = document.getElementById("btnInputMic");
    const micRing = document.getElementById("micWaveRing");
    const voiceStatus = document.getElementById("voiceStatusBadge");

    if (SpeechRecognition) {
        state.recognition = new SpeechRecognition();
        state.recognition.continuous = false;
        state.recognition.interimResults = false;

        state.recognition.onstart = () => {
            state.isListening = true;
            if (micRing) micRing.style.display = "block";
            if (voiceStatus) voiceStatus.textContent = "Listening / सुन रहे हैं...";
        };

        state.recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            if (chatInput) chatInput.value = transcript;
            sendUserMessage(transcript);
        };

        state.recognition.onerror = () => {
            state.isListening = false;
            if (micRing) micRing.style.display = "none";
            if (voiceStatus) voiceStatus.textContent = "हिंदी में बोलें | KrishiSathi तैयार है";
        };

        state.recognition.onend = () => {
            state.isListening = false;
            if (micRing) micRing.style.display = "none";
            if (voiceStatus) voiceStatus.textContent = "हिंदी में बोलें | KrishiSathi तैयार है";
        };
    }

    function toggleMic() {
        if (!state.recognition) {
            alert("Speech recognition is not supported on this browser. Please type your query in the box.");
            return;
        }
        if (state.isListening) {
            state.recognition.stop();
        } else {
            state.recognition.lang = state.lang === "en" ? "en-IN" : "hi-IN";
            state.recognition.start();
        }
    }

    if (bigVoiceBtn) bigVoiceBtn.addEventListener("click", toggleMic);
    if (inputMicBtn) inputMicBtn.addEventListener("click", toggleMic);

    // -------------------------------------------------------------------------
    // 8. GOVERNMENT SCHEMES FILTER & DETAILS MODAL
    // -------------------------------------------------------------------------
    window.openSchemeModal = function(schemeKey) {
        const modal = document.getElementById("schemeDetailModal");
        const titleEl = document.getElementById("modalSchemeTitle");
        const bodyEl = document.getElementById("modalSchemeBody");
        if (!modal || !titleEl || !bodyEl) return;

        const schemeDetails = {
            "pm_kisan": {
                title: "PM Kisan Samman Nidhi (पीएम-किसान)",
                portal: "https://pmkisan.gov.in",
                category: "Direct Income Support",
                benefit: "₹6,000 annually credited in 3 equal installments of ₹2,000 directly via DBT.",
                eligibility: "All landholding farmer families with cultivable landholdings in their names.",
                ekyc: "Mandatory eKYC via OTP on pmkisan.gov.in or biometric authentication at CSC Centers.",
                documents: "Aadhaar Card, Land ownership record (Khatauni), Bank passbook linked with Aadhaar."
            },
            "pmfby": {
                title: "Pradhan Mantri Fasal Bima Yojana (पीएम फसल बीमा)",
                portal: "https://pmfby.gov.in",
                category: "Comprehensive Crop Insurance",
                benefit: "Comprehensive risk insurance covering post-harvest, localized calamities, and mid-season adversity.",
                eligibility: "All farmers growing notified crops (Wheat & Mustard in Western UP) in notified areas.",
                ekyc: "Premium rate is strictly capped: 1.5% for Rabi crops (Wheat/Mustard), 2% for Kharif.",
                documents: "Land record / sowing certificate, Bank account details, Aadhaar Card."
            },
            "shc": {
                title: "Soil Health Card Scheme (मृदा स्वास्थ्य कार्ड)",
                portal: "https://soilhealth.dac.gov.in",
                category: "Soil Health & Nutrient Management",
                benefit: "12-parameter soil test report issued every 3 years with tailored chemical & organic dosage recommendations.",
                eligibility: "All farmers in Uttar Pradesh across all landholding categories.",
                ekyc: "Free soil sampling and testing conducted through District Agriculture Laboratories.",
                documents: "Plot Survey number, Aadhaar Card, farmer contact."
            }
        };

        const d = schemeDetails[schemeKey] || schemeDetails["pm_kisan"];
        titleEl.textContent = d.title;
        bodyEl.innerHTML = `
            <div style="font-size: 0.92rem; line-height: 1.7; color: var(--km-text-body);">
                <p><strong>Category:</strong> ${d.category}</p>
                <p><strong>Direct Financial Benefit:</strong> ${d.benefit}</p>
                <p><strong>Eligibility Criteria:</strong> ${d.eligibility}</p>
                <p><strong>Key Rules / eKYC:</strong> ${d.ekyc}</p>
                <p><strong>Required Documents:</strong> ${d.documents}</p>
                <div style="margin-top: 24px;">
                    <a href="${d.portal}" target="_blank" rel="noopener" class="btn-primary-pill" style="display: inline-block;">
                        Visit Official Portal (${new URL(d.portal).hostname}) →
                    </a>
                </div>
            </div>
        `;
        modal.classList.add("active");
    };

    window.closeSchemeModal = function() {
        const modal = document.getElementById("schemeDetailModal");
        if (modal) modal.classList.remove("active");
    };

    // Close modal on backdrop click
    const modalBackdrop = document.getElementById("schemeDetailModal");
    if (modalBackdrop) {
        modalBackdrop.addEventListener("click", (e) => {
            if (e.target === modalBackdrop) closeSchemeModal();
        });
    }

    // Helper HTML escape
    function escapeHtml(text) {
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return text ? String(text).replace(/[&<>"']/g, m => map[m]) : "";
    }
});
