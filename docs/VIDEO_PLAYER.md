Totally—let’s give VibeCraft a **main video player** that feels like a DAW meets a cinema viewer: clean, musical, and precise. Below is a production-ready spec + React component you can drop in now.

---

# 🎥 Main Video Player — UX & Features

### Core layout

* **Video canvas** (16:9, rounded, subtle glow)
* **HUD overlay** (title/timecode, quick actions)
* **Transport bar** with:

  * Play/Pause, timecode, scrubber
  * **Waveform** under the scrubber
  * **Beat markers** (from beat grid)
  * **Clip markers** (your time-based clips)
  * A/B loop (set **A**, set **B**, loop toggle)
* **Right controls:** volume, speed, captions/lyrics, quality (1080p), PiP, download

### Why musicians will love it

* Familiar DAW vibes (beats + clips on the timeline)
* Fast loop of problem areas (A/B loop)
* Lyrics/captions toggle for review
* Keyboard shortcuts for flow

---

## Props & Data (what you likely already have)

```ts
type Clip = {
  id: string;
  index: number;        // 0-based in final order
  startSec: number;
  endSec: number;
  thumbUrl?: string;    // optional thumbnail
};

type Beat = { t: number };  // seconds

type LyricLine = {
  t: number;            // start time in seconds
  text: string;
  dur?: number;         // optional duration
};
```

---

## React Component (TypeScript + Tailwind `vc-*` theme)

Create `MainVideoPlayer.tsx`:

