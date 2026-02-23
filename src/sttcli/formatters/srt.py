from sttcli.formatters.base import BaseFormatter
from sttcli.models import TranscriptResult


def _srt_time(seconds: float) -> str:
    total_ms = int(seconds * 1000)
    ms = total_ms % 1000
    total_s = total_ms // 1000
    s = total_s % 60
    total_m = total_s // 60
    m = total_m % 60
    h = total_m // 60
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


class SRTFormatter(BaseFormatter):
    def format(self, result: TranscriptResult) -> str:
        blocks = []
        for i, seg in enumerate(result.segments, start=1):
            if seg.speaker:
                label = f"[{seg.speaker} ({seg.gender})]" if seg.gender else f"[{seg.speaker}]"
                text = f"{label} {seg.text}"
            elif seg.gender:
                text = f"[{seg.gender}] {seg.text}"
            else:
                text = seg.text
            blocks.append(
                f"{i}\n"
                f"{_srt_time(seg.start)} --> {_srt_time(seg.end)}\n"
                f"{text}"
            )
        return "\n\n".join(blocks) + "\n"
