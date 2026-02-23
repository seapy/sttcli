# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Run the CLI (always use the venv)
.venv/bin/sttcli <input_file> [options]

# Transcribe (default provider: whisper)
.venv/bin/sttcli audio.mp3
.venv/bin/sttcli audio.mp3 --provider elevenlabs --diarize
.venv/bin/sttcli audio.mp3 --provider elevenlabs --diarize --model scribe_v2

# Benchmark all providers (generates HTML comparison + individual .md files)
.venv/bin/sttcli benchmark audio.mp4
.venv/bin/sttcli benchmark audio.mp4 --providers "elevenlabs:scribe_v2,elevenlabs:scribe_v1,gemini,openai,whisper"

# Install / sync deps
uv sync
```

API keys are read from `~/.sttcli.toml`:
```toml
[openai]
api_key = "..."
[gemini]
api_key = "..."
[elevenlabs]
api_key = "..."
```

## Architecture

### Data flow
```
input file
  └─ audio.py          extract_audio() → temp WAV (ffmpeg, 16kHz mono PCM)
       └─ providers/*  transcribe() → TranscriptResult
            └─ formatters/*  format() → string output
```

### Core models (`models.py`)
- `Segment(start, end, text, speaker=None)` — one timestamped chunk
- `TranscriptResult(segments, language, duration, provider, model, source_file)`

### Provider system (`providers/`)
All providers extend `BaseProvider(model, language, api_key, device, diarize, num_speakers)`.

| Provider | Module | Default model | Diarize |
|---|---|---|---|
| `whisper` | `whisper_local.py` | `turbo` | ❌ |
| `openai` | `openai_api.py` | `whisper-1` | ❌ (25 MB limit) |
| `gemini` | `gemini.py` | `gemini-2.5-flash` | ✅ prompt-based, JSON schema |
| `elevenlabs` | `elevenlabs.py` | `scribe_v2` | ✅ native `diarize=True` |

ElevenLabs groups word-level timestamps into segments in `_group_words()`, splitting on sentence endings, long silences (>1s), or speaker changes when diarizing.

Gemini uploads the file, polls until `PROCESSING` completes, sends a structured JSON schema prompt, then deletes the file. Timestamps come back as `MM:SS` strings parsed by `_mmss_to_seconds()`.

### CLI (`cli.py`)
Uses a `_SmartCLI` Click group: unknown first arguments are automatically routed to the `transcribe` subcommand, preserving backward compatibility (`sttcli audio.mp3` = `sttcli transcribe audio.mp3`).

Subcommands: `transcribe`, `benchmark`.

`--diarize` on `whisper`/`openai` raises `UsageError` immediately.

### Benchmark (`benchmark.py`)
`run_benchmark()` accepts `provider_specs` as `["elevenlabs:scribe_v1", "gemini", ...]`. The `provider:model` format overrides the provider's `default_model`. Audio is extracted once and reused across all providers. Returns `list[BenchmarkEntry]` with `label`, `result`, `error`, `diarized`.

### Formatters (`formatters/`)
- `markdown.py` — bold timestamps, bold speaker badge if present
- `srt.py` — standard SRT with `[SPEAKER_XX]` prefix when diarized
- `json_fmt.py` — adds `"speaker"` key to all segments only if any segment has a speaker
- `text.py` — inserts `SPEAKER_XX:` header lines on speaker change
- `html_compare.py` — self-contained HTML, CSS grid of cards per provider, deterministic speaker colors from `_PALETTE`
