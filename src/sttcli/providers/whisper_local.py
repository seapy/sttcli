from pathlib import Path

from sttcli.models import Segment, TranscriptResult
from sttcli.progress import StepProgress
from sttcli.providers.base import BaseProvider


class WhisperProvider(BaseProvider):
    @property
    def default_model(self) -> str:
        return "turbo"

    @property
    def provider_name(self) -> str:
        return "whisper"

    def transcribe(self, audio_path: Path, step: StepProgress) -> TranscriptResult:
        import whisper

        step.advance_to(5, "Loading Whisper model...")
        model = whisper.load_model(self.model, device=self.device)

        step.advance_to(20, "Transcribing audio...")
        fp16 = self.device != "cpu"
        options = {"fp16": fp16}
        if self.language:
            options["language"] = self.language

        result = model.transcribe(str(audio_path), **options)

        step.advance_to(90, "Processing results...")
        segments = [
            Segment(start=s["start"], end=s["end"], text=s["text"].strip())
            for s in result["segments"]
        ]
        duration = segments[-1].end if segments else 0.0

        step.advance_to(100, "Done")
        return TranscriptResult(
            segments=segments,
            language=result.get("language", self.language or ""),
            duration=duration,
            provider=self.provider_name,
            model=self.model,
            source_file=str(audio_path),
        )
