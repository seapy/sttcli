from __future__ import annotations

import sys
import webbrowser
from pathlib import Path

import click

from sttcli.audio import extract_audio, get_duration, is_video
from sttcli.config import resolve_api_key
from sttcli.formatters import get_formatter
from sttcli.gender import detect_gender, detect_genders_per_speaker
from sttcli.progress import make_progress, StepProgress
from sttcli.providers import get_provider


# ── Smart default-command group ──────────────────────────────────────────────

class _SmartCLI(click.Group):
    """Routes to 'transcribe' when the first positional arg is not a subcommand."""

    def parse_args(self, ctx, args):
        for i, arg in enumerate(args):
            if not arg.startswith("-"):
                if arg not in self.commands:
                    # Not a subcommand — prepend 'transcribe'
                    args = list(args)
                    args.insert(i, "transcribe")
                break
        return super().parse_args(ctx, args)


@click.group(cls=_SmartCLI, invoke_without_command=True)
@click.pass_context
def main(ctx):
    """Transcribe audio or video files to text using various STT providers."""
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


# ── transcribe (existing behavior) ──────────────────────────────────────────

@main.command("transcribe")
@click.argument("input_file", type=click.Path(exists=True, path_type=Path))
@click.option("-p", "--provider", "provider_name",
              type=click.Choice(["whisper", "openai", "gemini", "elevenlabs"]),
              default="whisper", show_default=True,
              help="STT provider to use.")
@click.option("-m", "--model", default=None, help="Provider model name.")
@click.option("-l", "--language", default=None, help="Language code (e.g. ko, en, ja).")
@click.option("-f", "--format", "fmt",
              type=click.Choice(["markdown", "srt", "json", "text"]),
              default="markdown", show_default=True,
              help="Output format.")
@click.option("-o", "--output", type=click.Path(path_type=Path), default=None,
              help="Output file path (default: stdout).")
@click.option("--api-key", default=None, help="API key (overrides env and config).")
@click.option("--config", "config_file", type=click.Path(path_type=Path), default=None,
              help="Config file path (default: ~/.sttcli.toml).")
@click.option("--device", type=click.Choice(["cpu", "cuda", "mps"]), default="cpu",
              show_default=True, help="Compute device for Whisper.")
@click.option("--diarize", is_flag=True, default=False,
              help="Enable speaker diarization (elevenlabs and gemini only).")
@click.option("--num-speakers", type=int, default=None,
              help="Number of speakers hint (optional, used by elevenlabs and gemini).")
def transcribe(
    input_file: Path,
    provider_name: str,
    model: str | None,
    language: str | None,
    fmt: str,
    output: Path | None,
    api_key: str | None,
    config_file: Path | None,
    device: str,
    diarize: bool,
    num_speakers: int | None,
):
    """Transcribe a single audio or video file."""

    if diarize and provider_name in ("whisper", "openai"):
        raise click.UsageError(
            f"--diarize는 {provider_name} 프로바이더에서 지원되지 않습니다. "
            "elevenlabs 또는 gemini를 사용하세요."
        )

    resolved_key = resolve_api_key(provider_name, api_key, config_file)

    ProviderClass = get_provider(provider_name)
    provider = ProviderClass(
        model=model, language=language, api_key=resolved_key,
        device=device, diarize=diarize, num_speakers=num_speakers,
    )

    FormatterClass = get_formatter(fmt)
    formatter = FormatterClass()

    audio_path: Path | None = None
    is_temp = False

    try:
        with make_progress() as progress:
            if is_video(input_file):
                extract_step = StepProgress(progress, "Extracting audio...", total=100)
                extract_step.advance_to(0)
                audio_path, is_temp = extract_audio(input_file)
                extract_step.advance_to(100, "Audio extracted")
            else:
                audio_path = input_file

            trans_step = StepProgress(progress, "Transcribing...", total=100)
            result = provider.transcribe(audio_path, trans_step)

            # Skip pitch-based detection if the provider already supplied gender
            # (e.g. Gemini returns it directly from the transcription call).
            already_detected = any(seg.gender for seg in result.segments)
            if already_detected:
                gender_step = StepProgress(progress, "Gender detected by provider", total=100)
                gender_step.advance_to(100, "Done")
            else:
                gender_step = StepProgress(progress, "Detecting speaker gender...", total=100)
                gender_step.advance_to(0)
                has_speakers = any(seg.speaker for seg in result.segments)
                if has_speakers:
                    genders = detect_genders_per_speaker(str(audio_path), result.segments)
                    for seg in result.segments:
                        if seg.speaker and seg.speaker in genders:
                            seg.gender = genders[seg.speaker]
                else:
                    detected = detect_gender(str(audio_path))
                    for seg in result.segments:
                        seg.gender = detected
                gender_step.advance_to(100, "Done")

            fmt_step = StepProgress(progress, "Formatting output...", total=100)
            fmt_step.advance_to(50)
            output_text = formatter.format(result)
            fmt_step.advance_to(100, "Done")

    finally:
        if is_temp and audio_path and audio_path.exists():
            audio_path.unlink()

    if output:
        output.write_text(output_text, encoding="utf-8")
        click.echo(f"Transcript saved to {output}", err=True)
    else:
        sys.stdout.write(output_text)


