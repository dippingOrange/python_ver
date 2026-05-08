import json
import time
import uuid
import wave
import requests
import websocket
from pathlib import Path
from model.pronunciation_result import PronunciationResult, WordScore, PhonemeScore


class AlibabaAsrError(Exception):
    pass


class AlibabaAsrService:
    TOKEN_URL = "https://nls-meta.cn-shanghai.aliyuncs.com/api/v1/token"
    WS_GATEWAY = "wss://nls-gateway.cn-shanghai.aliyuncs.com/ws/v1"

    def __init__(self, config_path: str = "config.properties"):
        config = {}
        path = Path(config_path)
        if path.exists():
            for line in path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    config[key.strip()] = value.strip()

        self.access_key_id = config.get("aliyun.accessKeyId", "").strip()
        self.access_key_secret = config.get("aliyun.accessKeySecret", "").strip()
        self.app_key = config.get("aliyun.appKey", "").strip()
        self.enabled = bool(self.access_key_id and self.access_key_secret and self.app_key)

        self._cached_token = None
        self._token_expiry = 0

    def is_enabled(self) -> bool:
        return self.enabled

    def evaluate(self, wav_file_path: str, reference_text: str) -> PronunciationResult | None:
        if not self.enabled:
            return None
        try:
            token = self._get_token()
            return self._call_assessment(token, wav_file_path, reference_text)
        except Exception as e:
            print(f"Alibaba ASR error: {e}")
            return None

    def _get_token(self) -> str:
        now_ms = time.time() * 1000
        if self._cached_token and now_ms < self._token_expiry - 300_000:
            return self._cached_token
        return self._refresh_token()

    def _refresh_token(self) -> str:
        body = {
            "access_key_id": self.access_key_id,
            "access_key_secret": self.access_key_secret,
            "app_key": self.app_key,
        }
        resp = requests.post(
            self.TOKEN_URL,
            json=body,
            headers={"Content-Type": "application/json"},
            timeout=10,
        )
        if resp.status_code != 200:
            raise AlibabaAsrError(f"Token request failed: {resp.status_code}")

        data = resp.json()
        self._cached_token = data["token"]
        expire_sec = int(data["expire_time"])
        self._token_expiry = time.time() * 1000 + expire_sec * 1000
        return self._cached_token

    def _call_assessment(self, token: str, wav_path: str, ref_text: str) -> PronunciationResult:
        task_id = str(uuid.uuid4())

        with open(wav_path, "rb") as f:
            audio_data = f.read()

        ws_url = f"{self.WS_GATEWAY}?token={token}"
        ws = websocket.create_connection(ws_url, timeout=10)
        ws.settimeout(30)

        response_text = ""
        audio_sent = False
        result = PronunciationResult()

        try:
            # Step 1: Send StartTranscription
            start_msg = {
                "header": {
                    "name": "StartTranscription",
                    "namespace": "SpeechTranscriber",
                    "task_id": task_id,
                    "appkey": self.app_key,
                },
                "payload": {
                    "format": "wav",
                    "sample_rate": 16000,
                    "enable_intermediate_result": False,
                    "max_sentence_silence": 800,
                    "speech_assessment": {"enable": True, "core_type": "en.sent.score"},
                    "speech_noise_threshold": 0.1,
                },
            }
            ws.send(json.dumps(start_msg))

            # Step 2: Wait for TranscriptionStarted, then send audio + stop
            while True:
                msg = ws.recv()
                msg_str = msg.decode("utf-8") if isinstance(msg, bytes) else msg
                response_text += msg_str

                if "TranscriptionStarted" in msg_str and not audio_sent:
                    audio_sent = True
                    offset = 0
                    while offset < len(audio_data):
                        chunk_len = min(8192, len(audio_data) - offset)
                        ws.send_binary(audio_data[offset : offset + chunk_len])
                        offset += chunk_len

                    stop_msg = {
                        "header": {
                            "name": "StopTranscription",
                            "namespace": "SpeechTranscriber",
                            "task_id": task_id,
                        }
                    }
                    ws.send(json.dumps(stop_msg))

                if "TranscriptionCompleted" in msg_str:
                    result = self._parse_result(response_text)
                    break
        finally:
            ws.close()

        return result

    def _parse_result(self, response_text: str) -> PronunciationResult:
        result = PronunciationResult()
        lines = response_text.split("\n")
        for line in lines:
            line = line.strip()
            if not line:
                continue
            try:
                msg = json.loads(line)
                payload = msg.get("payload", {})
                result_str = payload.get("result", "")
                if not result_str:
                    continue
                result_data = json.loads(result_str) if isinstance(result_str, str) else result_str
                assessment = result_data.get("speech_assessment", {})
                if not assessment:
                    continue

                result.overall_score = assessment.get("total_score", -1)
                result.pronunciation_score = assessment.get("phone_score", -1)
                result.fluency_score = assessment.get("fluency_score", -1)
                result.completeness_score = assessment.get("integrity_score", -1)

                details = assessment.get("details", [])
                result.word_scores = self._parse_word_scores(details)
            except (json.JSONDecodeError, KeyError, TypeError):
                continue
        return result

    def _parse_word_scores(self, details: list) -> list:
        word_scores = []
        for item in details:
            ws = WordScore()
            ws.word = item.get("word", "")
            ws.score = item.get("score", -1)
            for phone in item.get("phones", []):
                ps = PhonemeScore()
                ps.phoneme = phone.get("phone", "")
                ps.score = phone.get("score", -1)
                ws.phoneme_scores.append(ps)
            word_scores.append(ws)
        return word_scores