```tsx
import React, { useEffect, useMemo, useRef, useState, KeyboardEvent } from "react";
import { Play, Pause, Volume2, VolumeX, SkipBack, SkipForward, Download, Settings, PictureInPicture2, Captions, Repeat, Scissors } from "lucide-react";
import clsx from "clsx";

/** Types */
export interface Clip { id: string; index: number; startSec: number; endSec: number; thumbUrl?: string; }
export interface Beat { t: number; }
export interface LyricLine { t: number; text: string; dur?: number; }

interface MainVideoPlayerProps {
  videoUrl: string;                // composed full video
  posterUrl?: string;
  durationSec: number;
  clips?: Clip[];                  // time-based clips
  beatGrid?: Beat[];               // beat timestamps
  lyrics?: LyricLine[];            // optional time-synced lines
  onDownload?: () => void;
  initialPlaybackRate?: number;    // default 1.0
}

export const MainVideoPlayer: React.FC<MainVideoPlayerProps> = ({
  videoUrl,
  posterUrl,
  durationSec,
  clips = [],
  beatGrid = [],
  lyrics = [],
  onDownload,
  initialPlaybackRate = 1.0,
}) => {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const railRef = useRef<HTMLDivElement | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [current, setCurrent] = useState(0);
  const [hoverSec, setHoverSec] = useState<number | null>(null);
  const [volume, setVolume] = useState(0.9);
  const [muted, setMuted] = useState(false);
  const [playbackRate, setPlaybackRate] = useState(initialPlaybackRate);
  const [pipSupported, setPipSupported] = useState(false);

  // A/B loop
  const [aMark, setAMark] = useState<number | null>(null);
  const [bMark, setBMark] = useState<number | null>(null);
  const [loopAB, setLoopAB] = useState(false);

  // Captions
  const [showLyrics, setShowLyrics] = useState(true);

  useEffect(() => {
    setPipSupported(!!(document as any).pictureInPictureEnabled);
  }, []);

  useEffect(() => {
    const v = videoRef.current;
    if (!v) return;
    const onTime = () => setCurrent(v.currentTime);
    v.addEventListener("timeupdate", onTime);
    v.volume = muted ? 0 : volume;
    v.playbackRate = playbackRate;
    return () => v.removeEventListener("timeupdate", onTime);
  }, [volume, muted, playbackRate]);

  // A/B loop enforcement
  useEffect(() => {
    const v = videoRef.current;
    if (!v || !loopAB || aMark == null || bMark == null) return;
    if (current >= bMark) v.currentTime = aMark;
  }, [current, loopAB, aMark, bMark]);

  const togglePlay = () => {
    const v = videoRef.current;
    if (!v) return;
    if (isPlaying) { v.pause(); setIsPlaying(false); }
    else { v.play(); setIsPlaying(true); }
  };

  const jump = (delta: number) => {
    const v = videoRef.current;
    if (!v) return;
    v.currentTime = clamp(v.currentTime + delta, 0, durationSec);
  };

  const setTimeFromRail = (clientX: number) => {
    if (!railRef.current) return;
    const rect = railRef.current.getBoundingClientRect();
    const ratio = clamp((clientX - rect.left) / rect.width, 0, 1);
    const t = ratio * durationSec;
    const v = videoRef.current;
    if (v) v.currentTime = t;
  };

  const onRailMouseMove = (e: React.MouseEvent) => {
    if (!railRef.current) return;
    const rect = railRef.current.getBoundingClientRect();
    const ratio = clamp((e.clientX - rect.left) / rect.width, 0, 1);
    setHoverSec(ratio * durationSec);
  };

  const onKey = (e: KeyboardEvent<HTMLDivElement>) => {
    if (e.target && (e.target as HTMLElement).tagName === "INPUT") return;
    switch (e.key) {
      case " ": e.preventDefault(); togglePlay(); break;
      case "j": jump(-5); break;
      case "l": jump(5); break;
      case "k": togglePlay(); break;
      case "ArrowLeft": jump(-1); break;
      case "ArrowRight": jump(1); break;
      case "ArrowUp": setVolume(v => clamp(v + 0.05, 0, 1)); setMuted(false); break;
      case "ArrowDown": setVolume(v => clamp(v - 0.05, 0, 1)); break;
      case "m": setMuted(m => !m); break;
      case "[": setPlaybackRate(r => clamp(r - 0.25, 0.25, 2)); break;
      case "]": setPlaybackRate(r => clamp(r + 0.25, 0.25, 2)); break;
      case "a": setAMark(current); break;
      case "b": setBMark(current); break;
      case "\\": setLoopAB(v => !v); break; // toggle A/B loop
      case "c": setShowLyrics(v => !v); break;
    }
  };

  const currentLyric = useMemo(() => {
    if (!lyrics.length) return null;
    // find the last line whose start <= current
    let i = lyrics.findIndex(l => l.t > current);
    i = i === -1 ? lyrics.length - 1 : Math.max(0, i - 1);
    const line = lyrics[i];
    if (!line) return null;
    if (line.dur != null && current > line.t + line.dur) return null;
    return line.text;
  }, [current, lyrics]);

  const currentRatio = durationSec ? (current / durationSec) : 0;

  return (
    <div className="vc-card p-0 overflow-hidden" onKeyDown={onKey} tabIndex={0}>
      {/* Video Canvas */}
      <div className="relative bg-black">
        <video
          ref={videoRef}
          src={videoUrl}
          poster={posterUrl}
          className="w-full aspect-video"
          onClick={togglePlay}
          onPlay={() => setIsPlaying(true)}
          onPause={() => setIsPlaying(false)}
          controls={false}
        />
        {/* HUD overlay: timecode + quick actions */}
        <div className="pointer-events-none absolute inset-0 flex items-end justify-between p-3">
          <div className="pointer-events-auto flex items-center gap-2">
            <TransportButton onClick={() => jump(-5)} title="Back 5s (J)">
              <SkipBack className="h-4 w-4" />
            </TransportButton>
            <TransportButton onClick={togglePlay} title="Play/Pause (Space/K)">
              {isPlaying ? <Pause className="h-5 w-5" /> : <Play className="h-5 w-5" />}
            </TransportButton>
            <TransportButton onClick={() => jump(5)} title="Forward 5s (L)">
              <SkipForward className="h-4 w-4" />
            </TransportButton>
            <span className="ml-2 text-[11px] text-white/90 bg-black/40 rounded px-1 py-0.5">
              {fmtTime(current)} / {fmtTime(durationSec)}
            </span>
          </div>

          <div className="pointer-events-auto flex items-center gap-2">
            <TransportButton
              onClick={() => setLoopAB(v => !v)}
              title="Toggle A/B Loop (\\)"
              selected={loopAB}
            >
              <Repeat className="h-4 w-4" />
            </TransportButton>

            <TransportButton onClick={() => setShowLyrics(v => !v)} title="Toggle Captions (C)" selected={showLyrics}>
              <Captions className="h-4 w-4" />
            </TransportButton>

            <div className="flex items-center gap-1 bg-black/40 rounded px-1.5 py-0.5">
              <button
                className="text-[11px] text-white/90 hover:text-white"
                onClick={() => setPlaybackRate(r => clamp(r - 0.25, 0.25, 2))}
                title="Slower ([)"
              >–</button>
              <span className="text-[11px] text-white/90 w-8 text-center">{playbackRate.toFixed(2)}x</span>
              <button
                className="text-[11px] text-white/90 hover:text-white"
                onClick={() => setPlaybackRate(r => clamp(r + 0.25, 0.25, 2))}
                title="Faster (])"
              >+</button>
            </div>

            <TransportButton
              onClick={() => setMuted(m => !m)}
              title={muted ? "Unmute (M)" : "Mute (M)"}
            >
              {muted || volume === 0 ? <VolumeX className="h-4 w-4" /> : <Volume2 className="h-4 w-4" />}
            </TransportButton>

            {pipSupported && (
              <TransportButton
                onClick={async () => {
                  const v = videoRef.current as any;
                  if (!v) return;
                  if (document.pictureInPictureElement) {
                    (document as any).exitPictureInPicture?.();
                  } else {
                    await v.requestPictureInPicture?.();
                  }
                }}
                title="Picture-In-Picture"
              >
                <PictureInPicture2 className="h-4 w-4" />
              </TransportButton>
            )}

            <TransportButton onClick={onDownload} title="Download">
              <Download className="h-4 w-4" />
            </TransportButton>

            <TransportButton title="Settings">
              <Settings className="h-4 w-4" />
            </TransportButton>
          </div>
        </div>

        {/* A/B markers overlay */}
        {(aMark != null || bMark != null) && (
          <div className="pointer-events-none absolute inset-x-0 bottom-20 h-0">
            {aMark != null && <MarkerPx time={aMark} duration={durationSec} color="bg-vc-accent-primary" />}
            {bMark != null && <MarkerPx time={bMark} duration={durationSec} color="bg-vc-accent-secondary" />}
          </div>
        )}

        {/* Lyrics overlay (subtle, centered bottom) */}
        {showLyrics && currentLyric && (
          <div className="pointer-events-none absolute inset-x-0 bottom-16 flex justify-center">
            <div className="px-3 py-1.5 rounded-md bg-black/50 text-white text-sm font-medium">
              {currentLyric}
            </div>
          </div>
        )}
      </div>

      {/* Timeline rail: scrubber + waveform + beats + clips */}
      <div
        ref={railRef}
        className="relative px-3 py-3 border-t border-vc-border bg-[rgba(255,255,255,0.02)]"
        onMouseMove={onRailMouseMove}
        onMouseLeave={() => setHoverSec(null)}
        onClick={(e) => setTimeFromRail(e.clientX)}
      >
        {/* Waveform placeholder (can swap in real waveform) */}
        <div className="h-10 rounded bg-[rgba(255,255,255,0.03)] relative overflow-hidden">
          <WaveBars duration={durationSec} />
          {/* Beat markers */}
          {beatGrid.map((b, i) => (
            <BeatTick key={i} t={b.t} duration={durationSec} />
          ))}
          {/* Clip spans */}
          {clips.map(c => (
            <ClipSpan key={c.id} start={c.startSec} end={c.endSec} duration={durationSec} index={c.index} />
          ))}
          {/* Playhead */}
          <Playhead t={current} duration={durationSec} />
          {/* Hover time indicator */}
          {hoverSec != null && <HoverTime t={hoverSec} duration={durationSec} />}
        </div>

        {/* A/B controls row */}
        <div className="mt-2 flex items-center gap-2">
          <span className="vc-badge">A/B Loop</span>
          <button className="vc-btn-secondary vc-btn-sm" onClick={() => setAMark(current)} title="Set A (a)">
            <Scissors className="h-3.5 w-3.5 mr-1" /> Set A
          </button>
          <button className="vc-btn-secondary vc-btn-sm" onClick={() => setBMark(current)} title="Set B (b)">
            <Scissors className="h-3.5 w-3.5 mr-1" /> Set B
          </button>
          <button className={clsx("vc-btn-sm", loopAB ? "vc-btn-primary" : "vc-btn-secondary")} onClick={() => setLoopAB(v => !v)}>
            {loopAB ? "Loop A↔B On" : "Loop A↔B Off"}
          </button>
          {(aMark != null || bMark != null) && (
            <span className="text-[11px] text-vc-text-muted ml-2">
              A: {aMark != null ? fmtTime(aMark) : "--:--"} • B: {bMark != null ? fmtTime(bMark) : "--:--"}
            </span>
          )}
        </div>
      </div>
    </div>
  );
};

/** Subcomponents */

const TransportButton: React.FC<{ onClick?: () => void; title?: string; selected?: boolean; children: React.ReactNode; }> =
({ onClick, title, selected, children }) => (
  <button
    className={clsx(
      "pointer-events-auto vc-icon-btn",
      selected && "vc-icon-btn-selected"
    )}
    onClick={onClick}
    title={title}
  >
    {children}
  </button>
);

const Playhead: React.FC<{ t: number; duration: number; }> = ({ t, duration }) => {
  const left = `${(t / duration) * 100}%`;
  return <div className="absolute inset-y-0 w-[2px] bg-white/90" style={{ left }} />;
};

const HoverTime: React.FC<{ t: number; duration: number; }> = ({ t, duration }) => {
  const left = `${(t / duration) * 100}%`;
  return (
    <div className="absolute -top-5" style={{ left }}>
      <div className="translate-x-[-50%] text-[10px] text-white/90 bg-black/60 rounded px-1 py-[1px]">
        {fmtTime(t)}
      </div>
    </div>
  );
};

const BeatTick: React.FC<{ t: number; duration: number; }> = ({ t, duration }) => {
  const left = `${(t / duration) * 100}%`;
  return <div className="absolute inset-y-0 w-[1px] bg-white/24" style={{ left }} />;
};

const ClipSpan: React.FC<{ start: number; end: number; duration: number; index: number; }> =
({ start, end, duration, index }) => {
  const left = `${(start / duration) * 100}%`;
  const width = `${((end - start) / duration) * 100}%`;
  return (
    <div
      className="absolute top-0 bottom-0 rounded-sm bg-gradient-to-r from-vc-accent-primary/20 to-vc-accent-tertiary/20 border border-vc-border/60"
      style={{ left, width }}
      title={`Clip #${index + 1}`}
    />
  );
};

