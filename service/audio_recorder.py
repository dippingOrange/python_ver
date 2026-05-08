import threading
import wave
import queue
import sounddevice as sd
import numpy as np
from pathlib import Path


class AudioRecorder:
    SAMPLE_RATE = 16000
    SAMPLE_BITS = 16
    CHANNELS = 1
    TEMP_FILE = "record_temp.wav"

    def __init__(self):
        self._recording = False
        self._thread = None
        self._audio_data = None

    def is_recording(self) -> bool:
        return self._recording

    def get_temp_file(self) -> str:
        return self.TEMP_FILE

    def start_recording(self):
        if self._recording:
            return

        self._audio_data = None
        self._recording = True
        self._thread = threading.Thread(target=self._record_loop, daemon=True)
        self._thread.start()

    def _record_loop(self):
        try:
            q = queue.Queue()

            def callback(indata, frames, time, status):
                q.put(indata.copy())

            with sd.InputStream(
                samplerate=self.SAMPLE_RATE,
                channels=self.CHANNELS,
                dtype="int16",
                callback=callback,
                blocksize=1024,
            ):
                while self._recording:
                    sd.sleep(100)

            # Drain remaining data from queue
            frames = []
            while not q.empty():
                frames.append(q.get_nowait())

            if frames:
                self._audio_data = np.concatenate(frames, axis=0)
                self._save_wav()

        except Exception as e:
            print(f"Recording error: {e}")
            self._recording = False

    def stop_recording(self):
        self._recording = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=3)

    def _save_wav(self):
        if self._audio_data is None or len(self._audio_data) == 0:
            return

        path = Path(self.TEMP_FILE)
        with wave.open(str(path), "wb") as wf:
            wf.setnchannels(self.CHANNELS)
            wf.setsampwidth(self.SAMPLE_BITS // 8)
            wf.setframerate(self.SAMPLE_RATE)
            wf.writeframes(self._audio_data.tobytes())
