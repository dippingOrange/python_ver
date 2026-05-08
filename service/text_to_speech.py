import subprocess
import threading
from collections import OrderedDict


class TextToSpeechService:
    VOICES = OrderedDict(
        [
            ("Aria (女声, 自信)", "en-US-AriaNeural"),
            ("Jenny (女声, 友善)", "en-US-JennyNeural"),
            ("Emma (女声, 轻快)", "en-US-EmmaMultilingualNeural"),
            ("Guy (男声, 热情)", "en-US-GuyNeural"),
            ("Christopher (男声, 权威)", "en-US-ChristopherNeural"),
            ("Andrew (男声, 温暖)", "en-US-AndrewMultilingualNeural"),
            ("Brian (男声, 随意)", "en-US-BrianMultilingualNeural"),
        ]
    )

    SPEEDS = [0.5, 0.75, 1.0, 1.25, 1.5]
    SPEED_LABELS = ["0.5x", "0.75x", "1.0x", "1.25x", "1.5x"]

    def __init__(self):
        self.enabled = True
        self.voice = "en-US-AriaNeural"
        self.speed = 1.0
        self._warmed_up = False

    def get_voice_names(self) -> list:
        return list(self.VOICES.keys())

    def set_voice(self, voice_id: str):
        self.voice = voice_id

    def set_speed(self, speed: float):
        self.speed = speed

    def set_enabled(self, enabled: bool):
        self.enabled = enabled

    def is_enabled(self) -> bool:
        return self.enabled

    def warm_up(self):
        if self._warmed_up:
            return
        self._warmed_up = True
        try:
            subprocess.run(
                ["edge-playback", "--text", " . "],
                capture_output=True,
                timeout=5,
            )
        except Exception:
            pass

    def speak(self, text: str):
        if not self.enabled or not text or not text.strip():
            return
        if not self._warmed_up:
            self.warm_up()

        # Pad beginning to avoid audio cutoff
        text = "... " + text
        if len(text) > 500:
            text = text[:497] + "..."

        try:
            cmd = ["edge-playback", "--voice", self.voice]
            if self.speed != 1.0:
                rate_pct = round((self.speed - 1.0) * 100)
                cmd += ["--rate", f"{'+' if rate_pct >= 0 else ''}{rate_pct}%"]
            cmd += ["--text", text]
            subprocess.run(cmd, capture_output=True, timeout=60)
        except Exception:
            pass

    def speak_async(self, text: str):
        threading.Thread(target=self.speak, args=(text,), daemon=True).start()
