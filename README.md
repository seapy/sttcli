# sttcli

오디오/영상 파일을 텍스트로 변환하는 CLI 도구. 여러 STT 프로바이더를 지원하며 화자 분리(Speaker Diarization)와 프로바이더 간 벤치마크 기능을 제공합니다.

## 설치

```bash
uv tool install git+https://github.com/seapy/sttcli.git
```

설치 후 `sttcli` 명령어를 바로 사용할 수 있습니다.

ffmpeg이 필요합니다 (영상 파일 처리 시):
```bash
brew install ffmpeg        # macOS
sudo apt install ffmpeg    # Ubuntu/Debian
```

## API 키 설정

`~/.sttcli.toml` 파일을 생성하고 사용할 프로바이더의 키를 입력합니다.

```toml
[openai]
api_key = "sk-..."

[gemini]
api_key = "AIza..."

[elevenlabs]
api_key = "sk_..."
```

Whisper는 로컬 실행이므로 API 키가 필요 없습니다.

## 기본 사용법

```bash
sttcli <파일> [옵션]
```

오디오(mp3, wav, flac, m4a 등)와 영상(mp4, mkv, mov 등) 파일 모두 지원합니다. 영상은 자동으로 오디오를 추출합니다.

### 프로바이더 선택

| 프로바이더 | 기본 모델 | 화자 분리 | 비고 |
|---|---|---|---|
| `whisper` | turbo | ❌ | 로컬 실행, API 키 불필요 |
| `openai` | whisper-1 | ❌ | 25 MB 파일 크기 제한 |
| `gemini` | gemini-2.5-flash | ✅ | 프롬프트 기반 |
| `elevenlabs` | scribe_v2 | ✅ | 네이티브 지원, 단어 단위 타임스탬프 |

```bash
# 기본 (Whisper 로컬)
sttcli audio.mp3

# OpenAI
sttcli audio.mp3 --provider openai

# Gemini
sttcli audio.mp3 --provider gemini

# ElevenLabs
sttcli audio.mp3 --provider elevenlabs
```

### 출력 형식

`--format` (`-f`) 옵션으로 출력 형식을 선택합니다. 기본값은 `markdown`입니다.

```bash
sttcli audio.mp3 -f markdown   # 기본값
sttcli audio.mp3 -f srt        # 자막 파일
sttcli audio.mp3 -f json       # JSON
sttcli audio.mp3 -f text       # 순수 텍스트
```

파일로 저장:
```bash
sttcli audio.mp3 -o transcript.md
sttcli audio.mp3 -f srt -o subtitle.srt
```

### 언어 지정

```bash
sttcli audio.mp3 --language ko   # 한국어
sttcli audio.mp3 --language en   # 영어
```

### 모델 지정

```bash
sttcli audio.mp3 --provider whisper --model large-v3
sttcli audio.mp3 --provider elevenlabs --model scribe_v1
sttcli audio.mp3 --provider gemini --model gemini-2.5-pro
```

## 화자 분리 (Diarization)

ElevenLabs와 Gemini에서 지원합니다. `--diarize` 플래그를 추가합니다.

```bash
# ElevenLabs (네이티브, 가장 정확)
sttcli audio.mp3 --provider elevenlabs --diarize

# Gemini
sttcli audio.mp3 --provider gemini --diarize

# 화자 수 힌트 제공 (선택)
sttcli audio.mp3 --provider elevenlabs --diarize --num-speakers 2
```

화자 분리 결과는 포맷에 따라 다르게 표시됩니다.

**markdown:**
```
**[00:03 → 00:09]** **speaker_0** 안녕하세요, 반갑습니다.
**[00:10 → 00:15]** **speaker_1** 네, 저도 반갑습니다.
```

**srt:**
```
1
00:00:03,000 --> 00:00:09,000
[speaker_0] 안녕하세요, 반갑습니다.
```

**text:**
```
speaker_0:
안녕하세요, 반갑습니다.

speaker_1:
네, 저도 반갑습니다.
```

**json:**
```json
{
  "segments": [
    { "start": 3.0, "end": 9.0, "text": "안녕하세요, 반갑습니다.", "speaker": "speaker_0" }
  ]
}
```

> Whisper, OpenAI에 `--diarize`를 사용하면 오류가 발생합니다.

## 벤치마크

동일한 파일을 여러 프로바이더로 동시에 전사하고, 결과를 HTML 파일로 비교합니다. API 키가 없는 프로바이더는 자동으로 스킵됩니다.

```bash
# 전체 프로바이더로 벤치마크 (기본값)
sttcli benchmark audio.mp4

# 특정 프로바이더 지정
sttcli benchmark audio.mp4 --providers "elevenlabs,gemini,openai,whisper"

# provider:model 형식으로 모델 간 비교
sttcli benchmark audio.mp4 --providers "elevenlabs:scribe_v2,elevenlabs:scribe_v1,gemini,openai,whisper"

# 화자 분리 없이 전사 정확도만 비교
sttcli benchmark audio.mp4 --no-diarize

# 결과 저장 위치 지정
sttcli benchmark audio.mp4 --output-dir ./results
```

기본적으로 화자 분리를 지원하는 프로바이더(ElevenLabs, Gemini)는 diarize 모드로, 나머지는 일반 모드로 실행됩니다.

**출력 파일** (`<입력파일명>_benchmark/` 폴더에 생성):
- `elevenlabs_scribe_v2.md`, `gemini_gemini-2.5-flash.md` 등 — 프로바이더별 개별 결과
- `comparison.html` — 모든 결과를 한눈에 비교하는 HTML (자동으로 브라우저 오픈)

HTML 비교 화면을 열지 않으려면:
```bash
sttcli benchmark audio.mp4 --no-open
```

## 전체 옵션

### `sttcli transcribe` (기본 명령)

```
sttcli [transcribe] <INPUT_FILE> [OPTIONS]

옵션:
  -p, --provider [whisper|openai|gemini|elevenlabs]  STT 프로바이더 (기본: whisper)
  -m, --model TEXT                                   모델 이름
  -l, --language TEXT                                언어 코드 (ko, en, ja 등)
  -f, --format [markdown|srt|json|text]              출력 형식 (기본: markdown)
  -o, --output PATH                                  출력 파일 경로 (기본: stdout)
      --api-key TEXT                                 API 키 (설정 파일/환경변수 덮어쓰기)
      --config PATH                                  설정 파일 경로 (기본: ~/.sttcli.toml)
      --device [cpu|cuda|mps]                        Whisper 연산 장치 (기본: cpu)
      --diarize                                      화자 분리 활성화
      --num-speakers INTEGER                         화자 수 힌트
```

### `sttcli benchmark`

```
sttcli benchmark <INPUT_FILE> [OPTIONS]

옵션:
      --providers TEXT         쉼표 구분 프로바이더 목록 (기본: 전체)
      --output-dir PATH        결과 저장 폴더
      --num-speakers INTEGER   화자 수 힌트
      --no-diarize             화자 분리 비활성화
      --device [cpu|cuda|mps]  Whisper 연산 장치 (기본: cpu)
      --config PATH            설정 파일 경로
      --no-open                브라우저 자동 실행 안 함
```

## 환경변수

설정 파일 대신 환경변수를 사용할 수도 있습니다.

```bash
export OPENAI_API_KEY="sk-..."
export GEMINI_API_KEY="AIza..."
export ELEVENLABS_API_KEY="sk_..."
```
