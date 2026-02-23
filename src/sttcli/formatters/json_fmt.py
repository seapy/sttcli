import json

from sttcli.formatters.base import BaseFormatter
from sttcli.models import TranscriptResult


class JSONFormatter(BaseFormatter):
    def format(self, result: TranscriptResult) -> str:
        has_speaker = any(seg.speaker is not None for seg in result.segments)
        has_gender = any(seg.gender is not None for seg in result.segments)

        seg_list = []
        for seg in result.segments:
            d: dict = {"start": seg.start, "end": seg.end, "text": seg.text}
            if has_speaker:
                d["speaker"] = seg.speaker
            if has_gender:
                d["gender"] = seg.gender
            seg_list.append(d)

        data = {
            "provider": result.provider,
            "model": result.model,
            "language": result.language,
            "duration": result.duration,
            "source_file": result.source_file,
            "segments": seg_list,
        }
        return json.dumps(data, ensure_ascii=False, indent=2)
