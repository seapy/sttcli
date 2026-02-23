from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from sttcli.audio import extract_audio, is_video
from sttcli.config import resolve_api_key
from sttcli.models import TranscriptResult
from sttcli.progress import StepProgress, make_progress
from sttcli.providers import get_provider

# Providers that support native diarization
DIARIZE_SUPPORTED = {"elevenlabs", "gemini"}

# Providers that require an API key
API_KEY_REQUIRED = {"openai", "gemini", "elevenlabs"}

# Default provider list for benchmark (uses each provider's default model)
ALL_PROVIDERS = ["elevenlabs", "gemini", "openai", "whisper"]


@dataclass
class BenchmarkEntry:
    provider: str       # provider name (e.g. "elevenlabs")
    label: str          # display label (e.g. "elevenlabs:scribe_v1" or "elevenlabs")
    result: TranscriptResult | None
    error: str | None
    diarized: bool


def parse_provider_spec(spec: str) -> tuple[str, str | None]:
    """
    Parse a provider spec like "elevenlabs:scribe_v1" into ("elevenlabs", "scribe_v1").
    "elevenlabs" → ("elevenlabs", None)  # uses provider default model
    """
    if ":" in spec:
        provider, model = spec.split(":", 1)
        return provider.strip(), model.strip()
    return spec.strip(), None


def run_benchmark(
    input_path: Path,
    provider_specs: list[str],
    diarize: bool = True,
    num_speakers: int | None = None,
    config_file: Path | None = None,
    device: str = "cpu",
) -> tuple[Path, list[BenchmarkEntry]]:
    """
    Run each provider spec on input_path and return (audio_path_used, results).
    Audio extraction (video→wav) is done once and reused across providers.

    provider_specs may include "provider" or "provider:model" entries.
    """
    import click

    # Extract audio once if needed
    audio_path: Path
    is_temp = False
    if is_video(input_path):
        click.echo(f"Extracting audio from {input_path.name}...", err=True)
        audio_path, is_temp = extract_audio(input_path)
    else:
        audio_path = input_path

    entries: list[BenchmarkEntry] = []

    try:
        for spec in provider_specs:
            provider_name, explicit_model = parse_provider_spec(spec)
            label = spec  # e.g. "elevenlabs:scribe_v1" or "elevenlabs"

            api_key = resolve_api_key(provider_name, None, config_file)

            if provider_name in API_KEY_REQUIRED and not api_key:
                click.echo(
                    f"  ⚠  [{label}] API key not configured — skipped.", err=True
                )
                entries.append(BenchmarkEntry(
                    provider=provider_name,
                    label=label,
                    result=None,
                    error="API key not configured",
                    diarized=False,
                ))
                continue

            use_diarize = diarize and provider_name in DIARIZE_SUPPORTED

            click.echo(
                f"  ▶  [{label}] transcribing"
                f"{' (diarize)' if use_diarize else ''}...",
                err=True,
            )

            try:
                ProviderClass = get_provider(provider_name)
                provider = ProviderClass(
                    model=explicit_model,  # None → provider uses its own default
                    api_key=api_key,
                    device=device,
                    diarize=use_diarize,
                    num_speakers=num_speakers,
                )
                with make_progress() as progress:
                    step = StepProgress(
                        progress, f"[{label}] Transcribing...", total=100
                    )
                    result = provider.transcribe(audio_path, step)

                entries.append(BenchmarkEntry(
                    provider=provider_name,
                    label=label,
                    result=result,
                    error=None,
                    diarized=use_diarize,
                ))
                click.echo(
                    f"  ✓  [{label}] done "
                    f"({len(result.segments)} segments, {result.language})",
                    err=True,
                )

            except Exception as exc:
                click.echo(f"  ✗  [{label}] error: {exc}", err=True)
                entries.append(BenchmarkEntry(
                    provider=provider_name,
                    label=label,
                    result=None,
                    error=str(exc),
                    diarized=use_diarize,
                ))
    finally:
        if is_temp and audio_path.exists():
            audio_path.unlink()

    return audio_path, entries
