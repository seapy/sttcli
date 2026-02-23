from __future__ import annotations

import subprocess

import numpy as np


def _extract_pcm(
    audio_path: str,
    start: float | None = None,
    duration: float | None = None,
) -> np.ndarray:
    """Extract mono 16 kHz PCM from audio file using ffmpeg."""
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error"]
    if start is not None and start > 0:
        cmd += ["-ss", str(start)]
    cmd += ["-i", audio_path]
    if duration is not None and duration > 0:
        cmd += ["-t", str(duration)]
    cmd += ["-ar", "16000", "-ac", "1", "-f", "s16le", "-"]

    result = subprocess.run(cmd, capture_output=True)
    if not result.stdout:
        return np.array([], dtype=np.float32)
    return np.frombuffer(result.stdout, dtype=np.int16).astype(np.float32) / 32768.0


def _estimate_f0(audio: np.ndarray, sr: int = 16000) -> float | None:
    """
    Estimate fundamental frequency (F0) via autocorrelation.
    Returns the median F0 in Hz across voiced frames, or None if undetermined.
    """
    if len(audio) < int(sr * 0.1):
        return None

    frame_length = int(0.025 * sr)   # 25 ms
    hop_length = int(0.010 * sr)     # 10 ms
    min_period = int(sr / 400)       # 400 Hz ceiling
    max_period = int(sr / 50)        # 50 Hz floor

    f0_values: list[float] = []
    for i in range(0, len(audio) - frame_length, hop_length):
        frame = audio[i : i + frame_length]

        acorr = np.correlate(frame, frame, mode="full")
        acorr = acorr[len(acorr) // 2 :]   # keep positive lags

        if acorr[0] == 0:
            continue
        acorr = acorr / acorr[0]

        if max_period >= len(acorr):
            continue
        segment = acorr[min_period:max_period]
        if len(segment) == 0:
            continue

        peak_idx = int(np.argmax(segment))
        if segment[peak_idx] > 0.45:   # voiced-frame threshold
            f0_values.append(sr / (peak_idx + min_period))

    if len(f0_values) < 5:
        return None
    return float(np.median(f0_values))


def detect_gender(
    audio_path: str,
    start: float | None = None,
    end: float | None = None,
) -> str | None:
    """
    Detect speaker gender from an audio segment using pitch analysis.
    Returns 'male', 'female', or None if the pitch cannot be determined.

    Threshold: median F0 >= 165 Hz → female, < 165 Hz → male.
    """
    try:
        duration = (end - start) if (start is not None and end is not None) else None
        audio = _extract_pcm(audio_path, start, duration)
        if len(audio) == 0:
            return None
        f0 = _estimate_f0(audio)
        if f0 is None:
            return None
        return "female" if f0 >= 165.0 else "male"
    except Exception:
        return None


def detect_genders_per_speaker(audio_path: str, segments: list) -> dict[str, str]:
    """
    Detect gender for each unique speaker by aggregating pitch across all their segments.
    Returns a mapping of {speaker_id: 'male'|'female'}.
    """
    from collections import defaultdict

    speaker_f0s: dict[str, list[float]] = defaultdict(list)

    try:
        for seg in segments:
            if seg.speaker is None:
                continue
            seg_duration = seg.end - seg.start
            if seg_duration < 0.5:
                continue

            audio = _extract_pcm(audio_path, seg.start, seg_duration)
            if len(audio) == 0:
                continue
            f0 = _estimate_f0(audio)
            if f0 is not None:
                speaker_f0s[seg.speaker].append(f0)
    except Exception:
        pass

    result: dict[str, str] = {}
    for speaker, f0_list in speaker_f0s.items():
        if f0_list:
            median_f0 = float(np.median(f0_list))
            result[speaker] = "female" if median_f0 >= 165.0 else "male"
    return result