const WaveBars: React.FC<{ duration: number; }> = () => {
  // decorative placeholder; replace with real waveform when ready
  const bars = Array.from({ length: 160 }, (_, i) => 0.3 + 0.35 * Math.sin(i / 5) ** 2);
  return (
    <div className="absolute inset-0 flex items-center gap-[2px] px-2">
      {bars.map((h, i) => (
        <div
          key={i}
          className="w-[2px] rounded-full bg-gradient-to-t from-vc-accent-primary/70 via-vc-accent-secondary/70 to-vc-accent-tertiary/70"
          style={{ height: `${h * 100}%`, opacity: 0.8 }}
        />
      ))}
    </div>
  );
};

const MarkerPx: React.FC<{ time: number; duration: number; color: string; }> = ({ time, duration, color }) => {
  const left = `${(time / duration) * 100}%`;
  return <div className={clsx("absolute w-[2px] h-6 rounded", color)} style={{ left }} />;
};

/** Utils */
function clamp(n: number, min: number, max: number) { return Math.max(min, Math.min(max, n)); }
function fmtTime(sec: number) {
  const s = Math.floor(Math.max(0, sec));
  const m = Math.floor(s / 60);
  const r = (s % 60).toString().padStart(2, "0");
  return `${m}:${r}`;
}
```

---

## Keyboard Shortcuts (built-in)

* **Space / K**: play/pause
* **J / L**: ±5s, **← / →**: ±1s
* **↑ / ↓**: volume up/down, **M**: mute
* **[ / ]**: playback speed −/+
* **A / B**: set A/B marks, **\**: toggle A/B loop
* **C**: captions/lyrics toggle

---

## How to use

```tsx
<MainVideoPlayer
  videoUrl={finalVideoUrl}
  posterUrl={poster}
  durationSec={analysis.durationSec}
  clips={plannedClips}
  beatGrid={beatGrid}
  lyrics={sectionLyricsMerged}   // optional
  onDownload={() => window.open(finalVideoUrl, "_blank")}
