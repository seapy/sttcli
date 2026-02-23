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
        ]

        # Add gender metadata rows
        has_speakers = any(seg.speaker for seg in result.segments)
        if has_speakers:
            seen: dict[str, str] = {}
            for seg in result.segments:
                if seg.speaker and seg.gender and seg.speaker not in seen:
                    seen[seg.speaker] = seg.gender
            for speaker, gender in sorted(seen.items()):
                lines.append(f"| {speaker}_gender | {gender} |")
        else:
            first_gender = next(
                (seg.gender for seg in result.segments if seg.gender), None
            )
            if first_gender:
                lines.append(f"| Gender   | {first_gender} |")

        lines += ["", "---", ""]

        for seg in result.segments:
            start = _fmt_time(seg.start)
            end = _fmt_time(seg.end)
            if seg.speaker:
                lines.append(f"**[{start} → {end}]** **{seg.speaker}** {seg.text}")
            else:
                lines.append(f"**[{start} → {end}]** {seg.text}")
            lines.append("")
        return "\n".join(lines)
