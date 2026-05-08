import json
import requests
from pathlib import Path


class AiService:
    def __init__(self, config_path: str = "config.properties"):
        self.config = {}
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                self.config[key.strip()] = value.strip()

        self.endpoint = self.config.get("api.endpoint")
        self.api_key = self.config.get("api.key")
        self.model = self.config.get("api.model", "deepseek-chat")

        if not self.api_key:
            raise ValueError("api.key is not configured")

    def call_api(self, system_prompt: str, user_message: str) -> str:
        body = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
        }

        resp = requests.post(
            self.endpoint,
            json=body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            timeout=60,
        )
        data = resp.json()
        return data["choices"][0]["message"]["content"]
