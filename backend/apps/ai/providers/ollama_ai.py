from __future__ import annotations

import json
from urllib.request import Request, urlopen


class OllamaAIProvider:
    provider_name = "ollama"

    def __init__(self, *, base_url: str, model: str):
        self.base_url = base_url.rstrip("/")
        self.model = model

    def generate_remediation(self, *, finding_context: dict, sources: list[dict]) -> str:
        prompt = (
            "Use only the trusted context sources below. Return plain text sections: Executive summary, "
            "Technical risk, Business impact, Recommended remediation steps, Validation steps, Caveats and assumptions. "
            "Start with Draft — human review required.\n\n"
            f"Finding: {finding_context}\n\nSources: {sources}"
        )
        payload = json.dumps({"model": self.model, "prompt": prompt, "stream": False}).encode("utf-8")
        request = Request(f"{self.base_url}/api/generate", data=payload, headers={"Content-Type": "application/json"})
        with urlopen(request, timeout=60) as response:
            data = json.loads(response.read().decode("utf-8"))
        content = str(data.get("response") or "").strip()
        if not content:
            raise ValueError("AI provider returned an empty response.")
        if not content.startswith("Draft — human review required"):
            content = "Draft — human review required\n\n" + content
        return content
