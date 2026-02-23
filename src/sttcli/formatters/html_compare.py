from __future__ import annotations

import html
import re
from datetime import datetime
from pathlib import Path

from sttcli.benchmark import BenchmarkEntry

# ── Speaker color palette ────────────────────────────────────────────────────
_PALETTE = [
    "#3b82f6",  # blue
    "#ec4899",  # pink
    "#8b5cf6",  # purple
    "#f59e0b",  # amber
    "#10b981",  # emerald
    "#f97316",  # orange
    "#06b6d4",  # cyan
    "#84cc16",  # lime
]


def _speaker_color(speaker: str) -> str:
    m = re.search(r"\d+", speaker)
    idx = int(m.group()) if m else abs(hash(speaker))
    return _PALETTE[idx % len(_PALETTE)]


def _fmt_time(seconds: float) -> str:
    total = int(seconds)
    m, s = divmod(total, 60)
    return f"{m:02d}:{s:02d}"


def _fmt_duration(seconds: float) -> str:
    h = int(seconds) // 3600
    m = (int(seconds) % 3600) // 60
    s = int(seconds) % 60
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


# ── Card renderers ───────────────────────────────────────────────────────────

def _render_success_card(entry: BenchmarkEntry) -> str:
    r = entry.result
    assert r is not None

    diarize_badge = (
        '<span class="badge badge-diarize">diarized</span>'
        if entry.diarized
        else '<span class="badge badge-plain">no diarize</span>'
    )

    segments_html = []
    for seg in r.segments:
        time_str = html.escape(f"{_fmt_time(seg.start)} → {_fmt_time(seg.end)}")
        text_str = html.escape(seg.text)

        speaker_html = ""
        if seg.speaker:
            color = _speaker_color(seg.speaker)
            label = html.escape(seg.speaker)
            speaker_html = (
                f'<span class="speaker-badge" style="background:{color}">{label}</span>'
            )

        segments_html.append(f"""
        <div class="segment">
          <div class="segment-meta">
            <span class="time">{time_str}</span>
            {speaker_html}
          </div>
          <p class="seg-text">{text_str}</p>
        </div>""")

    body = "\n".join(segments_html)

    # Card title: use label if it differs from bare provider name
    title = html.escape(entry.label)

    return f"""
  <div class="card">
    <div class="card-header">
      <div class="card-title">
        <span class="provider-name">{title}</span>
        {diarize_badge}
      </div>
      <div class="card-stats">
        <span class="stat">🌐 {html.escape(r.language or "?")}</span>
        <span class="stat">⏱ {html.escape(_fmt_duration(r.duration))}</span>
        <span class="stat">📝 {len(r.segments)} segs</span>
      </div>
    </div>
    <div class="card-body">
      {body}
    </div>
  </div>"""


def _render_error_card(entry: BenchmarkEntry) -> str:
    is_skip = entry.error and "not configured" in entry.error
    icon = "🔑" if is_skip else "⚠️"
    msg_class = "skip-msg" if is_skip else "error-msg"
    body_class = "card-skipped" if is_skip else "card-error"

    return f"""
  <div class="card card-dim">
    <div class="card-header">
      <div class="card-title">
        <span class="provider-name">{html.escape(entry.label)}</span>
      </div>
    </div>
    <div class="{body_class}">
      <div class="state-icon">{icon}</div>
      <div class="{msg_class}">{html.escape(entry.error or "Unknown error")}</div>
    </div>
  </div>"""


# ── CSS ──────────────────────────────────────────────────────────────────────

