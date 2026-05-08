import tkinter as tk
from tkinter import ttk
import threading
from pathlib import Path
from service.reading_service import ReadingService
from service.audio_recorder import AudioRecorder
from service.speech_to_text import SpeechToTextService
from service.text_to_speech import TextToSpeechService


class ReadingPanel(ttk.Frame):
    def __init__(self, parent, reading_service: ReadingService, on_back):
        super().__init__(parent)
        self.reading_service = reading_service
        self.recorder = AudioRecorder()
        self.stt = SpeechToTextService()
        self.tts = TextToSpeechService()
        self.on_back = on_back
        self._current_passage = ""
        self._last_spoken_text = ""
        self._last_recording_file = None
        self._build_ui()
        self._load_new_passage()

    def _build_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # Top — passage
        top = ttk.LabelFrame(self, text="Read the following passage:", padding=5)
        top.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        top.columnconfigure(0, weight=1)
        self.passage_text = tk.Text(
            top, height=6, wrap="word", font=("Arial", 13), state="disabled"
        )
        self.passage_text.grid(row=0, column=0, sticky="ew")

        # Center — input + result
        center = ttk.Frame(self)
        center.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        center.columnconfigure(0, weight=1)
        center.rowconfigure(0, weight=0)
        center.rowconfigure(1, weight=1)
        center.rowconfigure(2, weight=0)

        ttk.Label(center, text="🎙️ Your Reading:", font=("Arial", 11, "bold")).grid(
            row=0, column=0, sticky="w", pady=(0, 2)
        )
        self.input_text = tk.Text(
            center, height=4, wrap="word", font=("Arial", 13)
        )
        self.input_text.grid(row=1, column=0, sticky="nsew")

        result_frame = ttk.LabelFrame(center, text="🧠 AI Feedback:", padding=3)
        result_frame.grid(row=2, column=0, sticky="ew", pady=(5, 0))
        result_frame.columnconfigure(0, weight=1)
        self.result_text = tk.Text(
            result_frame,
            height=6,
            wrap="word",
            font=("Arial", 13),
            state="disabled",
        )
        self.result_text.grid(row=0, column=0, sticky="ew")

        # Pronunciation detail (hidden by default)
        self.pron_detail_text = tk.Text(
            center,
            height=2,
            wrap="word",
            font=("Arial", 11),
            state="disabled",
            bg="#F5F5FF",
        )

        # Bottom — controls
        bottom = ttk.Frame(self)
        bottom.grid(row=2, column=0, sticky="ew", padx=10, pady=(5, 10))

        # TTS row
        tts_row = ttk.Frame(bottom)
        tts_row.pack(fill="x", pady=2)

        self.tts_btn = ttk.Button(
            tts_row,
            text="🔊 TTS",
            command=self._toggle_tts,
            width=10,
        )
        self.tts_btn.pack(side="left", padx=2)

        ttk.Label(tts_row, text="Voice:").pack(side="left", padx=(10, 2))
        self.voice_var = tk.StringVar(value=self.tts.get_voice_names()[0])
        voice_box = ttk.Combobox(
            tts_row,
            textvariable=self.voice_var,
            values=self.tts.get_voice_names(),
            state="readonly",
            width=20,
        )
        voice_box.pack(side="left", padx=2)
        voice_box.bind(
            "<<ComboboxSelected>>",
            lambda e: self.tts.set_voice(self.tts.VOICES[self.voice_var.get()]),
        )

        ttk.Label(tts_row, text="Speed:").pack(side="left", padx=(10, 2))
        self.speed_var = tk.StringVar(value="1.0x")
        speed_box = ttk.Combobox(
            tts_row,
            textvariable=self.speed_var,
            values=self.tts.SPEED_LABELS,
            state="readonly",
            width=6,
        )
        speed_box.pack(side="left", padx=2)
        speed_box.bind(
            "<<ComboboxSelected>>",
            lambda e: self.tts.set_speed(
                self.tts.SPEEDS[self.tts.SPEED_LABELS.index(self.speed_var.get())]
            ),
        )

        self.replay_btn = ttk.Button(
            tts_row, text="🔁 Replay", command=self._replay, state="disabled"
        )
        self.replay_btn.pack(side="left", padx=(10, 2))

        # Action row
        action_row = ttk.Frame(bottom)
        action_row.pack(fill="x", pady=(5, 0))

        self.record_btn = ttk.Button(
            action_row, text="🎤 Record", command=self._handle_record
        )
        self.record_btn.pack(side="left", padx=2)

        ttk.Button(action_row, text="New Passage", command=self._load_new_passage).pack(
            side="left", padx=2
        )

        self.evaluate_btn = ttk.Button(
            action_row, text="Evaluate", command=self._handle_evaluate
        )
        self.evaluate_btn.pack(side="left", padx=2)

        ttk.Button(action_row, text="Back", command=self.on_back).pack(
            side="right", padx=2
        )

    def _toggle_tts(self):
        self.tts.set_enabled(not self.tts.is_enabled())
        self.tts_btn.configure(
            text="🔊 TTS" if self.tts.is_enabled() else "🔇 TTS"
        )

    def _replay(self):
        if self._last_spoken_text:
            self.tts.speak_async(self._last_spoken_text)

    def _load_new_passage(self):
        passage = self.reading_service.get_random_passage()
        if passage:
            self._current_passage = passage
            self.passage_text.configure(state="normal")
            self.passage_text.delete("1.0", "end")
            self.passage_text.insert("1.0", passage)
            self.passage_text.configure(state="disabled")
            self.input_text.delete("1.0", "end")
            self.result_text.configure(state="normal")
            self.result_text.delete("1.0", "end")
            self.result_text.configure(state="disabled")
            self._last_recording_file = None
        else:
            self.passage_text.configure(state="normal")
            self.passage_text.delete("1.0", "end")
            self.passage_text.insert("1.0", "No texts found in texts.txt")
            self.passage_text.configure(state="disabled")

    def _handle_record(self):
        if self.recorder.is_recording():
            self.recorder.stop_recording()
            self._last_recording_file = self.recorder.get_temp_file()
            self.record_btn.configure(text="🎤 Transcribing...", state="disabled")

            def do_transcribe():
                try:
                    text = self.stt.transcribe(self.recorder.get_temp_file())
                    self.after(0, lambda: self._on_transcription_done(text))
                except Exception as e:
                    self.after(0, lambda: self._on_transcription_error(str(e)))

            threading.Thread(target=do_transcribe, daemon=True).start()
        else:
            try:
                self.recorder.start_recording()
                self.record_btn.configure(text="🔴 Stop")
            except Exception as e:
                self._show_error(f"Could not start recording: {e}")

    def _on_transcription_done(self, text):
        self.input_text.delete("1.0", "end")
        self.input_text.insert("1.0", text)
        self.record_btn.configure(text="🎤 Record", state="normal")

    def _on_transcription_error(self, msg):
        self._show_error(f"Transcription failed: {msg}")
        self.record_btn.configure(text="🎤 Record", state="normal")

    def _handle_evaluate(self):
        user_input = self.input_text.get("1.0", "end-1c").strip()
        if not user_input:
            self._show_error("Please type the passage first.")
            return

        self.evaluate_btn.configure(state="disabled")
        self.result_text.configure(state="normal")
        self.result_text.delete("1.0", "end")
        self.result_text.insert("1.0", "Evaluating...")
        self.result_text.configure(state="disabled")

        wav = (
            self._last_recording_file
            if self._last_recording_file
            and Path(self._last_recording_file).exists()
            else None
        )

        def do_evaluate():
            try:
                result = self.reading_service.evaluate(
                    self._current_passage, user_input, wav
                )
                self.after(0, lambda: self._on_evaluate_done(result))
            except Exception as e:
                self.after(0, lambda: self._on_evaluate_error(str(e)))

        threading.Thread(target=do_evaluate, daemon=True).start()

    def _on_evaluate_done(self, result):
        text = f"Score: {result.score}/100\nFeedback: {result.feedback}\nTips: {result.tips}"
        self.result_text.configure(state="normal")
        self.result_text.delete("1.0", "end")
        self.result_text.insert("1.0", text)
        self.result_text.configure(state="disabled")

        # Show pronunciation detail if available
        if hasattr(self, "pron_detail_text"):
            self.pron_detail_text.grid_forget()

        if result.pronunciation_score > 0:
            detail = (
                f"Pronunciation: {result.pronunciation_score}/100  "
                f"Fluency: {result.fluency_score}/100  "
                f"Completeness: {result.completeness_score}/100"
            )
            self.pron_detail_text.configure(state="normal")
            self.pron_detail_text.delete("1.0", "end")
            self.pron_detail_text.insert("1.0", detail)
            self.pron_detail_text.configure(state="disabled")
            # Grid below the result frame
            info = self.result_text.grid_info()
            if info:
                self.pron_detail_text.grid(
                    row=info["row"] + 1,
                    column=info["column"],
                    sticky="ew",
                    pady=(3, 0),
                )

        self._last_spoken_text = (
            f"Your score is {result.score} out of 100. {result.feedback}. "
            f"Tip: {result.tips}"
        )
        self.replay_btn.configure(state="normal")
        self.tts.speak_async(self._last_spoken_text)
        self.evaluate_btn.configure(state="normal")

    def _on_evaluate_error(self, msg):
        self.result_text.configure(state="normal")
        self.result_text.delete("1.0", "end")
        self.result_text.insert("1.0", f"Error: {msg}")
        self.result_text.configure(state="disabled")
        self.evaluate_btn.configure(state="normal")

    def _show_error(self, msg):
        self.result_text.configure(state="normal")
        self.result_text.delete("1.0", "end")
        self.result_text.insert("1.0", msg)
        self.result_text.configure(state="disabled")