/>
```

---

## Notes / Options

* Replace `WaveBars` with a **real waveform** once you have amplitude samples.
* If your final render is 30 fps (recommended), you can still show **8 fps metadata** (frames per clip) in tooltips for transparency.
* For very long tracks, consider a **zoomable timeline** (1×/2×/4×).
* Add **hover preview thumbnails** by sampling every N seconds during composition (optional polish).

---

## Pending Tasks

- [x] 1. **Backend payload**
   - Extend `/songs/{id}/clips/status` (or add a dedicated endpoint) to include beat grid, clip boundaries, clip URLs/posters, and composed video metadata.
2. **Frontend data wiring**
   - Fetch the player payload after clip generation completes and pass it into the song profile; refetch on regeneration.
3. **Integrate `MainVideoPlayer`**
   - Render the component in the UI once clips (or a composed video) are available; wire up props (videoUrl, beatGrid, clips, lyrics).
4. **Timeline enhancements**
   - Highlight current clip, render clip spans over the waveform, enable seeking via clip taps or thumbnails, and show completed clip thumbnails in a strip.
5. **Clip actions**
   - Hook clip row “Preview/Regenerate” buttons to seek the player and trigger backend regeneration while keeping UI state in sync.
6. **Empty & error states**
   - Gracefully handle partial completion (mix of queued/processing/completed) and show messaging when no clips are ready.
7. **QA**
   - Validate keyboard shortcuts, loop behavior, captions toggle, and responsiveness on desktop/tablet; test long songs with many clips.

