import tkinter as tk
from tkinter import ttk
from pathlib import Path


class SetupPanel(ttk.Frame):
    def __init__(self, parent, on_complete):
        super().__init__(parent)
        self.on_complete = on_complete
        self._build_ui()
        self._load_existing_config()

    def _build_ui(self):
        pad = {"padx": 5, "pady": 5}

        # Title
        ttk.Label(self, text="API Configuration", font=("Arial", 18, "bold")).pack(
            pady=(20, 10)
        )

        # --- DeepSeek Section ---
        ttk.Separator(self, orient="horizontal").pack(fill="x", padx=20, pady=5)
        ttk.Label(self, text="DeepSeek (required)", font=("Arial", 13, "bold")).pack(
            anchor="w", padx=20, pady=2
        )

        f1 = ttk.Frame(self)
        f1.pack(fill="x", padx=40, pady=2)
        ttk.Label(f1, text="API URL:", width=16).pack(side="left")
        self.endpoint_var = tk.StringVar(
            value="https://api.deepseek.com/v1/chat/completions"
        )
        self.endpoint_entry = ttk.Entry(f1, textvariable=self.endpoint_var, width=50)
        self.endpoint_entry.pack(side="left", fill="x", expand=True)

        f2 = ttk.Frame(self)
        f2.pack(fill="x", padx=40, pady=2)
        ttk.Label(f2, text="API Key:", width=16).pack(side="left")
        self.api_key_var = tk.StringVar()
        self.api_key_entry = ttk.Entry(
            f2, textvariable=self.api_key_var, width=50, show="*"
        )
        self.api_key_entry.pack(side="left", fill="x", expand=True)

        # --- Alibaba ASR Section ---
        ttk.Separator(self, orient="horizontal").pack(fill="x", padx=20, pady=(15, 5))
        ttk.Label(self, text="Alibaba ASR (optional)", font=("Arial", 13, "bold")).pack(
            anchor="w", padx=20, pady=2
        )

        f3 = ttk.Frame(self)
        f3.pack(fill="x", padx=40, pady=2)
        ttk.Label(f3, text="AccessKey ID:", width=16).pack(side="left")
        self.ak_id_var = tk.StringVar()
        ttk.Entry(f3, textvariable=self.ak_id_var, width=50).pack(
            side="left", fill="x", expand=True
        )

        f4 = ttk.Frame(self)
        f4.pack(fill="x", padx=40, pady=2)
        ttk.Label(f4, text="AccessKey Secret:", width=16).pack(side="left")
        self.ak_secret_var = tk.StringVar()
        ttk.Entry(f4, textvariable=self.ak_secret_var, width=50, show="*").pack(
            side="left", fill="x", expand=True
        )

        f5 = ttk.Frame(self)
        f5.pack(fill="x", padx=40, pady=2)
        ttk.Label(f5, text="AppKey:", width=16).pack(side="left")
        self.app_key_var = tk.StringVar()
        ttk.Entry(f5, textvariable=self.app_key_var, width=50).pack(
            side="left", fill="x", expand=True
        )

        # Save button
        ttk.Button(
            self, text="Save & Start", command=self._handle_save, style="Accent.TButton"
        ).pack(pady=15)

        # Status
        self.status_var = tk.StringVar(value=" ")
        self.status_label = ttk.Label(self, textvariable=self.status_var, foreground="red")
        self.status_label.pack()

    def _load_existing_config(self):
        path = Path("config.properties")
        if not path.exists():
            return
        try:
            config = {}
            for line in path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    config[k.strip()] = v.strip()

            if config.get("api.endpoint"):
                self.endpoint_var.set(config["api.endpoint"])
            if config.get("api.key"):
                self.api_key_var.set(config["api.key"])
            if config.get("aliyun.accessKeyId"):
                self.ak_id_var.set(config["aliyun.accessKeyId"])
            if config.get("aliyun.accessKeySecret"):
                self.ak_secret_var.set(config["aliyun.accessKeySecret"])
            if config.get("aliyun.appKey"):
                self.app_key_var.set(config["aliyun.appKey"])
        except Exception:
            pass

    def _handle_save(self):
        endpoint = self.endpoint_var.get().strip()
        api_key = self.api_key_var.get().strip()

        if not endpoint or not api_key:
            self.status_var.set("API URL and API Key are required.")
            return

        try:
            path = Path("config.properties")
            lines = []
            if path.exists():
                lines = path.read_text(encoding="utf-8").splitlines()

            config = {}
            for line in lines:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    config[k.strip()] = v.strip()

            config["api.endpoint"] = endpoint
            config["api.key"] = api_key
            config.setdefault("api.model", "deepseek-chat")
            config["aliyun.accessKeyId"] = self.ak_id_var.get().strip()
            config["aliyun.accessKeySecret"] = self.ak_secret_var.get().strip()
            config["aliyun.appKey"] = self.app_key_var.get().strip()

            with open(path, "w", encoding="utf-8") as f:
                for key in [
                    "api.endpoint",
                    "api.key",
                    "api.model",
                    "aliyun.accessKeyId",
                    "aliyun.accessKeySecret",
                    "aliyun.appKey",
                ]:
                    f.write(f"{key}={config.get(key, '')}\n")

            self.status_var.set("Configuration saved.")
            self.status_label.configure(foreground="green")
            self.after(100, self.on_complete)

        except Exception as e:
            self.status_var.set(f"Error saving config: {e}")
