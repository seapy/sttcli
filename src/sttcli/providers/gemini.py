import time
from pathlib import Path

from sttcli.models import Segment, TranscriptResult
from sttcli.progress import StepProgress
from sttcli.providers.base import BaseProvider


def _mmss_to_seconds(ts: str) -> float:
    """Convert MM:SS string to float seconds."""
    parts = ts.strip().split(":")
    if len(parts) == 2:
        return int(parts[0]) * 60 + float(parts[1])
    elif len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
    return float(ts)


_RESPONSE_SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "start": {"type": "string"},
            "end": {"type": "string"},
            "text": {"type": "string"},
        },
        "required": ["start", "end", "text"],
    },
}

_RESPONSE_SCHEMA_DIARIZE = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "start": {"type": "string"},
            "end": {"type": "string"},
            "text": {"type": "string"},
            "speaker": {"type": "string"},
        },
        "required": ["start", "end", "text", "speaker"],
    },
}


class GeminiProvider(BaseProvider):
    @property
    def default_model(self) -> str:
        return "gemini-2.5-flash"

    @property
    def provider_name(self) -> str:
        return "gemini"

    def transcribe(self, audio_path: Path, step: StepProgress) -> TranscriptResult:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=self.api_key)

        step.advance_to(10, "Uploading audio to Gemini...")
        uploaded = client.files.upload(file=audio_path)

        step.advance_to(30, "Waiting for file processing...")
        while uploaded.state and uploaded.state.name == "PROCESSING":
            time.sleep(1)
            uploaded = client.files.get(name=uploaded.name)

        step.advance_to(40, "Generating transcript...")
        prompt = (
            "Transcribe this audio into timestamped segments. "
            "Use MM:SS format for start and end times (e.g. '00:03', '01:24')."
        )
        if self.language:
            prompt += f" Output language: {self.language}."
        if self.diarize:
            prompt += (
                " Identify speakers as SPEAKER_00, SPEAKER_01, etc. "
                "Split segments at speaker boundaries."
            )
            if self.num_speakers:
                prompt += f" There are {self.num_speakers} speakers."

        schema = _RESPONSE_SCHEMA_DIARIZE if self.diarize else _RESPONSE_SCHEMA

        try:
            response = client.models.generate_content(
                model=self.model,
                contents=[
                    types.Part.from_uri(file_uri=uploaded.uri, mime_type=uploaded.mime_type),
                    prompt,
                ],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=schema,
                ),
            )
        finally:
            try:
                client.files.delete(name=uploaded.name)
            except Exception:
                pass

        step.advance_to(85, "Parsing response...")
        import json
        raw = json.loads(response.text)
        segments = [
            Segment(
                start=_mmss_to_seconds(item["start"]),
                end=_mmss_to_seconds(item["end"]),
                text=item["text"].strip(),
                speaker=item.get("speaker") or None,
            )
            for item in raw
        ]
        duration = segments[-1].end if segments else 0.0

        step.advance_to(100, "Done")
        return TranscriptResult(
            segments=segments,
            language=self.language or "",
            duration=duration,
            provider=self.provider_name,
            model=self.model,
            source_file=str(audio_path),
        )