_CSS = """
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
  background: #f1f5f9;
  color: #1e293b;
  min-height: 100vh;
}

/* ── HEADER ── */
header {
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
  color: #f8fafc;
  padding: 24px 32px;
  border-bottom: 2px solid #334155;
}
header h1 { font-size: 1.4rem; font-weight: 700; margin-bottom: 10px; letter-spacing: -0.02em; }
header h1 span { color: #64748b; font-weight: 400; }
.header-meta { display: flex; gap: 20px; font-size: 0.82rem; color: #94a3b8; flex-wrap: wrap; }
.header-meta span { display: flex; align-items: center; gap: 5px; }

/* ── MAIN ── */
main { padding: 24px 32px; }

/* ── GRID ── */
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(420px, 1fr));
  gap: 20px;
  align-items: start;
}

/* ── CARD ── */
.card {
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0,0,0,.07), 0 4px 16px rgba(0,0,0,.04);
  overflow: hidden;
  border: 1px solid #e2e8f0;
}
.card-dim { opacity: 0.7; }

.card-header {
  padding: 14px 18px;
  border-bottom: 1px solid #f1f5f9;
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 8px;
  background: #f8fafc;
}
.card-title { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.provider-name { font-size: 0.95rem; font-weight: 700; color: #0f172a; }

.badge {
  font-size: 0.68rem; font-weight: 600;
  padding: 2px 8px; border-radius: 20px;
  white-space: nowrap;
}
.badge-model   { background: #e0f2fe; color: #0369a1; }
.badge-diarize { background: #dcfce7; color: #166534; }
.badge-plain   { background: #fef9c3; color: #854d0e; }

.card-stats { display: flex; gap: 14px; font-size: 0.78rem; color: #64748b; }
.stat { display: flex; align-items: center; gap: 4px; }

/* ── CARD BODY ── */
.card-body {
  padding: 12px 18px;
  max-height: 560px;
  overflow-y: auto;
  scroll-behavior: smooth;
}
.card-body::-webkit-scrollbar { width: 4px; }
.card-body::-webkit-scrollbar-track { background: #f8fafc; }
.card-body::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 2px; }

/* ── SEGMENTS ── */
.segment {
  padding: 8px 0;
  border-bottom: 1px solid #f8fafc;
}
.segment:last-child { border-bottom: none; }
.segment-meta { display: flex; align-items: center; gap: 7px; margin-bottom: 4px; }

.time {
  font-size: 0.7rem;
  font-family: 'SF Mono', 'Fira Code', 'Consolas', monospace;
  color: #94a3b8;
  white-space: nowrap;
  min-width: 90px;
}
.speaker-badge {
  font-size: 0.68rem; font-weight: 700;
  padding: 1px 7px; border-radius: 3px;
  color: #fff; white-space: nowrap;
}
.seg-text {
  font-size: 0.88rem; color: #334155; line-height: 1.6;
  word-break: break-word;
}

/* ── ERROR / SKIP STATE ── */
.card-error, .card-skipped {
  padding: 32px 20px;
  display: flex; flex-direction: column; align-items: center;
  gap: 10px; text-align: center;
}
.state-icon { font-size: 2rem; }
.error-msg  { font-size: 0.82rem; color: #ef4444; max-width: 320px; line-height: 1.5; }
.skip-msg   { font-size: 0.82rem; color: #f59e0b; max-width: 320px; line-height: 1.5; }

@media (max-width: 860px) {
  main { padding: 16px; }
  header { padding: 18px 16px; }
  .grid { grid-template-columns: 1fr; }
}
"""


# ── Public API ───────────────────────────────────────────────────────────────

def generate_comparison_html(
    source_file: str,
    entries: list[BenchmarkEntry],
) -> str:
    filename = Path(source_file).name
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Duration from first successful result
    duration_str = "—"
    for e in entries:
        if e.result:
            duration_str = _fmt_duration(e.result.duration)
            break

    n_ok = sum(1 for e in entries if e.result is not None)
    n_total = len(entries)

    cards = "\n".join(
        _render_success_card(e) if e.result else _render_error_card(e)
        for e in entries
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>STT Benchmark — {html.escape(filename)}</title>
  <style>{_CSS}</style>
</head>
<body>
  <header>
    <h1>STT Benchmark <span>— {html.escape(filename)}</span></h1>
    <div class="header-meta">
      <span>📁 {html.escape(source_file)}</span>
      <span>⏱ {html.escape(duration_str)}</span>
      <span>🕐 {now}</span>
      <span>✅ {n_ok} / {n_total} providers</span>
    </div>
  </header>
  <main>
    <div class="grid">
      {cards}
    </div>
  </main>
</body>
</html>
"""
