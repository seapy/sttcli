from sttcli.formatters.base import BaseFormatter
from sttcli.models import TranscriptResult


class TextFormatter(BaseFormatter):
    def format(self, result: TranscriptResult) -> str:
        lines = []
        prev_speaker = object()  # sentinel
        for seg in result.segments:
            if seg.speaker is not None and seg.speaker != prev_speaker:
                if lines:
                    lines.append("")
                lines.append(f"{seg.speaker}:")
                prev_speaker = seg.speaker
            lines.append(seg.text)
        return "\n".join(lines) + "\n"
