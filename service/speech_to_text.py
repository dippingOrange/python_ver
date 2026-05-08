import subprocess
from pathlib import Path


class SpeechToTextService:
    WHISPER_EXE = "STT/whisper-cli.exe"
    MODEL = "STT/ggml-base.bin"
    # Fallback: look in parent Java project
    ALT_WHISPER_EXE = "../Eng_verbal_practice_tool/STT/whisper-cli.exe"
    ALT_MODEL = "../Eng_verbal_practice_tool/STT/ggml-base.bin"

    def _resolve_path(self, default: str, alt: str) -> str:
        if Path(default).exists():
            return default
        if Path(alt).exists():
            return alt
        return default  # Let it fail with a clear error

    def transcribe(self, wav_path: str) -> str:
        exe = self._resolve_path(self.WHISPER_EXE, self.ALT_WHISPER_EXE)
        model = self._resolve_path(self.MODEL, self.ALT_MODEL)

        if not Path(exe).exists():
            raise RuntimeError(f"whisper-cli.exe not found at {exe}")
        if not Path(model).exists():
            raise RuntimeError(f"Model file not found at {model}")

        abs_wav = str(Path(wav_path).resolve())

        proc = subprocess.run(
            [exe, "-f", abs_wav, "-m", model, "-l", "en", "-otxt", "-t", "4"],
            capture_output=True,
            text=True,
            cwd=".",
        )

        if proc.returncode != 0:
            raise RuntimeError(f"whisper-cli exited with code {proc.returncode}")

        txt_path = Path(abs_wav + ".txt")
        if not txt_path.exists():
            raise RuntimeError("Transcription output file not found")

        text = txt_path.read_text(encoding="utf-8").strip()
        txt_path.unlink(missing_ok=True)  # cleanup
        return text
