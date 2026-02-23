from pathlib import Path

from sttcli.models import Segment, TranscriptResult
from sttcli.progress import StepProgress
from sttcli.providers.base import BaseProvider

MAX_FILE_SIZE = 25 * 1024 * 1024  # 25 MB


class OpenAIProvider(BaseProvider):
    @property
    def default_model(self) -> str:
        return "whisper-1"

    @property
    def provider_name(self) -> str:
        return "openai"

    def transcribe(self, audio_path: Path, step: StepProgress) -> TranscriptResult:
        from openai import OpenAI

        file_size = audio_path.stat().st_size
        if file_size > MAX_FILE_SIZE:
            raise ValueError(
                f"File size {file_size / 1024 / 1024:.1f} MB exceeds OpenAI's 25 MB limit. "
                "Please compress the audio or split it into smaller chunks."
            )

        client = OpenAI(api_key=self.api_key)

        step.advance_to(10, "Uploading audio to OpenAI...")
        with open(audio_path, "rb") as f:
            kwargs = {
                "model": self.model,
                "file": f,
                "response_format": "verbose_json",
                "timestamp_granularities": ["segment"],
            }
            if self.language:
                kwargs["language"] = self.language

            response = client.audio.transcriptions.create(**kwargs)

        step.advance_to(90, "Processing response...")
        segments = [
            Segment(start=s.start, end=s.end, text=s.text.strip())
            for s in (response.segments or [])
        ]
        duration = segments[-1].end if segments else 0.0

        step.advance_to(100, "Done")
        return TranscriptResult(
            segments=segments,
            language=response.language or self.language or "",
            duration=duration,
            provider=self.provider_name,
            model=self.model,
            source_file=str(audio_path),
        )
