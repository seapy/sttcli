from dataclasses import dataclass, field


@dataclass
class Segment:
    start: float
    end: float
    text: str
    speaker: str | None = field(default=None)


@dataclass
class TranscriptResult:
    segments: list[Segment]
    language: str
    duration: float
    provider: str
    model: str
    source_file: str
