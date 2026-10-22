"""Text-to-Speech (TTS) module for KrishiSathi supporting Hindi pronunciation."""

import io
import base64
from typing import Optional


def get_hindi_audio_bytes(text: str) -> Optional[bytes]:
    """Attempts to synthesize Hindi audio using gTTS if installed.

    Returns raw mp3 bytes or None if gTTS is not available.
    """
    try:
        from gtts import gTTS

        tts = gTTS(text=text, lang="hi", slow=False)
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        return fp.read()
    except (ImportError, Exception):
        return None


def get_browser_speech_html(text: str, auto_play: bool = True) -> str:
    """Generates an accessible HTML/JS component leveraging the browser's

    native Web Speech API (SpeechSynthesis) in Hindi (hi-IN).
    Requires zero external pip packages and zero network latency.
    """
    escaped_text = text.replace('"', '\\"').replace("\n", " ")
    autoplay_code = (
        'window.speakKrishiSathi();' if auto_play else ''
    )

    return f"""
    <div style="padding: 12px; background-color: #f0fdf4; border-left: 4px solid #16a34a; border-radius: 6px; margin: 10px 0;">
        <div style="display: flex; align-items: center; justify-content: space-between;">
            <div style="font-size: 15px; color: #166534; font-weight: 600;">
                🔊 कृषिसाथी आवाज (KrishiSathi Voice Output)
            </div>
            <button onclick="window.speakKrishiSathi()" style="
                background-color: #16a34a;
                color: white;
                border: none;
                padding: 6px 14px;
                border-radius: 20px;
                cursor: pointer;
                font-weight: 500;
                font-size: 13px;
                display: flex;
                align-items: center;
                gap: 6px;
            ">
                ▶ बोलकर सुनाएं (Listen Aloud)
            </button>
        </div>
        <p style="margin: 8px 0 0 0; color: #15803d; font-size: 14px; line-height: 1.5;">{escaped_text}</p>
    </div>

    <script>
    window.speakKrishiSathi = function() {{
        if ('speechSynthesis' in window) {{
            window.speechSynthesis.cancel();
            const utterance = new SpeechSynthesisUtterance("{escaped_text}");
            utterance.lang = 'hi-IN';
            utterance.rate = 0.95; // slightly slower for rural clarity
            utterance.pitch = 1.0;

            // Select Hindi voice if available
            const voices = window.speechSynthesis.getVoices();
            const hindiVoice = voices.find(v => v.lang.includes('hi') || v.lang.includes('IN'));
            if (hindiVoice) {{
                utterance.voice = hindiVoice;
            }}

            window.speechSynthesis.speak(utterance);
        }} else {{
            console.warn("Web Speech API not supported in this browser.");
        }}
    }};
    {autoplay_code}
    </script>
    """
