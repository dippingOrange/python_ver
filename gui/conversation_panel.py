import tkinter as tk
from tkinter import ttk
import threading
from pathlib import Path
from model.scenario import Scenario
from service.conversation_service import ConversationService
from service.audio_recorder import AudioRecorder
from service.speech_to_text import SpeechToTextService
from service.text_to_speech import TextToSpeechService


class ConversationPanel(ttk.Frame):
    SPINNER_CHARS = ["|", "/", "—", "\\"]

    def __init__(
        self, parent, conversation_service: ConversationService, on_back
    ):
        super().__init__(parent)
        self.conversation_service = conversation_service
        self.recorder = AudioRecorder()
        self.stt = SpeechToTextService()
        self.tts = TextToSpeechService()
        self.on_back = on_back

        self._conversation_active = False
        self._last_ai_response = ""
        self._last_recording_file = None
        self._text_hidden = False
        self._spinner_idx = 0
        self._spinner_job = None
        self._typewriter_job = None
        self._loading_mark = ""
        self._build_ui()

    def _build_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # Top controls
        top = ttk.Frame(self)
        top.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        top.columnconfigure(0, weight=1)

        # Scenario row
        scenario_row = ttk.Frame(top)
        scenario_row.pack(fill="x", pady=2)

        ttk.Label(scenario_row, text="Scenario:").pack(side="left", padx=2)
        self.scenario_var = tk.StringVar()
        self.scenario_box = ttk.Combobox(
            scenario_row,
            textvariable=self.scenario_var,
            values=[s.label for s in Scenario],
            state="readonly",
            width=15,
        )
        self.scenario_box.current(0)
        self.scenario_box.pack(side="left", padx=2)

        self.start_btn = ttk.Button(
            scenario_row,
            text="Start Conversation",
            command=self._handle_start,
            style="Accent.TButton",
        )
        self.start_btn.pack(side="left", padx=(10, 2))

        ttk.Label(scenario_row, text="Length:").pack(side="left", padx=(10, 2))
        self.length_var = tk.StringVar(value="Normal")
        length_box = ttk.Combobox(
            scenario_row,
            textvariable=self.length_var,
            values=ConversationService.LENGTH_LABELS,
            state="readonly",
            width=8,
        )
        length_box.current(0)
        length_box.pack(side="left", padx=2)
        length_box.bind(
            "<<ComboboxSelected>>",
            lambda e: self.conversation_service.set_response_length(
                ConversationService.LENGTH_LABELS.index(self.length_var.get())
            ),
        )

        # TTS row
        tts_row = ttk.Frame(top)
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

        self.hide_btn = ttk.Button(
            tts_row, text="🙈 Hide Text", command=self._toggle_hide_text
        )
        self.hide_btn.pack(side="left", padx=(10, 2))

        # Chat area
        self.chat_text = tk.Text(
            self,
            wrap="word",
            font=("Arial", 13),
            state="disabled",
        )
        self.chat_text.grid(
            row=1, column=0, sticky="nsew", padx=10, pady=5
        )

        # Scrollbar for chat
        scrollbar = ttk.Scrollbar(self, command=self.chat_text.yview)
        scrollbar.grid(row=1, column=1, sticky="ns", pady=5)
        self.chat_text.configure(yscrollcommand=scrollbar.set)

        # Bottom controls
        bottom = ttk.Frame(self)
        bottom.grid(row=2, column=0, columnspan=2, sticky="ew", padx=10, pady=(5, 10))

        input_row = ttk.Frame(bottom)
        input_row.pack(fill="x")

        ttk.Label(input_row, text="🎙️ Press to speak:").pack(side="left")
        self.record_btn = ttk.Button(
            input_row, text="🎤 Record", command=self._handle_record, state="disabled"
        )
        self.record_btn.pack(side="left", padx=5)

        self.replay_btn = ttk.Button(
            input_row,
            text="🔁 Replay",
            command=self._replay,
            state="disabled",
        )
        self.replay_btn.pack(side="left", padx=2)

        self.summary_btn = ttk.Button(
            input_row,
            text="Summary",
            command=self._handle_summary,
            state="disabled",
        )
        self.summary_btn.pack(side="left", padx=2)

        ttk.Button(input_row, text="Back", command=self._handle_back).pack(
            side="right", padx=2
        )

    # ---------- helpers ----------

    def _toggle_tts(self):
        self.tts.set_enabled(not self.tts.is_enabled())
        self.tts_btn.configure(
            text="🔊 TTS" if self.tts.is_enabled() else "🔇 TTS"
        )

    def _toggle_hide_text(self):
        if self._text_hidden:
            self.chat_text.configure(foreground="black")
            self.hide_btn.configure(text="🙈 Hide Text")
            self._text_hidden = False
        else:
            self.chat_text.configure(foreground="white")
            self.hide_btn.configure(text="🙉 Show Text")
            self._text_hidden = True

    def _replay(self):
        if self._last_ai_response:
            self.tts.speak_async(self._last_ai_response)

    def _handle_back(self):
        self.after(0, self.on_back)

    def _show_loading(self):
        self.chat_text.configure(state="normal")
        self._loading_mark = self.chat_text.index("end-1c")
        self.chat_text.insert("end", "AI: |")
        self.chat_text.configure(state="disabled")
        self.chat_text.see("end")
        self._spinner_idx = 0
        self._animate_spinner()

    def _animate_spinner(self):
        if not self._conversation_active and self._spinner_job is None:
            return
        self._spinner_idx = (self._spinner_idx + 1) % len(self.SPINNER_CHARS)
        self.chat_text.configure(state="normal")
        try:
            pos = f"{self._loading_mark}+4c"
            self.chat_text.delete(pos, f"{pos}+1c")
            self.chat_text.insert(pos, self.SPINNER_CHARS[self._spinner_idx])
        except Exception:
            pass
        self.chat_text.configure(state="disabled")
        self._spinner_job = self.after(200, self._animate_spinner)

    def _hide_loading(self, response):
        if self._spinner_job:
            self.after_cancel(self._spinner_job)
            self._spinner_job = None
        self.chat_text.configure(state="normal")
        try:
            chat_start = self._loading_mark
            chat_end = self.chat_text.index("end-1c")
            self.chat_text.delete(chat_start, chat_end)
        except Exception:
            pass
        self._typewrite(response)

    def _typewrite(self, text):
        if self._typewriter_job:
            self.after_cancel(self._typewriter_job)
            self._typewriter_job = None

        self.chat_text.configure(state="normal")
        if not self.chat_text.get("end-2c", "end-1c") == "\n":
            self.chat_text.insert("end", "\n")
        self.chat_text.insert("end", "AI: ")
        self._loading_mark = self.chat_text.index("end-1c")
        self._type_text = text
        self._type_pos = 0
        self.chat_text.configure(state="disabled")

        def start_typing():
            self._typewriter_job = self.after(25, self._type_char)

        self.after(1500, start_typing)

    def _type_char(self):
        if self._type_pos < len(self._type_text):
            self.chat_text.configure(state="normal")
            self.chat_text.insert("end", self._type_text[self._type_pos])
            self._type_pos += 1
            self.chat_text.configure(state="disabled")
            self.chat_text.see("end")
            self._typewriter_job = self.after(25, self._type_char)
        else:
            self.chat_text.configure(state="normal")
            self.chat_text.insert("end", "\n\n")
            self.chat_text.configure(state="disabled")
            self.chat_text.see("end")
            self._typewriter_job = None

    # ---------- handlers ----------

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
                self._append_chat(f"Error: {e}\n")

    def _on_transcription_done(self, text):
        self.record_btn.configure(text="🎤 Record", state="normal")
        self._append_chat(f"You: {text}\n")
        self._auto_send(text)

    def _on_transcription_error(self, msg):
        self._append_chat(f"Transcription failed: {msg}\n")
        self.record_btn.configure(text="🎤 Record", state="normal")

    def _auto_send(self, user_input):
        if not user_input.strip() or not self._conversation_active:
            return

        self._show_loading()
        wav = (
            self._last_recording_file
            if self._last_recording_file
            and Path(self._last_recording_file).exists()
            else None
        )

        def do_send():
            try:
                response = self.conversation_service.send_message(user_input, wav)
                self.after(0, lambda: self._on_response(response, wav))
            except Exception as e:
                self.after(0, lambda: self._on_response_error(str(e)))

        threading.Thread(target=do_send, daemon=True).start()

    def _on_response(self, response, wav):
        if wav and self.conversation_service.has_scored_turns():
            self.summary_btn.configure(state="normal")
        self._hide_loading(response)
        self._last_ai_response = response
        self.replay_btn.configure(state="normal")
        self.tts.speak_async(response)
        self.record_btn.configure(state="normal")

    def _on_response_error(self, msg):
        self._hide_loading(f"Error: {msg}")
        self.record_btn.configure(state="normal")

    def _handle_start(self):
        scenario_name = self.scenario_var.get()
        scenario = next(s for s in Scenario if s.label == scenario_name)
        self.conversation_service.set_scenario(scenario)
        self._conversation_active = True
        self.chat_text.configure(state="normal")
        self.chat_text.delete("1.0", "end")
        self.chat_text.configure(state="disabled")
        self.scenario_box.configure(state="disabled")
        self.start_btn.configure(state="disabled")
        self.record_btn.configure(state="normal")
        self._show_loading()

        def do_start():
            try:
                response = self.conversation_service.start_conversation()
                self.after(0, lambda: self._on_start_response(response))
            except Exception as e:
                self.after(0, lambda: self._on_response_error(str(e)))

        threading.Thread(target=do_start, daemon=True).start()

    def _on_start_response(self, response):
        self._hide_loading(response)
        self._last_ai_response = response
        self.replay_btn.configure(state="normal")
        self.tts.speak_async(response)

    def _handle_summary(self):
        self.summary_btn.configure(state="disabled")
        self._append_chat("\n--- Pronunciation Summary ---\n")
        self._append_chat("Generating...\n")

        def do_summary():
            try:
                summary = self.conversation_service.get_conversation_summary()
                self.after(0, lambda: self._append_chat(summary + "\n\n"))
            except Exception as e:
                self.after(0, lambda: self._append_chat(f"Error: {e}\n"))

        threading.Thread(target=do_summary, daemon=True).start()

    def _append_chat(self, text):
        self.chat_text.configure(state="normal")
        self.chat_text.insert("end", text)
        self.chat_text.configure(state="disabled")
        self.chat_text.see("end")

    def reset(self):
        self._conversation_active = False
        self.conversation_service.reset()
        self.scenario_box.configure(state="readonly")
        self.start_btn.configure(state="normal")
        self.record_btn.configure(state="disabled")
        self.record_btn.configure(text="🎤 Record")
        self.summary_btn.configure(state="disabled")
        self.replay_btn.configure(state="disabled")
        self.chat_text.configure(state="normal")
        self.chat_text.delete("1.0", "end")
        self.chat_text.configure(state="disabled")
        self._last_recording_file = None
        self._last_ai_response = ""
        if self._spinner_job:
            self.after_cancel(self._spinner_job)
            self._spinner_job = None
        if self._typewriter_job:
            self.after_cancel(self._typewriter_job)
            self._typewriter_job = None
