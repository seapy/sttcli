from pathlib import Path

from sttcli.formatters.base import BaseFormatter
from sttcli.models import TranscriptResult


def _fmt_time(seconds: float) -> str:
    total = int(seconds)
    m, s = divmod(total, 60)
    return f"{m:02d}:{s:02d}"


def _fmt_duration(seconds: float) -> str:
    total = int(seconds)
    m, s = divmod(total, 60)
    return f"{m:02d}:{s:02d}"


class MarkdownFormatter(BaseFormatter):
    def format(self, result: TranscriptResult) -> str:
        filename = Path(result.source_file).name
        lines = [
            f"# Transcript: {filename}",
            "",
            "| Field    | Value            |",
            "|----------|------------------|",
            f"| Provider | {result.provider} |",
            f"| Model    | {result.model} |",
            f"| Language | {result.language} |",
            f"| Duration | {_fmt_duration(result.duration)} |",
            "",
            "---",
            "",
        ]
        for seg in result.segments:
            start = _fmt_time(seg.start)
            end = _fmt_time(seg.end)
            if seg.speaker:
                lines.append(f"**[{start} → {end}]** **{seg.speaker}** {seg.text}")
            else:
                lines.append(f"**[{start} → {end}]** {seg.text}")
            lines.append("")
        return "\n".join(lines)
