/**
 * KrishiMitra AI — Gnani.ai Voice AI Client
 * Official Integration for:
 *  1. Gnani Prisma v3.0 (Speech-to-Text) -> https://docs.gnani.ai/api/STT/speech-to-text
 *  2. Gnani Timbre v2.5 (Text-to-Speech) -> https://docs.gnani.ai/api/TTS/tts-inference
 * 
 * Works across:
 *  - Vanilla HTML/JS (krishisathi.html, dashboard.html, index.html)
 *  - React.js + Vite frontend (exportable ES6 module + window.KrishiGnaniVoice)
 *  - Netlify static hosting with optional remote Flask backend
 * 
 * Security:
 *  - GNANI_API_KEY is securely kept on the Python backend; never exposed to browser.
 *  - All requests are routed through backend proxy endpoints (/api/krishisathi/stt & /api/krishisathi/tts).
 *  - Gracefully falls back to browser Web Speech API & text chat if voice services are unavailable.
 */

(function (global) {
    "use strict";

    // Audio context & recording state
    let mediaRecorder = null;
    let audioChunks = [];
    let recordStream = null;
    let recordTimer = null;
    let recordDurationSec = 0;
    const MAX_RECORD_SECONDS = 30; // Max duration for Gnani STT REST

    let currentAudioElement = null;
    let isSpeakingAudio = false;
    let activeBrowserRecognition = null;

    /**
     * Resolves the base API URL (supports separately hosted Flask backend and Netlify)
     */
    function getApiBaseUrl() {
        if (typeof window !== "undefined") {
            if (window.KRISHI_API_BASE_URL) return window.KRISHI_API_BASE_URL.replace(/\/+$/, "");
            try {
                const stored = localStorage.getItem("km_api_base");
                if (stored) return stored.replace(/\/+$/, "");
            } catch (e) {}
        }
        return "";
    }

    /**
     * Determines best supported audio mime type for browser recording
     */
    function getBestSupportedMimeType() {
        if (typeof MediaRecorder === "undefined") return "";
        const candidates = [
            "audio/webm;codecs=opus",
            "audio/webm",
            "audio/ogg;codecs=opus",
            "audio/ogg",
            "audio/mp4",
            "audio/wav",
        ];
        for (const type of candidates) {
            if (MediaRecorder.isTypeSupported && MediaRecorder.isTypeSupported(type)) {
                return type;
            }
        }
        return "";
    }

    /**
     * Strips markdown formatting for natural speech synthesis
     */
    function cleanTextForSpeech(text) {
        if (!text) return "";
        return String(text)
            .replace(/\*\*(.+?)\*\*/g, "$1")
            .replace(/\*(.+?)\*/g, "$1")
            .replace(/`(.+?)`/g, "$1")
            .replace(/https?:\/\/\S+/g, "")
            .replace(/[#•_~]+/g, " ")
            .replace(/\s+/g, " ")
            .trim();
    }

    /**
     * Fallback speech synthesis using browser window.speechSynthesis
     */
    function fallbackBrowserSpeak(text, lang = "hi-IN", onEndCallback = null) {
        if (typeof window === "undefined" || !("speechSynthesis" in window)) {
            if (onEndCallback) onEndCallback();
            return;
        }
        try {
            window.speechSynthesis.cancel();
            const clean = cleanTextForSpeech(text);
            const utterance = new SpeechSynthesisUtterance(clean);
            utterance.lang = lang.includes("hi") ? "hi-IN" : "en-IN";
            utterance.rate = 0.95;
            utterance.onend = () => {
                isSpeakingAudio = false;
                if (onEndCallback) onEndCallback();
            };
            utterance.onerror = () => {
                isSpeakingAudio = false;
                if (onEndCallback) onEndCallback();
            };
            isSpeakingAudio = true;
            window.speechSynthesis.speak(utterance);
        } catch (e) {
            isSpeakingAudio = false;
            if (onEndCallback) onEndCallback();
        }
    }

    /**
     * Fallback speech recognition using browser Web Speech API
     */
    function fallbackBrowserRecognition(options) {
        const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRec) {
            if (options.onError) {
                options.onError({
                    error_code: "SPEECH_NOT_SUPPORTED",
                    message: "Speech recognition is not supported in this browser. Please type your question.",
                });
            }
            return;
        }

        try {
            if (activeBrowserRecognition) {
                try { activeBrowserRecognition.stop(); } catch (e) {}
            }
            const rec = new SpeechRec();
            activeBrowserRecognition = rec;
            const langCode = (options.language || "hi").toLowerCase().includes("hi") ? "hi-IN" : "en-IN";
            rec.lang = langCode;
            rec.continuous = false;
            rec.interimResults = false;

            rec.onstart = () => {
                if (options.onStart) options.onStart();
            };

            rec.onresult = (evt) => {
                const transcript = (evt.results && evt.results[0] && evt.results[0][0])
                    ? evt.results[0][0].transcript
                    : "";
                if (options.onSuccess && transcript) {
                    options.onSuccess({
                        status: "success",
                        transcript: transcript,
                        provider: "Browser Web Speech API",
                        model: "browser-native",
                        detected_language_code: langCode,
                    });
                }
            };

            rec.onerror = (err) => {
                if (options.onError) {
                    options.onError({
                        error_code: err.error || "BROWSER_RECOGNITION_ERROR",
                        message: "Could not capture audio via browser speech. Please try typing your question.",
                    });
                }
            };

            rec.onend = () => {
                activeBrowserRecognition = null;
                if (options.onEnd) options.onEnd();
            };

            rec.start();
        } catch (err) {
            if (options.onError) {
                options.onError({
                    error_code: "BROWSER_REC_START_FAILED",
                    message: err.message || "Failed to start speech recognition.",
                });
            }
        }
    }

    const KrishiGnaniVoice = {
        /**
         * Check Gnani.ai backend status
         */
        async checkStatus() {
            try {
                const base = getApiBaseUrl();
                const res = await fetch(`${base}/api/krishisathi/voice-status`);
                if (res.ok) {
                    return await res.json();
                }
            } catch (e) {}
            return {
                status: "offline",
                gnani_configured: false,
                provider: "Browser Web Speech API Fallback",
                stt: { model: "prisma-v3.0" },
                tts: { model: "timbre-v2.5" },
            };
        },

        /**
         * Checks if voice recording is currently in progress
         */
        isRecording() {
            return mediaRecorder && mediaRecorder.state === "recording";
        },

        /**
         * Checks if audio is currently playing
         */
        isPlaying() {
            return isSpeakingAudio || (currentAudioElement && !currentAudioElement.paused);
        },

        /**
         * Stops any active speech audio playback (Gnani Timbre or Browser)
         */
        stopPlayback() {
            if (currentAudioElement) {
                try {
                    currentAudioElement.pause();
                    currentAudioElement.currentTime = 0;
                } catch (e) {}
                currentAudioElement = null;
            }
            if (typeof window !== "undefined" && "speechSynthesis" in window) {
                try {
                    window.speechSynthesis.cancel();
                } catch (e) {}
            }
            isSpeakingAudio = false;
        },

        /**
         * Starts microphone audio recording
         * @param {Object} options
         *   - onStart: callback when recording starts
         *   - onTick: callback every second with (durationSeconds, maxSeconds)
         *   - onError: callback on error with { error_code, message }
         */
        async startRecording(options = {}) {
            this.stopPlayback();

            if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                // Fall back to browser SpeechRecognition if MediaRecorder is not available
                fallbackBrowserRecognition({
                    language: options.language || "hi-IN",
                    onStart: options.onStart,
                    onSuccess: options.onSuccess,
                    onError: options.onError,
                    onEnd: options.onEnd,
                });
                return;
            }

            try {
                recordStream = await navigator.mediaDevices.getUserMedia({
                    audio: {
                        channelCount: 1,
                        echoCancellation: true,
                        noiseSuppression: true,
                        autoGainControl: true,
                    },
                });
            } catch (err) {
                let friendlyMsg = "Microphone access is required to speak.";
                let code = "MIC_PERMISSION_DENIED";
                if (err.name === "NotAllowedError" || err.name === "PermissionDeniedError") {
                    friendlyMsg = "Microphone permission was denied. Please allow microphone access in your browser settings (click lock icon in address bar) or use text chat.";
                } else if (err.name === "NotFoundError" || err.name === "DevicesNotFoundError") {
                    friendlyMsg = "No microphone was found on your device. You can type your question in the text box.";
                    code = "NO_MIC_FOUND";
                } else if (err.name === "NotReadableError") {
                    friendlyMsg = "Microphone is already in use by another application.";
                    code = "MIC_BUSY";
                }
                if (options.onError) {
                    options.onError({ error_code: code, message: friendlyMsg, rawError: err });
                }
                return;
            }

            try {
                const mimeType = getBestSupportedMimeType();
                audioChunks = [];
                mediaRecorder = mimeType
                    ? new MediaRecorder(recordStream, { mimeType })
                    : new MediaRecorder(recordStream);

                mediaRecorder.ondataavailable = (e) => {
                    if (e.data && e.data.size > 0) {
                        audioChunks.push(e.data);
                    }
                };

                recordDurationSec = 0;
                if (recordTimer) clearInterval(recordTimer);
                recordTimer = setInterval(() => {
                    recordDurationSec += 1;
                    if (options.onTick) {
                        options.onTick(recordDurationSec, MAX_RECORD_SECONDS);
                    }
                    if (recordDurationSec >= MAX_RECORD_SECONDS) {
                        // Automatically stop recording at 30 seconds
                        KrishiGnaniVoice.stopRecording();
                    }
                }, 1000);

                mediaRecorder.start(250); // collect chunks every 250ms
                if (options.onStart) options.onStart();
            } catch (err) {
                if (options.onError) {
                    options.onError({
                        error_code: "RECORDER_INIT_FAILED",
                        message: "Could not start audio recorder. Falling back to browser speech recognition.",
                    });
                }
                fallbackBrowserRecognition({
                    language: options.language || "hi-IN",
                    onStart: options.onStart,
                    onSuccess: options.onSuccess,
                    onError: options.onError,
                    onEnd: options.onEnd,
                });
            }
        },

        /**
         * Stops recording and returns the recorded audio Blob
         * @returns {Promise<Blob>}
         */
        stopRecording() {
            return new Promise((resolve) => {
                if (recordTimer) {
                    clearInterval(recordTimer);
                    recordTimer = null;
                }

                if (!mediaRecorder || mediaRecorder.state === "inactive") {
                    if (recordStream) {
                        recordStream.getTracks().forEach((t) => t.stop());
                        recordStream = null;
                    }
                    resolve(null);
                    return;
                }

                mediaRecorder.onstop = () => {
                    const mimeType = mediaRecorder.mimeType || "audio/webm";
                    const blob = new Blob(audioChunks, { type: mimeType });
                    audioChunks = [];

                    if (recordStream) {
                        recordStream.getTracks().forEach((t) => t.stop());
                        recordStream = null;
                    }
                    resolve(blob);
                };

                try {
                    mediaRecorder.stop();
                } catch (e) {
                    if (recordStream) {
                        recordStream.getTracks().forEach((t) => t.stop());
                        recordStream = null;
                    }
                    resolve(null);
                }
            });
        },

        /**
         * Cancels recording without processing
         */
        cancelRecording() {
            if (recordTimer) {
                clearInterval(recordTimer);
                recordTimer = null;
            }
            if (mediaRecorder && mediaRecorder.state !== "inactive") {
                try { mediaRecorder.stop(); } catch (e) {}
            }
            if (recordStream) {
                recordStream.getTracks().forEach((t) => t.stop());
                recordStream = null;
            }
            audioChunks = [];
        },

        /**
         * Transcribes audio using Gnani Prisma v3.0 REST API
         * @param {Blob} audioBlob
         * @param {Object} options: { language: 'hi-IN'|'en-IN'|'indic-auto', model: 'prisma-v3.0' }
         */
        async transcribe(audioBlob, options = {}) {
            if (!audioBlob || audioBlob.size < 64) {
                throw new Error("Recorded audio is too short or empty.");
            }

            const langCode = options.language || "hi-IN,en-IN";
            const model = options.model || "prisma-v3.0";
            const base = getApiBaseUrl();

            // Determine file extension from blob type
            let ext = "wav";
            if (audioBlob.type.includes("webm")) ext = "webm";
            else if (audioBlob.type.includes("ogg")) ext = "ogg";
            else if (audioBlob.type.includes("mp4")) ext = "m4a";

            const formData = new FormData();
            formData.append("audio_file", audioBlob, `recording.${ext}`);
            formData.append("model", model);
            formData.append("language_code", langCode);
            formData.append("format", "codemix");

            let res;
            try {
                res = await fetch(`${base}/api/krishisathi/stt`, {
                    method: "POST",
                    body: formData,
                });
            } catch (err) {
                throw new Error("Network error connecting to Gnani Speech-to-Text service.");
            }

            const data = await res.json().catch(() => ({}));
            if (!res.ok || data.status === "error") {
                const err = new Error(data.message || `Gnani STT error (status ${res.status})`);
                err.errorCode = data.error_code;
                err.statusCode = res.status;
                throw err;
            }

            return {
                status: "success",
                transcript: data.transcript || "",
                model: data.model || model,
                detected_language_code: data.detected_language_code || langCode,
                processing_time: data.processing_time,
                provider: "Gnani.ai Prisma v3.0",
            };
        },

        /**
         * Synthesizes and plays text using Gnani Timbre v2.5 Text-to-Speech
         * @param {string} text
         * @param {Object} options: { language: 'hi-IN'|'en-IN', voice: 'Nalini'|'Deepak', gender: 'female'|'male', onStart, onEnd, onError }
         */
        async speak(text, options = {}) {
            this.stopPlayback();

            const cleanText = cleanTextForSpeech(text);
            if (!cleanText) return;

            const lang = options.language || (cleanText.match(/[\u0900-\u097F]/) ? "hi-IN" : "en-IN");
            const gender = options.gender || "female";
            const voice = options.voice || (gender === "male" ? "Deepak" : "Nalini");
            const speed = options.speed || 1.0;
            const base = getApiBaseUrl();

            try {
                const res = await fetch(`${base}/api/krishisathi/tts`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        text: cleanText,
                        language: lang,
                        voice: voice,
                        gender: gender,
                        model: "timbre-v2.5",
                        speed: speed,
                    }),
                });

                if (!res.ok) {
                    const errData = await res.json().catch(() => ({}));
                    console.warn("Gnani Timbre TTS unavailable, falling back to browser voice:", errData.message || res.status);
                    fallbackBrowserSpeak(cleanText, lang, options.onEnd);
                    if (options.onStart) options.onStart({ provider: "Browser Web Speech API" });
                    return;
                }

                const audioBlob = await res.blob();
                const audioUrl = URL.createObjectURL(audioBlob);
                const audio = new Audio(audioUrl);
                currentAudioElement = audio;

                audio.onplay = () => {
                    isSpeakingAudio = true;
                    if (options.onStart) {
                        options.onStart({
                            provider: "Gnani.ai Timbre v2.5",
                            voice: res.headers.get("X-Gnani-Voice") || voice,
                            model: res.headers.get("X-Gnani-Model") || "timbre-v2.5",
                        });
                    }
                };

                audio.onended = () => {
                    isSpeakingAudio = false;
                    URL.revokeObjectURL(audioUrl);
                    currentAudioElement = null;
                    if (options.onEnd) options.onEnd();
                };

                audio.onerror = (e) => {
                    console.warn("Audio playback error, trying browser fallback:", e);
                    isSpeakingAudio = false;
                    URL.revokeObjectURL(audioUrl);
                    currentAudioElement = null;
                    fallbackBrowserSpeak(cleanText, lang, options.onEnd);
                };

                await audio.play();
            } catch (err) {
                console.warn("Gnani TTS network error, using browser speech fallback:", err);
                fallbackBrowserSpeak(cleanText, lang, options.onEnd);
                if (options.onStart) options.onStart({ provider: "Browser Web Speech API" });
            }
        },
    };

    // Export to browser global and CommonJS / ES module
    if (typeof module !== "undefined" && module.exports) {
        module.exports = KrishiGnaniVoice;
    }
    if (typeof exports !== "undefined") {
        exports.KrishiGnaniVoice = KrishiGnaniVoice;
        exports.default = KrishiGnaniVoice;
    }
    global.KrishiGnaniVoice = KrishiGnaniVoice;

})(typeof window !== "undefined" ? window : globalThis);
