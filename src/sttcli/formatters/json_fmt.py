import json
from dataclasses import asdict

from sttcli.formatters.base import BaseFormatter
from sttcli.models import TranscriptResult


class JSONFormatter(BaseFormatter):
    def format(self, result: TranscriptResult) -> str:
        has_speaker = any(seg.speaker is not None for seg in result.segments)
        if has_speaker:
            seg_list = [
                {"start": seg.start, "end": seg.end, "text": seg.text, "speaker": seg.speaker}
                for seg in result.segments
            ]
        else:
            seg_list = [
                {"start": seg.start, "end": seg.end, "text": seg.text}
                for seg in result.segments
            ]
        data = {
            "provider": result.provider,
            "model": result.model,
            "language": result.language,
            "duration": result.duration,
            "source_file": result.source_file,
            "segments": seg_list,
        }
        return json.dumps(data, ensure_ascii=False, indent=2)
