from pathlib import Path

from sttcli.models import Segment, TranscriptResult
from sttcli.progress import StepProgress
from sttcli.providers.base import BaseProvider

SENTENCE_ENDINGS = set(".!?。！？")
MAX_SILENCE_GAP = 1.0


class ElevenLabsProvider(BaseProvider):
    @property
    def default_model(self) -> str:
        return "scribe_v2"

    @property
    def provider_name(self) -> str:
        return "elevenlabs"

    def transcribe(self, audio_path: Path, step: StepProgress) -> TranscriptResult:
        from elevenlabs import ElevenLabs

        client = ElevenLabs(api_key=self.api_key)

        step.advance_to(10, "Uploading audio to ElevenLabs...")
        with open(audio_path, "rb") as f:
            response = client.speech_to_text.convert(
                file=f,
                model_id=self.model,
                timestamps_granularity="word",
                tag_audio_events=False,
                language_code=self.language,
                diarize=self.diarize,
                num_speakers=self.num_speakers,
            )

        step.advance_to(80, "Grouping word timestamps into segments...")
        words = [w for w in (response.words or []) if getattr(w, "type", "word") == "word"]
        segments = _group_words(words, diarize=self.diarize)
        duration = segments[-1].end if segments else 0.0

        step.advance_to(100, "Done")
        return TranscriptResult(
            segments=segments,
            language=response.language_code or self.language or "",
            duration=duration,
            provider=self.provider_name,
            model=self.model,
            source_file=str(audio_path),
        )


def _group_words(words, diarize: bool = False) -> list[Segment]:
    if not words:
        return []

    segments: list[Segment] = []
    group_start = words[0].start or 0.0
    group_end = words[0].end or 0.0
    group_texts: list[str] = [words[0].text or ""]
    current_speaker: str | None = getattr(words[0], "speaker_id", None) if diarize else None

    for prev, curr in zip(words, words[1:]):
        prev_end = prev.end or 0.0
        curr_start = curr.start or 0.0
        gap = curr_start - prev_end

        sentence_break = any(group_texts[-1].rstrip().endswith(c) for c in SENTENCE_ENDINGS)
        long_silence = gap > MAX_SILENCE_GAP
        speaker_change = diarize and getattr(curr, "speaker_id", None) != current_speaker

        if sentence_break or long_silence or speaker_change:
            segments.append(Segment(
                start=group_start,
                end=group_end,
                text=" ".join(group_texts).strip(),
                speaker=current_speaker if diarize else None,
            ))
            group_start = curr_start
            group_texts = []
            if diarize:
                current_speaker = getattr(curr, "speaker_id", None)

        group_end = curr.end or group_end
        group_texts.append(curr.text or "")

    if group_texts:
        segments.append(Segment(
            start=group_start,
            end=group_end,
            text=" ".join(group_texts).strip(),
            speaker=current_speaker if diarize else None,
        ))

    return segments
