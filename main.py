import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from pathlib import Path

from service.ai_service import AiService
from service.alibaba_asr_service import AlibabaAsrService
from service.reading_service import ReadingService
from service.conversation_service import ConversationService
from gui.setup_panel import SetupPanel
from gui.home_panel import HomePanel
from gui.reading_panel import ReadingPanel
from gui.conversation_panel import ConversationPanel


class EnglishSpeakerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("English Speaking Practice")
        self.geometry("700x600")
        self.minsize(600, 500)
        self._apply_warm_theme()

        self.ai_service = None
        self.alibaba_asr = None
        self.reading_service = None
        self.conversation_service = None

        self._container = ttk.Frame(self)
        self._container.pack(fill="both", expand=True)

        self._panels = {}
        self._conversation_panel = None

        if self._is_config_complete():
            self._init_services()
            self._create_panels()
            self._show_panel("home")
        else:
            self._show_setup()

    # ---------- theme ----------

    def _apply_warm_theme(self):
        style = ttk.Style()
        style.theme_use("clam")

        # Colors
        CREAM = "#FFF8F0"
        WARM_ORANGE = "#F4976C"
        WARM_ORANGE_DARK = "#E8734A"
        WARM_ORANGE_HOVER = "#F7A88B"
        DARK_BROWN = "#3D2B1F"
        LIGHT_WARM = "#FDDCB5"

        self.configure(bg=CREAM)

        style.configure(".", background=CREAM, foreground=DARK_BROWN)
        style.configure("TFrame", background=CREAM)
        style.configure("TLabel", background=CREAM, foreground=DARK_BROWN)
        style.configure("TLabelframe", background=CREAM)
        style.configure("TLabelframe.Label", background=CREAM, foreground=DARK_BROWN)
        style.configure("TSeparator", background="#D5C4B0")
        style.configure("TEntry", fieldbackground="white", foreground=DARK_BROWN)

        # Accent button style
        style.configure(
            "Accent.TButton",
            background=WARM_ORANGE,
            foreground="white",
            borderwidth=0,
            focuscolor="none",
            relief="flat",
            padding=(15, 6),
            font=("Arial", 11),
        )
        style.map(
            "Accent.TButton",
            background=[("active", WARM_ORANGE_HOVER), ("disabled", "#CCC")],
            foreground=[("disabled", "#888")],
        )

        # Regular button
        style.configure(
            "TButton",
            background="#E8D5C4",
            foreground=DARK_BROWN,
            borderwidth=0,
            focuscolor="none",
            relief="flat",
            padding=(10, 4),
            font=("Arial", 10),
        )
        style.map(
            "TButton",
            background=[("active", LIGHT_WARM), ("disabled", "#CCC")],
            foreground=[("disabled", "#888")],
        )

        # Combobox
        style.configure(
            "TCombobox",
            fieldbackground="white",
            background="white",
            foreground=DARK_BROWN,
            arrowcolor=DARK_BROWN,
        )

        # Scrollbar
        style.configure("TScrollbar", background=CREAM, troughcolor="#E8D5C4")

    # ---------- config ----------

    def _is_config_complete(self):
        path = Path("config.properties")
        if not path.exists():
            return False
        try:
            config = {}
            for line in path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    config[k.strip()] = v.strip()
            return bool(config.get("api.key", "").strip())
        except Exception:
            return False

    def _init_services(self):
        self.ai_service = AiService()
        self.alibaba_asr = AlibabaAsrService()
        self.reading_service = ReadingService(self.ai_service, self.alibaba_asr)
        self.conversation_service = ConversationService(self.ai_service, self.alibaba_asr)

    # ---------- panels ----------

    def _show_setup(self):
        for w in self._container.winfo_children():
            w.destroy()
        self._panels.clear()

        setup = SetupPanel(self._container, self._complete_setup)
        setup.pack(fill="both", expand=True)
        self._panels["setup"] = setup

    def _complete_setup(self):
        for w in self._container.winfo_children():
            w.destroy()
        self._panels.clear()

        self._init_services()
        self._create_panels()
        self._show_panel("home")

    def _create_panels(self):
        home = HomePanel(
            self._container,
            on_reading=lambda: self._show_panel("reading"),
            on_conversation=lambda: self._show_panel("conversation"),
            on_settings=self._open_settings,
        )
        reading = ReadingPanel(
            self._container, self.reading_service, on_back=lambda: self._show_panel("home")
        )
        conversation = ConversationPanel(
            self._container,
            self.conversation_service,
            on_back=lambda: self._show_panel("home"),
        )

        self._panels["home"] = home
        self._panels["reading"] = reading
        self._panels["conversation"] = conversation

    def _show_panel(self, name):
        if self._conversation_panel and name != "conversation":
            self._conversation_panel.reset()

        panel = self._panels.get(name)
        if panel is None:
            return

        for p in self._panels.values():
            p.pack_forget()
        panel.pack(fill="both", expand=True)

    def _open_settings(self):
        for p in self._panels.values():
            p.pack_forget()

        setup = SetupPanel(self._container, self._complete_setup)
        setup.pack(fill="both", expand=True)
        self._panels["setup"] = setup


def main():
    app = EnglishSpeakerApp()
    app.mainloop()


if __name__ == "__main__":
    main()
