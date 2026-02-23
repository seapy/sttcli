import tempfile
from pathlib import Path

import ffmpeg


AUDIO_EXTENSIONS = {".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a", ".wma", ".opus"}
VIDEO_EXTENSIONS = {".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm", ".ts", ".m2ts"}


def is_video(path: Path) -> bool:
    return path.suffix.lower() in VIDEO_EXTENSIONS


def extract_audio(input_path: Path, progress_callback=None) -> tuple[Path, bool]:
    """Extract audio from video file. Returns (audio_path, is_temp).

    If input is already audio, returns (input_path, False).
    If input is video, extracts to temp WAV and returns (temp_path, True).
    """
    if not is_video(input_path):
        return input_path, False

    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    tmp.close()
    tmp_path = Path(tmp.name)

    try:
        (
            ffmpeg
            .input(str(input_path))
            .output(
                str(tmp_path),
                acodec="pcm_s16le",
                ar=16000,
                ac=1,
                vn=None,
            )
            .overwrite_output()
            .run(quiet=True)
        )
    except ffmpeg.Error as e:
        tmp_path.unlink(missing_ok=True)
        stderr = e.stderr.decode() if e.stderr else str(e)
        raise RuntimeError(f"ffmpeg audio extraction failed: {stderr}") from e

    return tmp_path, True


def get_duration(path: Path) -> float:
    try:
        probe = ffmpeg.probe(str(path))
        return float(probe["format"]["duration"])
    except Exception:
        return 0.0