# ── benchmark ────────────────────────────────────────────────────────────────

@main.command("benchmark")
@click.argument("input_file", type=click.Path(exists=True, path_type=Path))
@click.option("--providers", "provider_list", default=None,
              help="Comma-separated providers to run (default: all). "
                   "e.g. elevenlabs,gemini,openai,whisper")
@click.option("--output-dir", type=click.Path(path_type=Path), default=None,
              help="Output directory (default: <input_stem>_benchmark/ next to input).")
@click.option("--num-speakers", type=int, default=None,
              help="Speaker count hint for diarization.")
@click.option("--no-diarize", is_flag=True, default=False,
              help="Disable diarization (run as plain transcription benchmark).")
@click.option("--device", type=click.Choice(["cpu", "cuda", "mps"]), default="cpu",
              show_default=True, help="Compute device for Whisper.")
@click.option("--config", "config_file", type=click.Path(path_type=Path), default=None,
              help="Config file path (default: ~/.sttcli.toml).")
@click.option("--no-open", is_flag=True, default=False,
              help="Do not open the HTML result in the browser.")
def benchmark(
    input_file: Path,
    provider_list: str | None,
    output_dir: Path | None,
    num_speakers: int | None,
    no_diarize: bool,
    device: str,
    config_file: Path | None,
    no_open: bool,
):
    """Run all providers on INPUT_FILE and generate an HTML comparison report."""
    from sttcli.benchmark import ALL_PROVIDERS, parse_provider_spec, run_benchmark
    from sttcli.formatters.html_compare import generate_comparison_html
    from sttcli.formatters.markdown import MarkdownFormatter

    # Resolve provider specs (supports "provider" or "provider:model")
    if provider_list:
        specs = [p.strip() for p in provider_list.split(",") if p.strip()]
        invalid = [s for s in specs if parse_provider_spec(s)[0] not in ALL_PROVIDERS]
        if invalid:
            raise click.UsageError(f"Unknown provider(s): {', '.join(invalid)}")
        providers = specs
    else:
        providers = list(ALL_PROVIDERS)

    # Resolve output directory
    if output_dir is None:
        output_dir = input_file.parent / f"{input_file.stem}_benchmark"
    output_dir.mkdir(parents=True, exist_ok=True)

    click.echo(
        f"\n🚀 Starting benchmark: {input_file.name}\n"
        f"   Providers : {', '.join(providers)}\n"
        f"   Diarize   : {'off (--no-diarize)' if no_diarize else 'on (where supported)'}\n"
        f"   Output    : {output_dir}\n",
        err=True,
    )

    # Run all providers
    _, entries = run_benchmark(
        input_path=input_file,
        provider_specs=providers,
        diarize=not no_diarize,
        num_speakers=num_speakers,
        config_file=config_file,
        device=device,
    )

    # Save individual markdown files
    formatter = MarkdownFormatter()
    click.echo("\n💾 Saving individual transcripts...", err=True)
    for entry in entries:
        if entry.result is None:
            continue
        safe_model = entry.result.model.replace("/", "-")
        out_path = output_dir / f"{entry.provider}_{safe_model}.md"
        out_path.write_text(formatter.format(entry.result), encoding="utf-8")
        click.echo(f"   {out_path.name}", err=True)

    # Generate HTML comparison
    html_path = output_dir / "comparison.html"
    html_content = generate_comparison_html(str(input_file), entries)
    html_path.write_text(html_content, encoding="utf-8")

    click.echo(f"\n✅ HTML comparison saved to:\n   {html_path}\n", err=True)

    # Open in browser
    if not no_open:
        webbrowser.open(html_path.as_uri())


if __name__ == "__main__":
    main()
