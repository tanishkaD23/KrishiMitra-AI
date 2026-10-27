/**
 * KrishiMitra AI - Homepage Controller
 * Manages quick plot calculations, voice STT/TTS in both Hindi and English, and KrishiSathi widget.
 */

document.addEventListener("DOMContentLoaded", () => {
    let currentVoiceScript = "नमस्ते किसान भाई! आपके 2 एकड़ खेत में गेहूं की अनुमानित पैदावार लगभग 19.2 क्विंटल प्रति एकड़ रहने की संभावना है।";
    let isListening = false;
    let recognition = null;

    // DOM Elements
    const quickPlotForm = document.getElementById("quickPlotForm");
    const cropRadioBtns = document.querySelectorAll(".crop-radio-btn");
    const plotAcresInput = document.getElementById("plotAcres");
    const acreChips = document.querySelectorAll(".acre-chip");
    const yieldNumber = document.getElementById("yieldNumber");
    const totalHarvestNumber = document.getElementById("totalHarvestNumber");
    const benchmarkStatusBadge = document.getElementById("benchmarkStatusBadge");
    const confRangeText = document.getElementById("confRangeText");

    // Voice Elements
    const homeMicBtn = document.getElementById("homeMicBtn");
    const homeMicText = document.getElementById("homeMicText");
    const homeSpeakBtn = document.getElementById("homeSpeakBtn");
    const homeVoiceStatus = document.getElementById("homeVoiceStatus");
    const homeChatBox = document.getElementById("homeChatBox");
    const homeVoiceQueryForm = document.getElementById("homeVoiceQueryForm");
    const homeQueryInput = document.getElementById("homeQueryInput");

    // Crop radio pill toggle
    cropRadioBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            cropRadioBtns.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            const radio = btn.querySelector('input[type="radio"]');
            radio.checked = true;
        });
    });

    // Acre quick chips
    acreChips.forEach(chip => {
        chip.addEventListener("click", () => {
            acreChips.forEach(c => c.classList.remove("active"));
            chip.classList.add("active");
            plotAcresInput.value = parseFloat(chip.dataset.acres);
        });
    });

    plotAcresInput.addEventListener("input", (e) => {
        const val = parseFloat(e.target.value);
        acreChips.forEach(chip => {
            chip.classList.toggle("active", parseFloat(chip.dataset.acres) === val);
        });
    });

    // Form submission -> analyze
    quickPlotForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const selectedCrop = document.querySelector('input[name="crop"]:checked').value;
        const district = document.getElementById("districtSelect").value;
        const acres = parseFloat(plotAcresInput.value) || 2.0;
        const soilType = document.getElementById("soilSelect").value;
        const irrigation = document.getElementById("irrigationSelect").value;

        const payload = {
            crop: selectedCrop,
            district: district,
            plot_acres: acres,
            soil_type: soilType,
            irrigation_source: irrigation,
            sowing_window: "Timely Sown (Nov 01 - Nov 20)",
            seasonal_rainfall_mm: 65.0,
            march_max_temp_c: 31.5,
            nitrogen_kg_acre: selectedCrop === "Wheat" ? 48.0 : 32.0,
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

            if (!res.ok) throw new Error("Calculation failed");
            const data = await res.json();
            const y = data.yield;
            const adv = data.advisory;

            yieldNumber.textContent = y.predicted_yield_per_acre;
            totalHarvestNumber.textContent = `${y.total_harvest_quintals} Q`;

            const diff = y.performance_vs_regional_mean_pct;
            const isAbove = diff >= 0;
            const lang = window.krishiI18n ? window.krishiI18n.getCurrentLang() : "hi";

            if (lang === "hi") {
                benchmarkStatusBadge.textContent = `${isAbove ? '+' : ''}${diff}% जिला औसत से ${isAbove ? 'ऊपर' : 'नीचे'}`;
                confRangeText.textContent = `${y.confidence_interval_90.lower} - ${y.confidence_interval_90.upper} क्विंटल`;
            } else {
                benchmarkStatusBadge.textContent = `${isAbove ? '+' : ''}${diff}% vs District Average`;
                confRangeText.textContent = `${y.confidence_interval_90.lower} - ${y.confidence_interval_90.upper} Quintals`;
            }

            benchmarkStatusBadge.style.color = isAbove ? "#86efac" : "#fca5a5";

            // Update voice script
            if (lang === "hi") {
                currentVoiceScript = adv.hindi_voice_script;
            } else {
                currentVoiceScript = `Farmer friend! For your ${acres} acre plot, estimated ${selectedCrop} yield is approximately ${y.predicted_yield_per_acre} Quintals per acre. Total harvest is around ${y.total_harvest_quintals} Quintals.`;
            }

            // Append assistant announcement bubble
            appendAssistantBubble(currentVoiceScript);
        } catch (err) {
            console.error(err);
        }
    });

    // --- Voice Synthesis (TTS) ---
    function speakText(text) {
        if (!('speechSynthesis' in window)) {
            alert("Speech synthesis is not supported in this browser.");
            return;
        }

        window.speechSynthesis.cancel();
        const utterance = new SpeechSynthesisUtterance(text);
        const lang = window.krishiI18n ? window.krishiI18n.getCurrentLang() : "hi";
        utterance.lang = lang === "hi" ? "hi-IN" : "en-IN";
        utterance.rate = 0.95;

        // Choose appropriate voice
        const voices = window.speechSynthesis.getVoices();
        const voice = voices.find(v => lang === "hi" ? v.lang.includes("hi") : v.lang.includes("en-IN") || v.lang.includes("en-US"));
        if (voice) utterance.voice = voice;

        utterance.onstart = () => {
            homeVoiceStatus.textContent = lang === "hi" ? "कृषिसाथी बोल रहे हैं..." : "KrishiSathi is speaking...";
        };

        utterance.onend = () => {
            homeVoiceStatus.textContent = lang === "hi" ? "बोलकर पूछिए या अपनी फसल की ताजा स्थिति सुनिए" : "Ask by voice or listen to your crop status aloud";
        };

        window.speechSynthesis.speak(utterance);
    }

    homeSpeakBtn.addEventListener("click", () => {
        speakText(currentVoiceScript);
    });

    // --- Speech Recognition (STT) ---
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

    if (SpeechRecognition) {
        recognition = new SpeechRecognition();
        recognition.interimResults = false;
        recognition.maxAlternatives = 1;

        recognition.onstart = () => {
            isListening = true;
            homeMicBtn.classList.add("listening");
            const lang = window.krishiI18n ? window.krishiI18n.getCurrentLang() : "hi";
            homeMicText.textContent = lang === "hi" ? "सुन रहे हैं..." : "Listening...";
            homeVoiceStatus.textContent = lang === "hi" ? "आपकी आवाज सुन रहे हैं... कृपया बोलिए" : "Listening to your voice... Please speak";
        };

        recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            homeQueryInput.value = transcript;
            submitVoiceChat(transcript);
        };

        recognition.onerror = () => stopMic();
        recognition.onend = () => stopMic();
    } else {
        homeMicBtn.style.display = "none";
    }

    function toggleMic() {
        if (!recognition) return;
        if (isListening) {
            recognition.stop();
            stopMic();
        } else {
            const lang = window.krishiI18n ? window.krishiI18n.getCurrentLang() : "hi";
            recognition.lang = lang === "hi" ? "hi-IN" : "en-IN";
            try {
                recognition.start();
            } catch (err) {
                console.warn(err);
            }
        }
    }

    function stopMic() {
        isListening = false;
        homeMicBtn.classList.remove("listening");
        const lang = window.krishiI18n ? window.krishiI18n.getCurrentLang() : "hi";
        homeMicText.textContent = lang === "hi" ? "बोलकर पूछें" : "Ask by Voice";
        homeVoiceStatus.textContent = lang === "hi" ? "बोलकर पूछिए या अपनी फसल की ताजा स्थिति सुनिए" : "Ask by voice or listen to your crop status aloud";
    }

    homeMicBtn.addEventListener("click", toggleMic);

    // --- Voice Chat Form ---
    async function submitVoiceChat(query) {
        if (!query.trim()) return;

        appendUserBubble(query);
        homeQueryInput.value = "";

        const crop = document.querySelector('input[name="crop"]:checked').value;
        const acres = parseFloat(plotAcresInput.value) || 2.0;
        const currentYield = yieldNumber.textContent;

        const context = {
            crop: crop,
            plot_acres: acres,
            predicted_yield: currentYield,
            district: document.getElementById("districtSelect").value,
            alerts_hi: ["ताज जड़ (CRI) अवस्था पर पहली सिंचाई अवश्य करें।"],
            advisories_hi: ["संतुलित उर्वरक एवं समय पर सिंचाई प्रबंधन करें।"],
            eligible_schemes: [{ name_hi: "प्रधानमंत्री फसल बीमा योजना" }, { name_hi: "PM-KISAN" }]
        };

        try {
            const res = await fetch("/api/krishisathi/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ query: query, context: context })
            });

            if (!res.ok) throw new Error("Chat failed");
            const data = await res.json();
            const answer = data.answer;

            let sourcesHtml = "";
            if (data.sources && data.sources.length) {
                const pills = data.sources.map(s => {
                    const label = s.source_type === "official_pdf" ? "Official PDF" : (s.is_official ? "Official Portal" : "Web Ref");
                    const color = s.is_official ? "#16a34a" : "#2563eb";
                    return `<a href="${s.url}" target="_blank" rel="noopener noreferrer" style="display:inline-block;margin:3px 4px 0 0;padding:2px 6px;border-radius:10px;border:1px solid ${color};font-size:0.65rem;color:${color};text-decoration:none;">[${label}] ${s.title} (${s.access_date || ""})</a>`;
                }).join("");
                sourcesHtml = `<div class="chat-sources" style="margin-top:6px;display:flex;flex-wrap:wrap;">${pills}</div>`;
            }

            appendAssistantBubble(answer + sourcesHtml);
            speakText(answer);
        } catch (err) {
            console.error(err);
            appendAssistantBubble("उत्तर देने में असमर्थ। कृपया पुनः प्रयास करें।");
        }
    }

    function appendUserBubble(text) {
        const div = document.createElement("div");
        div.className = "v-bubble v-bubble-user";
        div.innerHTML = `<strong>किसान:</strong> <p>${text}</p>`;
        homeChatBox.appendChild(div);
        homeChatBox.scrollTop = homeChatBox.scrollHeight;
    }

    function appendAssistantBubble(text) {
        const div = document.createElement("div");
        div.className = "v-bubble v-bubble-assistant";
        div.innerHTML = `<strong>कृषिसाथी:</strong> <p>${text}</p>`;
        homeChatBox.appendChild(div);
        homeChatBox.scrollTop = homeChatBox.scrollHeight;
    }

    homeVoiceQueryForm.addEventListener("submit", (e) => {
        e.preventDefault();
        submitVoiceChat(homeQueryInput.value);
    });

    // Listen to global language change
    window.addEventListener("krishimitra:languageChanged", (e) => {
        const lang = e.detail.lang;
        if (lang === "en") {
            currentVoiceScript = `Welcome farmer friend! For your plot in Western UP, KrishiMitra estimates high accuracy crop yields and tailored precision advisory.`;
        } else {
            currentVoiceScript = `नमस्ते किसान भाई! कृषिमित्र में आपका स्वागत है। आपके खेत के लिए सटीक पैदावार और समयबद्ध सलाह उपलब्ध है।`;
        }
    });
});
