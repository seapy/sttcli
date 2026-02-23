# sttcli

A CLI tool for transcribing audio and video files using multiple STT providers. Supports speaker diarization and cross-provider benchmarking.

## Installation

```bash
uv tool install git+https://github.com/seapy/sttcli.git
```

ffmpeg is required for video files:
```bash
brew install ffmpeg        # macOS
sudo apt install ffmpeg    # Ubuntu/Debian
```

## API Keys

Create `~/.sttcli.toml` and add keys for the providers you want to use:

```toml
[openai]
api_key = "sk-..."

[gemini]
api_key = "AIza..."

[elevenlabs]
api_key = "sk_..."
```

Whisper runs locally and requires no API key.

Alternatively, environment variables are also supported: `OPENAI_API_KEY`, `GEMINI_API_KEY`, `ELEVENLABS_API_KEY`.

## Usage

```bash
sttcli <file> [options]
```

Accepts audio files (mp3, wav, flac, m4a, etc.) and video files (mp4, mkv, mov, etc.). Audio is extracted from video automatically.

### Providers

| Provider | Default model | Diarization | Notes |
|---|---|---|---|
| `whisper` | turbo | ❌ | Local, no API key required |
| `openai` | whisper-1 | ❌ | 25 MB file size limit |
| `gemini` | gemini-2.5-flash | ✅ | Prompt-based |
| `elevenlabs` | scribe_v2 | ✅ | Native, word-level timestamps |

```bash
sttcli audio.mp3                            # default (whisper)
sttcli audio.mp3 --provider openai
sttcli audio.mp3 --provider gemini
sttcli audio.mp3 --provider elevenlabs
```

### Output formats

```bash
sttcli audio.mp3 -f markdown   # default
sttcli audio.mp3 -f srt
sttcli audio.mp3 -f json
sttcli audio.mp3 -f text
```

Save to file:
```bash
sttcli audio.mp3 -o transcript.md
sttcli audio.mp3 -f srt -o subtitle.srt
```

### Other options

```bash
sttcli audio.mp3 --language ko              # language hint
sttcli audio.mp3 --provider whisper --model large-v3   # override model
sttcli audio.mp3 --provider gemini --model gemini-2.5-pro
```

## Speaker Diarization

Supported by ElevenLabs (native) and Gemini (prompt-based). Add the `--diarize` flag:

```bash
sttcli audio.mp3 --provider elevenlabs --diarize
sttcli audio.mp3 --provider gemini --diarize
sttcli audio.mp3 --provider elevenlabs --diarize --num-speakers 2
```

Speaker labels appear in all output formats:

**markdown**
```
**[00:03 → 00:09]** **speaker_0** You mentioned that a lot of apps might be made obsolete.
**[00:12 → 00:13]** **speaker_1** Yeah.
```

**srt**
```
1
00:00:03,000 --> 00:00:09,000
[speaker_0] You mentioned that a lot of apps might be made obsolete.
```

**text**
```
speaker_0:
You mentioned that a lot of apps might be made obsolete.

speaker_1:
Yeah.
```

**json**
```json
{
  "segments": [
    { "start": 3.0, "end": 9.0, "text": "You mentioned...", "speaker": "speaker_0" }
  ]
}
```

> `--diarize` with `whisper` or `openai` will raise an error.

## Benchmark

Run the same file through multiple providers and compare results in a single HTML report. Providers without API keys are skipped automatically.

```bash
# Run all providers
sttcli benchmark audio.mp4

# Specific providers
sttcli benchmark audio.mp4 --providers "elevenlabs,gemini,openai,whisper"

# Compare models within the same provider
sttcli benchmark audio.mp4 --providers "elevenlabs:scribe_v2,elevenlabs:scribe_v1,gemini,openai,whisper"

# Transcription-only benchmark (no diarization)
sttcli benchmark audio.mp4 --no-diarize
```

Diarization is enabled by default for providers that support it (ElevenLabs, Gemini).

Output is saved to `<filename>_benchmark/`:
- `elevenlabs_scribe_v2.md`, `gemini_gemini-2.5-flash.md`, ... — individual results per provider
- `comparison.html` — side-by-side comparison, opens in browser automatically

```bash
sttcli benchmark audio.mp4 --output-dir ./results   # custom output dir
sttcli benchmark audio.mp4 --no-open                # skip browser
```

## Reference

### `sttcli [transcribe]`

```
sttcli [transcribe] <INPUT_FILE> [OPTIONS]

  -p, --provider [whisper|openai|gemini|elevenlabs]  STT provider (default: whisper)
  -m, --model TEXT                                   Model name
  -l, --language TEXT                                Language code (e.g. en, ko, ja)
  -f, --format [markdown|srt|json|text]              Output format (default: markdown)
  -o, --output PATH                                  Output file (default: stdout)
      --api-key TEXT                                 API key override
      --config PATH                                  Config file (default: ~/.sttcli.toml)
      --device [cpu|cuda|mps]                        Compute device for Whisper (default: cpu)
      --diarize                                      Enable speaker diarization
      --num-speakers INTEGER                         Speaker count hint
```

### `sttcli benchmark`

```
sttcli benchmark <INPUT_FILE> [OPTIONS]

      --providers TEXT         Comma-separated provider list (default: all)
      --output-dir PATH        Output directory
      --num-speakers INTEGER   Speaker count hint
      --no-diarize             Disable diarization
      --device [cpu|cuda|mps]  Compute device for Whisper (default: cpu)
      --config PATH            Config file (default: ~/.sttcli.toml)
      --no-open                Do not open browser after benchmark
```
