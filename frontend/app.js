/**
 * KrishiMitra AI - Frontend Controller & KrishiSathi Voice Engine
 * Handles Plot Analysis, Speech Recognition (Hindi STT), Speech Synthesis (Hindi TTS), and Realtime Q&A
 */

document.addEventListener("DOMContentLoaded", () => {
    // State
    let currentAnalysisContext = null;
    let latestHindiVoiceScript = "नमस्ते किसान भाई! कृषिमित्र में आपका स्वागत है। अपनी फसल और खेत की जानकारी भरकर पूर्वानुमान प्राप्त करें।";
    let isListening = false;
    let recognitionInstance = null;

    // DOM Elements - Form & Inputs
    const plotForm = document.getElementById("plotForm");
    const cropPills = document.querySelectorAll(".crop-pill");
    const plotAcresInput = document.getElementById("plotAcres");
    const landCategoryBadge = document.getElementById("landCategoryBadge");
    const chipBtns = document.querySelectorAll(".chip-btn");
    const loadingOverlay = document.getElementById("loadingOverlay");

    // Slider inputs & displays
    const inputN = document.getElementById("inputN");
    const valN = document.getElementById("valN");
    const inputP = document.getElementById("inputP");
    const valP = document.getElementById("valP");
    const inputK = document.getElementById("inputK");
    const valK = document.getElementById("valK");
    const inputMarchTemp = document.getElementById("inputMarchTemp");
    const valMarchTemp = document.getElementById("valMarchTemp");
    const inputRainfall = document.getElementById("inputRainfall");
    const valRainfall = document.getElementById("valRainfall");

    // Results Elements
    const yieldPerAcreEl = document.getElementById("yieldPerAcre");
    const totalHarvestEl = document.getElementById("totalHarvest");
    const benchmarkStatusTag = document.getElementById("benchmarkStatusTag");
    const confIntervalText = document.getElementById("confIntervalText");
    const confRangeBar = document.getElementById("confRangeBar");
    const alertsContainer = document.getElementById("alertsContainer");
    const advisoryList = document.getElementById("advisoryList");
    const schemesList = document.getElementById("schemesList");
    const schemeCount = document.getElementById("schemeCount");

    // Voice & Chat Elements
    const btnMicListen = document.getElementById("btnMicListen");
    const btnSpeakAloud = document.getElementById("btnSpeakAloud");
    const voiceStatusText = document.getElementById("voiceStatusText");
    const micButtonText = document.getElementById("micButtonText");
    const btnChatMic = document.getElementById("btnChatMic");
    const chatForm = document.getElementById("chatForm");
    const chatInput = document.getElementById("chatInput");
    const chatMessages = document.getElementById("chatMessages");
    const quickQBtns = document.querySelectorAll(".quick-q-btn");

    // Tab buttons
    const tabBtns = document.querySelectorAll(".tab-btn");
    const tabPanes = document.querySelectorAll(".tab-pane");

    // --- 1. Form Event Handlers & Sliders ---
    cropPills.forEach(pill => {
        pill.addEventListener("click", () => {
            cropPills.forEach(p => p.classList.remove("active"));
            pill.classList.add("active");
            const radio = pill.querySelector('input[type="radio"]');
            radio.checked = true;

            // Adjust default nitrogen based on crop
            if (radio.value === "Mustard") {
                inputN.value = 32;
                valN.textContent = "32 kg";
                inputP.value = 16;
                valP.textContent = "16 kg";
                inputK.value = 8;
                valK.textContent = "8 kg";
            } else {
                inputN.value = 48;
                valN.textContent = "48 kg";
                inputP.value = 22;
                valP.textContent = "22 kg";
                inputK.value = 15;
                valK.textContent = "15 kg";
            }
        });
    });

    // Land category update
    function updateLandCategory(acres) {
        if (acres <= 2.47) {
            landCategoryBadge.textContent = "सीमांत किसान (Marginal: < 2.5 एकड़)";
            landCategoryBadge.className = "badge-marginal";
        } else if (acres <= 4.94) {
            landCategoryBadge.textContent = "लघु किसान (Small: 2.5 - 5.0 एकड़)";
            landCategoryBadge.className = "badge-marginal";
        } else {
            landCategoryBadge.textContent = "मध्यम / बड़ा किसान (Medium/Large)";
            landCategoryBadge.className = "badge-marginal";
        }
    }

    plotAcresInput.addEventListener("input", (e) => {
        const acres = parseFloat(e.target.value) || 1.0;
        updateLandCategory(acres);
        chipBtns.forEach(btn => {
            btn.classList.toggle("active", parseFloat(btn.dataset.acres) === acres);
        });
    });

    chipBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            chipBtns.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            const acres = parseFloat(btn.dataset.acres);
            plotAcresInput.value = acres;
            updateLandCategory(acres);
        });
    });

    // Synchronize Sliders
    inputN.addEventListener("input", () => valN.textContent = `${inputN.value} kg`);
    inputP.addEventListener("input", () => valP.textContent = `${inputP.value} kg`);
    inputK.addEventListener("input", () => valK.textContent = `${inputK.value} kg`);
    inputMarchTemp.addEventListener("input", () => valMarchTemp.textContent = `${inputMarchTemp.value} °C`);
    inputRainfall.addEventListener("input", () => valRainfall.textContent = `${inputRainfall.value} mm`);

    // Tab Switching
    tabBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            tabBtns.forEach(b => b.classList.remove("active"));
            tabPanes.forEach(p => p.classList.remove("active"));
            btn.classList.add("active");
            const targetId = btn.getAttribute("data-tab");
            document.getElementById(targetId).classList.add("active");
        });
    });

    // --- 2. Analyze Plot Form Submission ---
    plotForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const selectedCrop = document.querySelector('input[name="crop"]:checked').value;
        const district = document.getElementById("districtSelect").value;
        const plotAcres = parseFloat(plotAcresInput.value) || 2.0;
        const soilType = document.getElementById("soilSelect").value;
        const irrigationSource = document.getElementById("irrigationSelect").value;
        const sowingWindow = document.getElementById("sowingSelect").value;

        const payload = {
            crop: selectedCrop,
            district: district,
            plot_acres: plotAcres,
            soil_type: soilType,
            irrigation_source: irrigationSource,
            sowing_window: sowingWindow,
            seasonal_rainfall_mm: parseFloat(inputRainfall.value),
            march_max_temp_c: parseFloat(inputMarchTemp.value),
            nitrogen_kg_acre: parseFloat(inputN.value),
            phosphorus_kg_acre: parseFloat(inputP.value),
            potassium_kg_acre: parseFloat(inputK.value),
            state: "Uttar Pradesh"
        };

        loadingOverlay.classList.remove("hidden");

        try {
            const res = await fetch("/api/analyze", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });

            if (!res.ok) throw new Error("विश्लेषण में त्रुटि आई");
            const data = await res.json();
            renderResults(data);
        } catch (err) {
            console.error("Error analyzing plot:", err);
            alert("डेटा लोड करने में समस्या आई। कृपया पुनः प्रयास करें।");
        } finally {
            loadingOverlay.classList.add("hidden");
        }
    });

    // --- 3. Render Results to DOM ---
    function renderResults(data) {
        const { yield: yData, advisory: advData, schemes: schemesData } = data;

        // Save context for KrishiSathi
        currentAnalysisContext = {
            crop: data.plot_input.crop,
            district: data.plot_input.district,
            plot_acres: data.plot_input.plot_acres,
            predicted_yield: yData.predicted_yield_per_acre,
            alerts_hi: advData.alerts_hi,
            advisories_hi: advData.advisories_hi,
            eligible_schemes: schemesData
        };

        // Update Yield Card
        yieldPerAcreEl.textContent = yData.predicted_yield_per_acre;
        totalHarvestEl.textContent = `${yData.total_harvest_quintals} क्विंटल`;

        const diff = yData.performance_vs_regional_mean_pct;
        const isAbove = diff >= 0;
        benchmarkStatusTag.textContent = `${isAbove ? '+' : ''}${diff}% जिला औसत से ${isAbove ? 'ऊपर' : 'नीचे'}`;
        benchmarkStatusTag.className = `status-pill ${isAbove ? 'status-above' : 'status-below'}`;

        const ci = yData.confidence_interval_90;
        confIntervalText.textContent = `${ci.lower} - ${ci.upper} क्विंटल`;

        // Update Voice Script
        latestHindiVoiceScript = advData.hindi_voice_script;
        voiceStatusText.textContent = `ताजा पूर्वानुमान: ${yData.predicted_yield_per_acre} Q/Acre | सुनने के लिए "सलाह सुनें" दबाएं`;

        // Render Alerts
        alertsContainer.innerHTML = "";
        if (advData.alerts_hi && advData.alerts_hi.length > 0) {
            advData.alerts_hi.forEach((alertHi, idx) => {
                const alertEn = advData.alerts_en[idx] || "";
                const isHeat = alertHi.includes("गर्मी") || alertHi.includes("तापमान") || alertHi.includes("कमी");
                const div = document.createElement("div");
                div.className = `alert-item ${isHeat ? 'danger' : ''}`;
                div.innerHTML = `
                    <div class="alert-title">⚠️ महत्वपूर्ण चेतावनी (Critical Warning)</div>
                    <div class="alert-desc">${alertHi}</div>
                    <div class="alert-en">${alertEn}</div>
                `;
                alertsContainer.appendChild(div);
            });
        }

        // Render Advisories
        advisoryList.innerHTML = "";
        advData.advisories_hi.forEach((advHi, idx) => {
            const advEn = advData.advisories_en[idx] || "";
            const div = document.createElement("div");
            div.className = "advisory-card";
            div.innerHTML = `
                <div class="advisory-hi">${idx + 1}. ${advHi}</div>
                <div class="advisory-en">${advEn}</div>
            `;
            advisoryList.appendChild(div);
        });

        // Render Schemes
        schemeCount.textContent = schemesData.length;
        schemesList.innerHTML = "";
        schemesData.forEach(s => {
            const card = document.createElement("div");
            card.className = "scheme-card";
            const docsListHtml = s.documents_required.map(d => `<li>📄 ${d}</li>`).join("");
            card.innerHTML = `
                <div class="scheme-header">
                    <div class="scheme-title">${s.name_hi}</div>
                    <span class="scheme-category">${s.category}</span>
                </div>
                <div class="scheme-benefit"><b>मुख्य लाभ:</b> ${s.benefit_hi}</div>
                <div class="scheme-docs-title">आवश्यक दस्तावेज (Required Documents):</div>
                <ul class="scheme-docs-list">${docsListHtml}</ul>
                <div class="scheme-footer">
                    ${s.portal_url ? `<a href="${s.portal_url}" target="_blank" rel="noopener" class="btn-apply-scheme">योजना पोर्टल पर जाएं ↗</a>` : ''}
                </div>
            `;
            schemesList.appendChild(card);
        });
    }

    // --- 4. KrishiSathi Speech Synthesis (Hindi TTS) ---
    function speakHindi(text) {
        if (!('speechSynthesis' in window)) {
            alert("आपके ब्राउज़र में बोलकर सुनाने की सुविधा (SpeechSynthesis) उपलब्ध नहीं है।");
            return;
        }

        window.speechSynthesis.cancel();
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.lang = "hi-IN";
        utterance.rate = 0.95; // slightly slower for rural clarity
        utterance.pitch = 1.0;

        // Try to pick a natural Hindi voice
        const voices = window.speechSynthesis.getVoices();
        const hindiVoice = voices.find(v => v.lang.includes("hi") || v.lang.includes("HI") || v.lang.includes("IN"));
        if (hindiVoice) utterance.voice = hindiVoice;

        utterance.onstart = () => {
            voiceStatusText.textContent = "🔊 कृषिसाथी बोल रहे हैं...";
            btnSpeakAloud.classList.add("speaking");
        };

        utterance.onend = () => {
            voiceStatusText.textContent = "बोलकर पूछिए या अपनी फसल की ताजा स्थिति सुनिए";
            btnSpeakAloud.classList.remove("speaking");
        };

        window.speechSynthesis.speak(utterance);
    }

    btnSpeakAloud.addEventListener("click", () => {
        speakHindi(latestHindiVoiceScript);
    });

    // --- 5. KrishiSathi Speech Recognition (Hindi STT) ---
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

    if (SpeechRecognition) {
        recognitionInstance = new SpeechRecognition();
        recognitionInstance.lang = "hi-IN";
        recognitionInstance.interimResults = false;
        recognitionInstance.maxAlternatives = 1;

        recognitionInstance.onstart = () => {
            isListening = true;
            btnMicListen.classList.add("listening");
            btnChatMic.classList.add("listening");
            micButtonText.textContent = "सुन रहे हैं... बोलिए";
            voiceStatusText.textContent = "🎙️ आपकी आवाज सुन रहे हैं... कृपया अपना सवाल हिंदी में बोलें";
        };

        recognitionInstance.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            console.log("Speech recognized:", transcript);
            chatInput.value = transcript;

            // Automatically switch to chat tab and send
            document.querySelector('[data-tab="tab-chat"]').click();
            sendChatMessage(transcript);
        };

        recognitionInstance.onerror = (event) => {
            console.error("Speech recognition error:", event.error);
            voiceStatusText.textContent = "आवाज पहचानने में समस्या हुई। कृपया पुनः बोलें या लिखकर पूछें।";
            stopListening();
        };

        recognitionInstance.onend = () => {
            stopListening();
        };
    } else {
        btnMicListen.style.display = "none";
        btnChatMic.style.display = "none";
        console.warn("SpeechRecognition not supported in this browser. User can type.");
    }

    function toggleListening() {
        if (!recognitionInstance) {
            alert("माइक सुविधा Google Chrome या Edge ब्राउज़र में सबसे अच्छी तरह काम करती है।");
            return;
        }

        if (isListening) {
            recognitionInstance.stop();
            stopListening();
        } else {
            try {
                recognitionInstance.start();
            } catch (err) {
                console.error("Recognition start error:", err);
            }
        }
    }

    function stopListening() {
        isListening = false;
        btnMicListen.classList.remove("listening");
        btnChatMic.classList.remove("listening");
        micButtonText.textContent = "बोलकर पूछें";
        voiceStatusText.textContent = "बोलकर पूछिए या अपनी फसल की ताजा स्थिति सुनिए";
    }

    btnMicListen.addEventListener("click", toggleListening);
    btnChatMic.addEventListener("click", toggleListening);

    // --- 6. KrishiSathi Chat System ---
    async function sendChatMessage(query) {
        if (!query.trim()) return;

        // Append User Bubble
        appendBubble("user", query);
        chatInput.value = "";

        // Fallback default context if analyze hasn't been run yet
        const context = currentAnalysisContext || {
            crop: document.querySelector('input[name="crop"]:checked').value,
            district: document.getElementById("districtSelect").value,
            plot_acres: parseFloat(plotAcresInput.value) || 2.0,
            predicted_yield: yieldPerAcreEl.textContent,
            alerts_hi: ["समय पर पहली सिंचाई ताज जड़ (CRI) अवस्था पर करें।"],
            advisories_hi: ["संतुलित खाद और पानी दें।"],
            eligible_schemes: [{ name_hi: "प्रधानमंत्री फसल बीमा योजना" }, { name_hi: "PM-KISAN" }]
        };

        try {
            const res = await fetch("/api/krishisathi/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ query: query, context: context })
            });

            if (!res.ok) throw new Error("Chat request failed");
            const data = await res.json();
            const answer = data.answer;

            appendBubble("assistant", answer);

            // Automatically speak the response aloud in Hindi!
            speakHindi(answer);
        } catch (err) {
            console.error("Chat error:", err);
            appendBubble("assistant", "माफ़ कीजिए, उत्तर प्राप्त करने में समस्या आई। कृपया पुनः प्रयास करें।");
        }
    }

    function appendBubble(sender, text) {
        const bubble = document.createElement("div");
        bubble.className = `chat-bubble bubble-${sender}`;
        bubble.innerHTML = `
            <div class="bubble-sender">${sender === 'user' ? 'किसान भाई:' : '🤖 कृषिसाथी:'}</div>
            <p>${text}</p>
        `;
        chatMessages.appendChild(bubble);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    chatForm.addEventListener("submit", (e) => {
        e.preventDefault();
        sendChatMessage(chatInput.value);
    });

    quickQBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            const query = btn.getAttribute("data-q");
            sendChatMessage(query);
        });
    });

    // --- 7. Initial Load ---
    // Trigger initial prediction for default Western UP 2.0 Acre Wheat plot
    plotForm.dispatchEvent(new Event("submit"));
});
