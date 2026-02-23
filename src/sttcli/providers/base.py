from abc import ABC, abstractmethod
from pathlib import Path

from sttcli.models import TranscriptResult
from sttcli.progress import StepProgress


class BaseProvider(ABC):
    def __init__(self, model: str | None = None, language: str | None = None, api_key: str | None = None, device: str = "cpu", diarize: bool = False, num_speakers: int | None = None):
        self.model = model or self.default_model
        self.language = language
        self.api_key = api_key
        self.device = device
        self.diarize = diarize
        self.num_speakers = num_speakers

    @property
    @abstractmethod
    def default_model(self) -> str: ...

    @property
    @abstractmethod
    def provider_name(self) -> str: ...

    @abstractmethod
    def transcribe(self, audio_path: Path, step: StepProgress) -> TranscriptResult: ...
