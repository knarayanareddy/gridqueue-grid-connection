/**
 * Records the GridQueue demo video — video/script.md, 12 shots, exactly 170 s — from the static Pages build.
 *
 *   make demo-video            (= make build-pages, then this script)
 *   node --experimental-strip-types scripts/record-demo.ts [--plan] [--no-voiceover] [--no-captions] [--keep-raw]
 *
 * How it works
 *  - Serves frontend/dist (the `make build-pages` output) under /gridqueue-grid-connection/, like GitHub Pages.
 *  - Opens one "harness" page that holds every shot as a layer. Product shots embed the real app in same-origin
 *    iframes and drive it with Playwright (clicks, typing, scrolling); title, persona, diagram, terminal,
 *    LIMITATIONS and end shots are HTML cards built from repo files. One page means captions, push-ins and
 *    dissolves persist across shots without navigations.
 *  - A 1536×864 CSS-px layout scaled 1.25× in a 1920×1080 viewport = a 1080p frame at 125 % zoom (recordVideo
 *    captures CSS pixels and ignores deviceScaleFactor, so the zoom is a CSS scale, iframes included).
 *  - Playwright recordVideo captures it. A white pre-roll marks t=0; ffmpeg finds the first non-white frame, trims
 *    exactly 170 s, adds the fades, lays the voice-over (video/voiceover/*.mp3) on the shot timeline, and encodes
 *    docs/media/gridqueue-demo.mp4 (H.264/AAC) and .webm (VP9/Opus). Captions are burned in and also written to
 *    docs/media/gridqueue-demo.vtt.
 *  - Shot S09 shows the real output of the pytest command in the script, captured when the recording starts.
 *
 * Environment
 *  - CHROMIUM_PATH   use this Chromium binary (default: Playwright's own, `npx playwright-core install chromium`)
 *  - FFMPEG_PATH     use this ffmpeg (default: @ffmpeg-installer/ffmpeg)
 *  - PLAYWRIGHT_BROWSERS_PATH  where Playwright looks for its ffmpeg (recordVideo); linked automatically if missing
 */
import { spawnSync } from "node:child_process";
import { createServer, type Server } from "node:http";
import { createRequire } from "node:module";
import { existsSync, mkdirSync, readFileSync, rmSync, statSync, symlinkSync, writeFileSync } from "node:fs";
import { homedir } from "node:os";
import { dirname, extname, join, normalize, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import type { AddressInfo } from "node:net";
import type { Frame, Page } from "playwright-core";

const require = createRequire(import.meta.url);
const HERE = dirname(fileURLToPath(import.meta.url));
const REPO = resolve(HERE, "..");
const DIST = join(REPO, "frontend", "dist");
const PAGES_BASE = "/gridqueue-grid-connection/";
const SCRIPT_MD = join(REPO, "video", "script.md");
const VOICE_DIR = join(REPO, "video", "voiceover");
const OUT_DIR = join(REPO, "docs", "media");
const OUT_NAME = "gridqueue-demo";

const VIEW = { width: 1536, height: 864 }; // CSS px
const SCALE = 1.25; // 125 % zoom → 1920×1080
const FRAME = { width: 1920, height: 1080 };
const FPS = 25;
const RUNTIME_S = 170;
const FADE_S = 12 / FPS; // "12 frames" in the script = 0.48 s
const S09_COMMAND = "uv run --extra dev pytest tests/test_sandbox_pack.py -v -k withhold";

const args = new Set(process.argv.slice(2));
const PLAN_ONLY = args.has("--plan");
const WITH_VOICE = !args.has("--no-voiceover");
const WITH_CAPTIONS = !args.has("--no-captions");
const KEEP_RAW = args.has("--keep-raw");

// ---------------------------------------------------------------------------------------------- script.md

interface Shot {
  id: string;
  in: number;
  out: number;
  dur: number;
  transition: string;
  visual: string;
  vo: string;
}

function seconds(tc: string): number {
  const [m, s] = tc.split(":").map(Number);
  return m * 60 + s;
}

export function parseShots(md: string): Shot[] {
  const shots: Shot[] = [];
  const start = md.indexOf("\n## Shot list");
  if (start < 0) throw new Error("video/script.md: '## Shot list' section not found");
  const rest = md.slice(start + 1);
  const end = rest.indexOf("\n## ", 1);
  for (const line of (end < 0 ? rest : rest.slice(0, end)).split("\n")) {
    if (!/^\| S\d\d \|/.test(line)) continue;
    const c = line.split("|").slice(1, -1).map((x) => x.trim());
    if (c.length !== 8) throw new Error(`video/script.md: shot row has ${c.length} cells, expected 8: ${line.slice(0, 40)}`);
    shots.push({ id: c[0], in: seconds(c[1]), out: seconds(c[2]), dur: Number(c[3]), transition: c[4], visual: c[5], vo: c[6] });
  }
  if (shots.length !== 12) throw new Error(`video/script.md: expected 12 shots, found ${shots.length}`);
  shots.forEach((s, i) => {
    if (s.out - s.in !== s.dur) throw new Error(`${s.id}: in/out do not match its duration`);
    if (i > 0 && shots[i - 1].out !== s.in) throw new Error(`${s.id}: timecodes are not contiguous`);
  });
  if (shots[11].out !== RUNTIME_S) throw new Error(`video/script.md: runtime is ${shots[11].out} s, expected ${RUNTIME_S}`);
  return shots;
}

// ---------------------------------------------------------------------------------------------- voice-over

/**
 * Where each narration clip sits. 10 clips for 12 shots: S01+S02 and S08+S09 were synthesised as one clip each.
 * S01-S02 is split at the pause between the two lines (12.95 s) so S02's line starts on the title card.
 * S08-S09 plays unsplit from S08: S08's line is longer than its 10 s, so S09's line starts ~3 s into S09
 * (while the command is typed) and still ends inside it. `lead` = seconds after the shot's in-point.
 */
interface VoiceSegment {
  file: string;
  from?: number;
  to?: number;
  shots: string[];
  lead: number;
}

const VOICEOVER: VoiceSegment[] = [
  { file: "S01-S02.mp3", to: 12.95, shots: ["S01"], lead: 0.5 },
  { file: "S01-S02.mp3", from: 12.95, shots: ["S02"], lead: 0.05 },
  { file: "S03.mp3", shots: ["S03"], lead: 0.6 },
  { file: "S04.mp3", shots: ["S04"], lead: 0.5 },
  { file: "S05.mp3", shots: ["S05"], lead: 0.5 },
  { file: "S06.mp3", shots: ["S06"], lead: 0.8 },
  { file: "S07.mp3", shots: ["S07"], lead: 0.4 },
  { file: "S08-S09.mp3", shots: ["S08", "S09"], lead: 0.2 },
  { file: "S10.mp3", shots: ["S10"], lead: 0.4 },
  { file: "S11.mp3", shots: ["S11"], lead: 0.4 },
  { file: "S12.mp3", shots: ["S12"], lead: 0.3 },
];

interface PlacedVoice extends VoiceSegment {
  at: number;
  length: number;
  start: number;
  end: number;
}

interface Cue {
  start: number;
  end: number;
  text: string;
}

function ffmpegPath(): string {
  return process.env.FFMPEG_PATH || (require("@ffmpeg-installer/ffmpeg") as { path: string }).path;
}

function mediaDuration(file: string): number {
  const r = spawnSync(ffmpegPath(), ["-hide_banner", "-i", file], { encoding: "utf8" });
  const m = /Duration: (\d+):(\d+):([\d.]+)/.exec(r.stderr);
  if (!m) throw new Error(`cannot read the duration of ${file}`);
  return Number(m[1]) * 3600 + Number(m[2]) * 60 + Number(m[3]);
}

function placeVoice(shots: Shot[]): PlacedVoice[] {
  const byId = new Map(shots.map((s) => [s.id, s]));
  return VOICEOVER.map((v) => {
    const first = byId.get(v.shots[0])!;
    const last = byId.get(v.shots[v.shots.length - 1])!;
    const file = join(VOICE_DIR, v.file);
    if (!existsSync(file)) throw new Error(`missing voice-over clip ${file} (or pass --no-voiceover)`);
    const total = mediaDuration(file);
    const start = v.from ?? 0;
    const end = v.to ?? total;
    const at = first.in + v.lead;
    const placed = { ...v, at, start, end, length: end - start };
    if (at + placed.length > last.out + 0.001) {
      throw new Error(`${v.file}: ${placed.length.toFixed(2)} s from ${at.toFixed(2)} s overruns ${last.id} (ends ${last.out} s)`);
    }
    return placed;
  });
}

function sentences(text: string): string[] {
  return text
    .split(/(?<=[.!?])\s+/)
    .map((s) => s.trim())
    .filter(Boolean);
}

/** Caption cues: each sentence of a shot's narration, timed proportionally to its length inside its clip. */
function buildCues(shots: Shot[], voice: PlacedVoice[] | null): Cue[] {
  const byId = new Map(shots.map((s) => [s.id, s]));
  const cues: Cue[] = [];
  const segments: { from: number; to: number; text: string }[] = voice
    ? voice.map((v) => ({ from: v.at, to: v.at + v.length, text: v.shots.map((id) => byId.get(id)!.vo).join(" ") }))
    : shots.map((s) => ({ from: s.in + 0.3, to: s.out - 0.2, text: s.vo }));
  for (const seg of segments) {
    const parts = sentences(seg.text);
    const chars = parts.reduce((n, p) => n + p.length, 0);
    let t = seg.from;
    for (const p of parts) {
      const d = ((seg.to - seg.from) * p.length) / chars;
      cues.push({ start: t, end: t + d, text: p });
      t += d;
    }
  }
  // Hold each caption until the next one starts (max +0.6 s) so it does not flicker off between sentences.
  for (let i = 0; i < cues.length; i++) {
    const next = cues[i + 1]?.start ?? RUNTIME_S;
    cues[i].end = Math.min(next, cues[i].end + 0.6, RUNTIME_S);
  }
  return cues;
}

function vttTime(t: number): string {
  const ms = Math.round(t * 1000);
  const h = Math.floor(ms / 3600000);
  const m = Math.floor((ms % 3600000) / 60000);
  const s = Math.floor((ms % 60000) / 1000);
  const r = ms % 1000;
  return `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}.${String(r).padStart(3, "0")}`;
}

function toVtt(cues: Cue[]): string {
  return (
    "WEBVTT\n\n" +
    cues.map((c, i) => `${i + 1}\n${vttTime(c.start)} --> ${vttTime(c.end)}\n${c.text}\n`).join("\n")
  );
}

// ---------------------------------------------------------------------------------------------- content for HTML shots

function esc(s: string): string {
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

function inline(md: string): string {
  return esc(md)
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/(?<!\*)\*([^*\s][^*]*)\*(?!\*)/g, "<em>$1</em>")
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a>$1</a>');
}

/** Just enough Markdown for LIMITATIONS.md §1-§3: headings, quote, rule, bullets, tables, inline marks. */
export function markdownToHtml(md: string): string {
  const lines = md.split("\n");
  const out: string[] = [];
  let i = 0;
  while (i < lines.length) {
    const line = lines[i];
    const h = /^(#{1,3}) (.*)$/.exec(line);
    if (h) {
      const id = h[2].match(/^(\d)\./)?.[1];
      out.push(`<h${h[1].length}${id ? ` id="md-s${id}"` : ""}>${inline(h[2])}</h${h[1].length}>`);
      i++;
    } else if (line.startsWith(">")) {
      const buf: string[] = [];
      while (i < lines.length && lines[i].startsWith(">")) buf.push(lines[i++].replace(/^>\s?/, ""));
      out.push(`<blockquote>${inline(buf.join(" "))}</blockquote>`);
    } else if (/^---\s*$/.test(line)) {
      out.push("<hr>");
      i++;
    } else if (line.startsWith("- ")) {
      const items: string[] = [];
      while (i < lines.length && (lines[i].startsWith("- ") || /^\s{2,}\S/.test(lines[i]))) {
        if (lines[i].startsWith("- ")) items.push(lines[i].slice(2));
        else items[items.length - 1] += " " + lines[i].trim();
        i++;
      }
      out.push(`<ul>${items.map((it) => `<li>${inline(it)}</li>`).join("")}</ul>`);
    } else if (line.startsWith("|")) {
      const rows: string[][] = [];
      while (i < lines.length && lines[i].startsWith("|")) {
        const cells = lines[i].split("|").slice(1, -1).map((c) => c.trim());
        if (!cells.every((c) => /^:?-+:?$/.test(c))) rows.push(cells);
        i++;
      }
      const [head, ...body] = rows;
      out.push(
        `<table><thead><tr>${head.map((c) => `<th>${inline(c)}</th>`).join("")}</tr></thead><tbody>${body
          .map((r) => `<tr>${r.map((c) => `<td>${inline(c)}</td>`).join("")}</tr>`)
          .join("")}</tbody></table>`,
      );
    } else if (line.trim() === "") {
      i++;
    } else {
      const buf: string[] = [];
      while (i < lines.length && lines[i].trim() !== "" && !/^(#|>|- |\|)/.test(lines[i])) buf.push(lines[i++]);
      out.push(`<p>${inline(buf.join(" "))}</p>`);
    }
  }
  return out.join("\n");
}

function limitationsHtml(): string {
  const md = readFileSync(join(REPO, "LIMITATIONS.md"), "utf8");
  const end = md.indexOf("\n## 4.");
  if (end < 0) throw new Error("LIMITATIONS.md: section 4 heading not found");
  return markdownToHtml(md.slice(0, end));
}

function capturePytest(): string[] {
  const r = spawnSync("uv", ["run", "--extra", "dev", "pytest", "tests/test_sandbox_pack.py", "-v", "-k", "withhold", "-p", "no:cacheprovider", "--color=no"], {
    cwd: join(REPO, "backend"),
    encoding: "utf8",
  });
  if (r.error) throw new Error(`S09 needs uv on PATH to run the real tests: ${r.error.message}`);
  if (r.status !== 0) throw new Error(`S09: the withholding tests failed (exit ${r.status}):\n${r.stdout}\n${r.stderr}`);
  const lines = r.stdout.trimEnd().split("\n");
  if (!/passed/.test(lines[lines.length - 1])) throw new Error("S09: pytest output has no 'passed' summary line");
  return lines;
}

// ---------------------------------------------------------------------------------------------- harness page

function fontsCss(): string {
  const faces: [string, string, string][] = [
    ["Inter", "@fontsource-variable/inter", "inter"],
    ["Plus Jakarta Sans", "@fontsource-variable/plus-jakarta-sans", "plus-jakarta-sans"],
    ["JetBrains Mono", "@fontsource-variable/jetbrains-mono", "jetbrains-mono"],
  ];
  return faces
    .flatMap(([family, , file]) =>
      ["latin", "latin-ext"].map(
        (sub) =>
          `@font-face{font-family:'${family}';font-style:normal;font-display:block;font-weight:100 900;` +
          `src:url(/__rec/fonts/${file}-${sub}-wght-normal.woff2) format('woff2');` +
          (sub === "latin"
            ? "unicode-range:U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD;}"
            : "unicode-range:U+0100-02BA,U+02BD-02C5,U+02C7-02CC,U+02CE-02D7,U+02DD-02FF,U+0304,U+0308,U+0329,U+1D00-1DBF,U+1E00-1E9F,U+1EF2-1EFF,U+2020,U+20A0-20AB,U+20AD-20C0,U+2113,U+2C60-2C7F,U+A720-A7FF;}"),
      ),
    )
    .join("\n");
}

function fontFile(name: string): string | null {
  const m = /^([a-z-]+?)-(latin|latin-ext)-wght-normal\.woff2$/.exec(name);
  if (!m) return null;
  const pkg = { inter: "inter", "plus-jakarta-sans": "plus-jakarta-sans", "jetbrains-mono": "jetbrains-mono" }[m[1]];
  if (!pkg) return null;
  return join(dirname(require.resolve(`@fontsource-variable/${pkg}/package.json`)), "files", name);
}

const app = (q: string) => `${PAGES_BASE}?${q}`;

function harnessHtml(pytest: string[]): string {
  const term = JSON.stringify(pytest);
  return `<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>GridQueue demo harness</title>
<link rel="stylesheet" href="/__rec/tokens.css"><link rel="stylesheet" href="/__rec/fonts.css">
<style>
*{box-sizing:border-box}
html,body{margin:0;height:100%;overflow:hidden;background:var(--color-bg-primary);color:var(--color-text-primary);font-family:var(--font-body);-webkit-font-smoothing:antialiased}
#stage{position:relative;width:${VIEW.width}px;height:${VIEW.height}px;overflow:hidden;transform:scale(${SCALE});transform-origin:0 0}
.layer{position:absolute;inset:0;opacity:0;visibility:hidden;background:var(--color-bg-primary)}
.layer.on{opacity:1;visibility:visible}
.zoom{position:absolute;inset:0;transform-origin:50% 0}
.zoom iframe,.win iframe{border:0;display:block;width:100%;height:100%;background:var(--color-bg-primary)}
#sync{position:absolute;inset:0;background:#fff;z-index:50}
#caption{position:absolute;left:50%;bottom:22px;transform:translateX(-50%);max-width:1240px;z-index:40;padding:10px 22px;border-radius:10px;
  background:color-mix(in srgb,var(--color-bg-primary) 86%,transparent);border:1px solid var(--color-border);font-size:25px;line-height:1.35;text-align:center;
  font-weight:500;opacity:0;transition:opacity 120ms linear}
#caption.on{opacity:1}
#tag{position:absolute;top:14px;left:16px;z-index:41;padding:5px 12px;border-radius:999px;border:1.5px dashed var(--color-congested);
  background:color-mix(in srgb,var(--color-bg-primary) 88%,transparent);font-size:14px;font-weight:600;letter-spacing:.02em;opacity:0;transition:opacity 200ms}
#tag.on{opacity:1}
.eyebrow{font-size:15px;font-weight:600;letter-spacing:.12em;text-transform:uppercase;color:var(--color-text-secondary)}
.brand{display:flex;align-items:center;gap:18px;font-family:var(--font-display);font-weight:700;letter-spacing:-.01em}
.mark{width:26px;height:26px;border-radius:5px;background:var(--color-grid-blue);box-shadow:11px 11px 0 -4px var(--color-available)}
.reveal{opacity:0;transform:translateY(10px);transition:opacity 500ms ease,transform 500ms ease}
.reveal.in{opacity:1;transform:none}

/* S01 persona */
#L-persona .wrap{position:absolute;inset:0;display:grid;grid-template-columns:1.1fr .9fr;align-items:center;padding:0 96px 120px;gap:64px}
#L-persona h1{font-family:var(--font-display);font-size:50px;line-height:1.15;margin:18px 0 30px;letter-spacing:-.015em}
#L-persona .line{font-size:28px;line-height:1.4;margin:0 0 16px;color:var(--color-text-primary)}
#L-persona .line b{color:var(--color-congested);font-weight:600}
.roof{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;padding:26px;border-radius:14px;background:var(--color-bg-secondary);border:1px solid var(--color-border);transform:perspective(900px) rotateX(18deg)}
.panel{aspect-ratio:1.6;border-radius:4px;border:1.5px solid var(--color-border);background:var(--color-bg-card);transition:background 300ms,border-color 300ms}
.panel.lit{background:color-mix(in srgb,var(--color-grid-blue) 55%,var(--color-bg-card));border-color:var(--color-grid-blue)}
.kw{margin-top:26px;font-family:var(--font-mono);font-size:22px;color:var(--color-text-secondary);text-align:center}
.kw strong{color:var(--color-text-primary);font-size:30px}
.grid-q{margin-top:10px;text-align:center;font-size:20px;color:var(--color-congested);font-weight:600}
.lower3{position:absolute;left:96px;bottom:110px;padding:12px 20px;border-left:4px solid var(--color-grid-blue);background:var(--color-bg-secondary);font-size:22px;font-weight:600}
.lower3 span{color:var(--color-text-secondary);font-weight:500}

/* S02 title */
#L-title .wrap{position:absolute;inset:0;display:flex;flex-direction:column;justify-content:center;padding:0 140px 80px}
#L-title .brand{font-size:76px}
#L-title p{font-family:var(--font-display);font-size:38px;line-height:1.3;margin:28px 0 0;color:var(--color-text-secondary);max-width:1100px}

/* S03 split */
#L-split .pair{position:absolute;top:22px;left:24px;right:24px;bottom:104px;display:grid;grid-template-columns:1fr 1fr;gap:24px}
.win{display:flex;flex-direction:column;border-radius:12px;overflow:hidden;border:1.5px solid var(--color-border);background:var(--color-bg-primary);transition:border-color 300ms,box-shadow 300ms}
.win.focus{border-color:var(--color-grid-blue);box-shadow:0 0 0 3px color-mix(in srgb,var(--color-grid-blue) 35%,transparent)}
.win .bar{display:flex;align-items:center;gap:12px;height:40px;padding:0 14px;background:var(--color-bg-secondary);border-bottom:1px solid var(--color-border);font-size:15px}
.win .bar b{font-weight:700}
.win .bar .url{margin-left:auto;font-family:var(--font-mono);font-size:12px;color:var(--color-text-secondary)}
.win .body{flex:1;min-height:0}

/* S07/S08 architecture */
#L-arch .wrap{position:absolute;inset:0;padding:56px 48px 0}
#L-arch h2{font-family:var(--font-display);font-size:30px;margin:8px 0 46px}
.flow{display:grid;grid-template-columns:repeat(6,1fr);gap:34px;align-items:stretch}
.node{position:relative;padding:18px 16px;border-radius:12px;background:var(--color-bg-card);border:1.5px solid var(--color-border);min-height:228px;opacity:.18;transition:opacity 450ms,border-color 450ms,transform 450ms;transform:translateY(8px)}
.node.on{opacity:1;transform:none}
.node.hot{border-color:var(--color-grid-blue)}
.node.gate.hot{border-color:var(--color-available);box-shadow:0 0 0 3px color-mix(in srgb,var(--color-available) 25%,transparent)}
.node:not(:last-child)::after{content:"";position:absolute;right:-28px;top:50%;width:22px;height:2px;background:var(--color-text-secondary)}
.node:not(:last-child)::before{content:"";position:absolute;right:-29px;top:calc(50% - 5px);border:6px solid transparent;border-left:8px solid var(--color-text-secondary);border-right:0}
.node .n{font-family:var(--font-mono);font-size:13px;color:var(--color-text-secondary)}
.node h3{font-family:var(--font-display);font-size:22px;line-height:1.2;margin:8px 0 10px}
.node p{margin:0;font-size:16px;line-height:1.4;color:var(--color-text-secondary)}
.node ul{margin:12px 0 0;padding:0;list-style:none;font-size:15px}
.node li{padding:3px 0;opacity:0;transition:opacity 300ms}
.node li.in{opacity:1}
.node li::before{content:"";display:inline-block;width:8px;height:8px;margin-right:8px;border-radius:2px;background:var(--color-available)}
.node .replay{position:absolute;left:16px;bottom:14px;font-size:12px;font-weight:600;padding:2px 8px;border-radius:999px;border:1.5px dashed var(--color-congested);opacity:0;transition:opacity 300ms}
.honest .node.live{border-style:dashed;border-color:var(--color-congested)}
.honest .node.live .replay{opacity:1}
.card8{position:absolute;left:48px;right:48px;top:520px;padding:20px 26px;border-radius:12px;background:var(--color-bg-secondary);border-left:5px solid var(--color-congested);opacity:0;transform:translateY(12px);transition:opacity 400ms,transform 400ms}
.honest .card8{opacity:1;transform:none}
.card8 .t{font-size:26px;font-weight:700}
.card8 .s{margin-top:6px;font-size:18px;color:var(--color-text-secondary)}

/* S09 terminal */
#L-term .win{position:absolute;top:30px;left:40px;right:40px;bottom:110px}
#term{flex:1;padding:18px 22px;font-family:var(--font-mono);font-size:18px;line-height:1.5;white-space:pre-wrap;word-break:break-all;overflow:hidden;background:var(--color-bg-primary)}
#term .p{color:var(--color-available)}
#term .ok{color:var(--color-available)}
#term .dim{color:var(--color-text-secondary)}
#term .cur{display:inline-block;width:10px;height:1.1em;vertical-align:-3px;background:var(--color-text-primary)}

/* S11 LIMITATIONS.md */
#L-limits .win{position:absolute;top:24px;left:120px;right:120px;bottom:100px}
#doc{flex:1;overflow:hidden;padding:10px 46px 200px;background:var(--color-bg-primary);font-size:19px;line-height:1.55}
#doc h1{font-family:var(--font-display);font-size:34px;margin:22px 0 14px}
#doc h2{font-family:var(--font-display);font-size:27px;margin:34px 0 12px;padding-bottom:8px;border-bottom:1px solid var(--color-border)}
#doc blockquote{margin:0;padding:4px 18px;border-left:4px solid var(--color-border);color:var(--color-text-secondary)}
#doc hr{border:0;border-top:1px solid var(--color-border);margin:22px 0}
#doc li{margin:0 0 10px}
#doc code{font-family:var(--font-mono);font-size:.85em;padding:1px 6px;border-radius:5px;background:var(--color-bg-card)}
#doc table{border-collapse:collapse;width:100%;font-size:16px}
#doc th,#doc td{border:1px solid var(--color-border);padding:7px 10px;text-align:left;vertical-align:top}
#doc th{background:var(--color-bg-secondary)}

/* S12 end */
#L-end .wrap{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:26px;padding-bottom:90px;text-align:center}
#L-end .brand{font-size:58px}
#L-end .url{font-family:var(--font-mono);font-size:30px}
#L-end .warn{font-size:24px;font-weight:600;padding:8px 20px;border-radius:999px;border:2px dashed var(--color-congested)}
#L-end .fine{font-size:17px;color:var(--color-text-secondary);line-height:1.6}
</style></head>
<body><div id="stage">
<section class="layer" id="L-persona"><div class="wrap">
  <div>
    <div class="eyebrow">Persona (illustrative)</div>
    <h1>A 60 kW solar plan, and a grid that &ldquo;has no capacity&rdquo;</h1>
    <p class="line reveal" data-at="0.6">Wants <strong>60 kW</strong> of solar on the workshop roof.</p>
    <p class="line reveal" data-at="4.4">His installer: <b>&ldquo;the grid has no capacity.&rdquo;</b></p>
    <p class="line reveal" data-at="7.6">True? For how long? What can he do instead?</p>
  </div>
  <div><div class="roof">${Array.from({ length: 12 }, () => '<div class="panel"></div>').join("")}</div>
  <div class="kw"><strong id="kwn">0</strong> / 60 kW planned</div><div class="grid-q reveal" data-at="4.4">Grid connection: unknown</div></div>
</div><div class="lower3">Persona (illustrative): <span>Ruud, metalworking shop, Brabant</span></div></section>

<section class="layer" id="L-title"><div class="wrap">
  <div class="brand"><span class="mark"></span>GridQueue</div>
  <p>Answers in the operator's own words, or an honest &lsquo;we don't know&rsquo;.</p>
</div></section>

<section class="layer" id="L-split"><div class="pair">
  <div class="win" id="win-l"><div class="bar"><b>Feed-in</b><span class="muted">5612 AB · 60 kW</span><span class="url">…/gridqueue-grid-connection/?postcode=5612&amp;direction=feed_in</span></div>
    <div class="body"><iframe id="split-l" src="${app("postcode=5612&direction=feed_in&embed=1")}"></iframe></div></div>
  <div class="win" id="win-r"><div class="bar"><b>Consumption</b><span>5612 AB · 60 kW</span><span class="url">…/gridqueue-grid-connection/?postcode=5612&amp;direction=consumption</span></div>
    <div class="body"><iframe id="split-r" src="${app("postcode=5612&direction=consumption&embed=1")}"></iframe></div></div>
</div></section>

<section class="layer" id="L-app1"><div class="zoom"><iframe id="app1" src="${app("postcode=5612%20AB&direction=feed_in")}"></iframe></div></section>
<section class="layer" id="L-app2"><div class="zoom"><iframe id="app2" src="${PAGES_BASE}"></iframe></div></section>
<section class="layer" id="L-app3"><div class="zoom"><iframe id="app3" src="${app("tab=ab")}"></iframe></div></section>

<section class="layer" id="L-arch"><div class="wrap">
  <div class="eyebrow">How an answer is made</div>
  <h2>Retrieval and the model propose. A gate in plain Python decides.</h2>
  <div class="flow">
    <div class="node" data-step="0"><div class="n">input</div><h3>Postcode, kW, direction</h3><p>5612 AB · 60 kW · feed-in</p></div>
    <div class="node" data-step="1"><div class="n">S1</div><h3>Grid operator</h3><p>Static cited table. No model.</p></div>
    <div class="node live" data-step="2"><div class="n">S2</div><h3>Tavily</h3><p>Search and extract on the operator's own domain only. sha256 per document.</p><span class="replay">fixtures in this demo</span></div>
    <div class="node live" data-step="3"><div class="n">S3</div><h3>Nemotron Ultra</h3><p>On Nebius Token Factory. Claims as structured output.</p><span class="replay">replayed in this demo</span></div>
    <div class="node gate" data-step="4"><div class="n">S5 · gate</div><h3>Deterministic gate</h3><p>Plain Python. No model.</p>
      <ul><li>quote is in the source</li><li>date is in the quote</li><li>kW is in the quote</li></ul></div>
    <div class="node" data-step="5"><div class="n">answer</div><h3>Direction Card</h3><p>Operator quote, source, retrieval time, sha256. Or a refusal.</p></div>
  </div>
  <div class="card8"><div class="t">Not yet run: live API calls · Token Factory Sandbox · Serverless Job</div>
    <div class="s">This demo replays recorded model output over SYNTHETIC documents. The code for all three is built and unit-tested.</div></div>
</div></section>

<section class="layer" id="L-term"><div class="win"><div class="bar"><b>Terminal</b><span class="url">~/gridqueue-grid-connection/backend</span></div><div id="term"></div></div></section>

<section class="layer" id="L-limits"><div class="win"><div class="bar"><b>LIMITATIONS.md</b><span class="url">github.com/knarayanareddy/gridqueue-grid-connection</span></div>
  <div id="doc">${limitationsHtml()}</div></div></section>

<section class="layer" id="L-end"><div class="wrap">
  <div class="brand"><span class="mark"></span>GridQueue</div>
  <div class="url">github.com/knarayanareddy/gridqueue-grid-connection</div>
  <div class="warn">Not legal or connection advice</div>
  <div class="fine">Demo data: SYNTHETIC fixture documents · Narration: synthetic voice (text-to-speech)<br>Static demo: knarayanareddy.github.io/gridqueue-grid-connection</div>
</div></section>

<div id="tag">SYNTHETIC data</div>
<div id="caption"></div>
<div id="sync"></div>
</div>
<script>
const $ = (s) => document.querySelector(s);
const PYTEST = ${term};
const ease = (t) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);
function tween(ms, step) {
  return new Promise((done) => {
    const t0 = performance.now();
    (function f(now) { const k = Math.min(1, (now - t0) / ms); step(ease(k)); k < 1 ? requestAnimationFrame(f) : done(); })(t0);
  });
}
window.rec = {
  t0: 0,
  start(cues, captions) {
    this.t0 = performance.now();
    $("#sync").remove();
    if (!captions) return;
    const cap = $("#caption");
    let shown = -1;
    const tick = () => {
      const t = (performance.now() - this.t0) / 1000;
      const i = cues.findIndex((c) => t >= c.start && t < c.end);
      if (i !== shown) { shown = i; if (i < 0) cap.classList.remove("on"); else { cap.textContent = cues[i].text; cap.classList.add("on"); } }
      requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  },
  show(id, mode) {
    const next = document.getElementById(id);
    const cur = [...document.querySelectorAll(".layer.on")].filter((l) => l !== next);
    if (mode === "dissolve") {
      next.style.zIndex = 2; next.style.transition = "none"; next.style.opacity = 0; next.style.visibility = "visible";
      next.classList.add("on"); void next.offsetWidth;
      next.style.transition = "opacity ${Math.round(FADE_S * 1000)}ms linear"; next.style.opacity = 1;
      setTimeout(() => { cur.forEach((l) => l.classList.remove("on")); next.style.cssText = ""; }, ${Math.round(FADE_S * 1000) + 40});
    } else { cur.forEach((l) => l.classList.remove("on")); next.classList.add("on"); }
  },
  tag(on) { $("#tag").classList.toggle("on", on); },
  reveal(root) {
    root.querySelectorAll(".reveal").forEach((el) => setTimeout(() => el.classList.add("in"), Number(el.dataset.at) * 1000));
  },
  persona() {
    const L = $("#L-persona"); this.reveal(L);
    const panels = [...L.querySelectorAll(".panel")]; const kw = $("#kwn");
    panels.forEach((p, i) => setTimeout(() => { p.classList.add("lit"); kw.textContent = String((i + 1) * 5); }, 700 + i * 260));
  },
  zoom(layer, scale, ms, origin) {
    const z = document.querySelector("#" + layer + " .zoom");
    if (origin) z.style.transformOrigin = origin;
    z.style.transition = ms ? "transform " + ms + "ms cubic-bezier(.33,0,.67,1)" : "none";
    z.style.transform = "scale(" + scale + ")";
  },
  scrollFrame(id, selector, offset, ms) {
    const w = document.getElementById(id).contentWindow;
    const el = w.document.querySelector(selector);
    if (!el) throw new Error("scrollFrame: " + selector + " not found in " + id);
    const from = w.scrollY; const to = Math.max(0, el.getBoundingClientRect().top + from - offset);
    if (!ms) { w.scrollTo(0, to); return; }
    return tween(ms, (k) => w.scrollTo(0, from + (to - from) * k));
  },
  focusWin(side) { $("#win-l").classList.toggle("focus", side === "l"); $("#win-r").classList.toggle("focus", side === "r"); },
  arch(step) {
    const nodes = [...document.querySelectorAll(".node")];
    nodes.forEach((n) => { const s = Number(n.dataset.step); n.classList.toggle("on", s <= step); n.classList.toggle("hot", s === step); });
    if (step === 4) document.querySelectorAll(".gate li").forEach((li, i) => setTimeout(() => li.classList.add("in"), 900 + i * 900));
  },
  honest() { $("#L-arch").classList.add("honest"); document.querySelectorAll(".node").forEach((n) => n.classList.remove("hot")); },
  terminal(cmd) {
    const el = $("#term");
    const esc = (s) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;");
    const prompt = '<span class="p">~/gridqueue-grid-connection/backend $</span> ';
    let typed = "";
    const paint = (extra) => { el.innerHTML = prompt + esc(typed) + extra; };
    paint('<span class="cur"></span>');
    const perChar = 1900 / cmd.length;
    [...cmd].forEach((ch, i) => setTimeout(() => { typed += ch; paint('<span class="cur"></span>'); }, 300 + i * perChar));
    const head = PYTEST.filter((l) => !l.includes("::"));
    const tests = PYTEST.filter((l) => l.includes("::"));
    const summary = head.pop();
    const fmt = (l) => esc(l).replace(/ PASSED/, ' <span class="ok">PASSED</span>').replace(/(\\[ *\\d+%\\])/, '<span class="dim">$1</span>');
    let out = "";
    const add = (html, at) => setTimeout(() => { out += html + "\\n"; el.innerHTML = prompt + esc(typed) + "\\n" + out + '<span class="cur"></span>'; }, at);
    add("", 2500);
    head.forEach((l, i) => add('<span class="dim">' + esc(l) + "</span>", 2700 + i * 60));
    tests.forEach((l, i) => add(fmt(l), 3400 + i * 260));
    add('<span class="ok">' + esc(summary) + "</span>", 3400 + tests.length * 260 + 300);
  },
  async limits() {
    const doc = $("#doc");
    const top = (id) => document.getElementById(id).getBoundingClientRect().top - doc.getBoundingClientRect().top + doc.scrollTop - 12;
    doc.scrollTop = top("md-s1");
    await new Promise((r) => setTimeout(r, 2900));
    const a = doc.scrollTop, b = a + 230;
    await tween(1500, (k) => (doc.scrollTop = a + (b - a) * k));
    await new Promise((r) => setTimeout(r, 1200));
    const c = doc.scrollTop, d = top("md-s3");
    await tween(1900, (k) => (doc.scrollTop = c + (d - c) * k));
  },
};
</script></body></html>`;
}

// ---------------------------------------------------------------------------------------------- static server

const MIME: Record<string, string> = {
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".svg": "image/svg+xml",
  ".png": "image/png",
  ".woff2": "font/woff2",
  ".ico": "image/x-icon",
};

function serve(harness: string): Promise<{ server: Server; origin: string }> {
  const tokens = readFileSync(join(REPO, "frontend", "src", "tokens.css"), "utf8");
  const fonts = fontsCss();
  const server = createServer((req, res) => {
    const url = new URL(req.url ?? "/", "http://x");
    const send = (status: number, type: string, body: string | Buffer) => {
      res.writeHead(status, { "Content-Type": type, "Cache-Control": "no-store" });
      res.end(body);
    };
    if (url.pathname === "/__rec/harness.html") return send(200, MIME[".html"], harness);
    if (url.pathname === "/__rec/tokens.css") return send(200, MIME[".css"], tokens);
    if (url.pathname === "/__rec/fonts.css") return send(200, MIME[".css"], fonts);
    if (url.pathname.startsWith("/__rec/fonts/")) {
      const f = fontFile(url.pathname.slice("/__rec/fonts/".length));
      return f && existsSync(f) ? send(200, MIME[".woff2"], readFileSync(f)) : send(404, "text/plain", "no font");
    }
    if (!url.pathname.startsWith(PAGES_BASE)) return send(404, "text/plain", "not found");
    let rel = normalize(decodeURIComponent(url.pathname.slice(PAGES_BASE.length)));
    if (rel.startsWith("..")) return send(403, "text/plain", "forbidden");
    let file = join(DIST, rel);
    if (!rel || rel === "." || (existsSync(file) && statSync(file).isDirectory())) file = join(file, "index.html");
    if (!existsSync(file)) return send(404, "text/plain", "not found");
    send(200, MIME[extname(file)] ?? "application/octet-stream", readFileSync(file));
  });
  return new Promise((ok) =>
    server.listen(0, "127.0.0.1", () => ok({ server, origin: `http://127.0.0.1:${(server.address() as AddressInfo).port}` })),
  );
}

// ---------------------------------------------------------------------------------------------- recording

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

/** Playwright's recordVideo needs its own ffmpeg build; link the static ffmpeg there if it is missing. */
function ensurePlaywrightFfmpeg(): void {
  if (process.platform !== "linux" || process.arch !== "x64") return;
  const browsers = JSON.parse(readFileSync(join(dirname(require.resolve("playwright-core")), "browsers.json"), "utf8")) as {
    browsers: { name: string; revision: string }[];
  };
  const rev = browsers.browsers.find((b) => b.name === "ffmpeg")?.revision;
  if (!rev) return;
  const root = process.env.PLAYWRIGHT_BROWSERS_PATH || join(homedir(), ".cache", "ms-playwright");
  const target = join(root, `ffmpeg-${rev}`, "ffmpeg-linux");
  if (existsSync(target)) return;
  mkdirSync(dirname(target), { recursive: true });
  symlinkSync(ffmpegPath(), target);
  console.log(`linked ${ffmpegPath()} -> ${target} (Playwright recordVideo)`);
}

async function frameOf(page: Page, id: string): Promise<Frame> {
  const handle = await page.$(`#${id}`);
  const frame = await handle?.contentFrame();
  if (!frame) throw new Error(`iframe #${id} has no frame`);
  return frame;
}

interface ShotLog {
  id: string;
  planned: number;
  started: number;
  late: number;
}

async function record(shots: Shot[], cues: Cue[], pytest: string[]): Promise<{ raw: string; log: ShotLog[] }> {
  const { chromium } = await import("playwright-core");
  ensurePlaywrightFfmpeg();
  const { server, origin } = await serve(harnessHtml(pytest));
  const rawDir = join(OUT_DIR, ".raw");
  rmSync(rawDir, { recursive: true, force: true });
  const browser = await chromium.launch({
    executablePath: process.env.CHROMIUM_PATH || undefined,
    args: ["--hide-scrollbars", "--font-render-hinting=none", "--force-color-profile=srgb"],
  });
  // recordVideo captures CSS pixels and ignores deviceScaleFactor, so the 125 % zoom is a CSS scale of the
  // 1536×864 stage inside a 1920×1080 viewport (iframes included); text is rasterised at the final size.
  const context = await browser.newContext({
    viewport: FRAME,
    deviceScaleFactor: 1,
    colorScheme: "dark",
    reducedMotion: "no-preference",
    recordVideo: { dir: rawDir, size: FRAME },
  });
  await context.grantPermissions(["clipboard-read", "clipboard-write"], { origin });
  // The app's tokens name Inter / Plus Jakarta Sans / JetBrains Mono with system fallbacks; give the recording those
  // fonts (the design system's own) instead of whatever the recording machine has. Also hide scrollbars.
  await context.addInitScript(() => {
    if (!location.pathname.startsWith("/gridqueue-grid-connection/")) return;
    document.addEventListener("DOMContentLoaded", () => {
      const l = document.createElement("link");
      l.rel = "stylesheet";
      l.href = "/__rec/fonts.css";
      document.head.appendChild(l);
      const s = document.createElement("style");
      s.textContent = "html{scrollbar-width:none}::-webkit-scrollbar{display:none}";
      document.head.appendChild(s);
    });
  });
  const page = await context.newPage();
  page.on("pageerror", (e) => console.error("page error:", e.message));
  await page.goto(`${origin}/__rec/harness.html`);

  // Wait until every embedded app has rendered what its shot needs, and fonts are in.
  const [splitL, splitR, app1, app2, app3] = await Promise.all(
    ["split-l", "split-r", "app1", "app2", "app3"].map((id) => frameOf(page, id)),
  );
  await Promise.all([
    splitL.waitForSelector(".direction-card"),
    splitR.waitForSelector(".direction-card"),
    app1.waitForSelector(".direction-card"),
    app2.waitForSelector("form.query"),
    app3.waitForSelector(".ab-table"),
  ]);
  for (const f of [page.mainFrame(), splitL, splitR, app1, app2, app3]) await f.evaluate(() => document.fonts.ready.then(() => 0));
  await page.evaluate(() => (window as any).rec.scrollFrame("app1", "p.banner[role=note]:not(.banner--static)", 24, 0));
  await page.evaluate(() => (window as any).rec.scrollFrame("app3", "#panel-ab p.banner", 24, 0));
  await sleep(1000); // white pre-roll: the sync marker ffmpeg trims on

  const log: ShotLog[] = [];
  const T0 = performance.now();
  const now = () => (performance.now() - T0) / 1000;
  const until = async (t: number) => {
    const ms = (t - now()) * 1000;
    if (ms > 0) await sleep(ms);
  };
  const rec = (fn: string, ...a: unknown[]) =>
    page.evaluate(([f, xs]) => (window as any).rec[f as string](...(xs as unknown[])), [fn, a] as const);
  await rec("start", cues, WITH_CAPTIONS);

  const run: Record<string, (at: (s: number) => Promise<void>) => Promise<void>> = {
    S01: async () => {
      await rec("show", "L-persona", "cut");
      await rec("persona");
    },
    S02: async () => {
      await rec("show", "L-title", "cut");
    },
    S03: async (at) => {
      await rec("show", "L-split", "cut"); // both windows show the app's own SYNTHETIC banner
      await at(2.0);
      await rec("focusWin", "l");
      await at(5.2);
      await rec("focusWin", "r");
      await at(10.5);
      await rec("focusWin", "");
    },
    S04: async (at) => {
      await rec("show", "L-app1", "cut");
      await rec("tag", true);
      await rec("zoom", "L-app1", 1.15, 18500, "50% 18%");
      await at(8.0);
      await app1.click(".direction-card .quote-pill summary");
      await at(9.0);
      await rec("scrollFrame", "app1", ".direction-card", 24, 1400);
    },
    S05: async (at) => {
      await rec("zoom", "L-app1", 1, 0);
      await app1.click(".direction-card .quote-pill summary"); // close the quote again
      await rec("scrollFrame", "app1", "p.banner[role=note]:not(.banner--static)", 24, 0);
      await rec("show", "L-app1", "cut");
      await at(1.4);
      await rec("scrollFrame", "app1", "#options-heading", 28, 1600);
    },
    S06: async (at) => {
      await rec("show", "L-app2", "dissolve");
      await at(1.0);
      const input = app2.locator("form.query input").first();
      await input.click({ clickCount: 3 });
      await input.press("Backspace");
      await input.pressSequentially("3011", { delay: 150 });
      await at(2.6);
      await app2.click("form.query button[type=submit]");
      await app2.waitForSelector(".no-position");
      await at(3.6);
      await rec("scrollFrame", "app2", "p.banner[role=note]:not(.banner--static)", 24, 1300);
      await at(12.5);
      await app2.locator(".no-position button", { hasText: "Copy Dutch script" }).click();
    },
    S07: async (at) => {
      await rec("tag", false);
      await rec("show", "L-arch", "cut");
      await rec("arch", 0);
      await at(0.5);
      await rec("arch", 1);
      await at(1.0);
      await rec("arch", 2);
      await at(3.9);
      await rec("arch", 3);
      await at(9.0);
      await rec("arch", 4);
      await at(15.2);
      await rec("arch", 5);
    },
    S08: async () => {
      await rec("honest");
    },
    S09: async () => {
      await rec("show", "L-term", "cut");
      await rec("terminal", S09_COMMAND);
    },
    S10: async (at) => {
      await rec("show", "L-app3", "cut");
      await rec("tag", true);
      await rec("zoom", "L-app3", 1.15, 13000, "50% 30%");
      await at(14.0);
      await rec("zoom", "L-app3", 1, 900);
      await rec("scrollFrame", "app3", "[aria-labelledby=limits-heading]", 220, 1600);
    },
    S11: async () => {
      await rec("tag", false);
      await rec("show", "L-limits", "dissolve");
      void rec("limits");
    },
    S12: async () => {
      await rec("show", "L-end", "cut");
    },
  };

  for (const shot of shots) {
    await until(shot.in);
    const started = now();
    log.push({ id: shot.id, planned: shot.in, started: Number(started.toFixed(3)), late: Number((started - shot.in).toFixed(3)) });
    await run[shot.id]((s) => until(shot.in + s));
  }
  await until(RUNTIME_S + 0.6);

  const video = page.video();
  await context.close();
  await browser.close();
  server.close();
  const raw = await video!.path();
  return { raw, log };
}

// ---------------------------------------------------------------------------------------------- post-production

function ff(argv: string[], label: string): string {
  const r = spawnSync(ffmpegPath(), ["-hide_banner", "-y", ...argv], { encoding: "utf8", maxBuffer: 64 * 1024 * 1024 });
  if (r.status !== 0) throw new Error(`ffmpeg (${label}) failed:\n${r.stderr.slice(-3000)}`);
  return r.stderr;
}

/**
 * Seconds of white pre-roll at the start of the raw recording (the sync marker). Playwright writes frames only
 * when the page changes, so the marker is one held white frame; t=0 is the timestamp of the first dark frame.
 */
function syncOffset(raw: string): number {
  const log = ff(["-t", "15", "-i", raw, "-vf", "signalstats,metadata=print:key=lavfi.signalstats.YAVG", "-an", "-f", "null", "-"], "sync");
  const frames = [...log.matchAll(/pts_time:([\d.]+)[\s\S]*?YAVG=([\d.]+)/g)].map((m) => ({ t: Number(m[1]), y: Number(m[2]) }));
  if (!frames.length || frames[0].y < 150) throw new Error("sync marker not found: the raw video does not start white");
  const first = frames.find((f) => f.y < 150);
  if (!first) throw new Error("sync marker not found: the raw video never leaves the white pre-roll");
  return first.t;
}

function buildVoiceTrack(voice: PlacedVoice[], wav: string): void {
  const files = [...new Set(voice.map((v) => v.file))];
  const inputs = files.flatMap((f) => ["-i", join(VOICE_DIR, f)]);
  const parts: string[] = [];
  const labels: string[] = [];
  let cursor = 0;
  voice.forEach((v, i) => {
    const gap = v.at - cursor;
    if (gap > 0.001) {
      parts.push(`aevalsrc=0:d=${gap.toFixed(3)}:s=48000[g${i}]`);
      labels.push(`[g${i}]`);
    }
    const k = files.indexOf(v.file);
    parts.push(
      `[${k}:a]atrim=start=${v.start.toFixed(3)}:end=${v.end.toFixed(3)},asetpts=PTS-STARTPTS,aresample=48000,aformat=channel_layouts=mono[v${i}]`,
    );
    labels.push(`[v${i}]`);
    cursor = v.at + v.length;
  });
  parts.push(
    `${labels.join("")}concat=n=${labels.length}:v=0:a=1,apad,atrim=0:${RUNTIME_S},loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000,` +
      `afade=t=out:st=${(RUNTIME_S - FADE_S).toFixed(2)}:d=${FADE_S.toFixed(2)}[out]`,
  );
  ff([...inputs, "-filter_complex", parts.join(";"), "-map", "[out]", "-ac", "2", "-t", String(RUNTIME_S), wav], "voice track");
}

function encode(raw: string, offset: number, wav: string | null): { mp4: string; webm: string } {
  // Playwright writes frames only on change (variable frame rate): make it constant-rate over the whole timeline
  // first, then trim at the sync point — an input seek would skip to the next *changed* frame.
  const vf =
    `fps=${FPS},trim=start=${offset.toFixed(3)}:duration=${RUNTIME_S},setpts=PTS-STARTPTS,` +
    `fade=t=in:st=0:d=${FADE_S},fade=t=out:st=${(RUNTIME_S - FADE_S).toFixed(2)}:d=${FADE_S},format=yuv420p`;
  const input = ["-i", raw, ...(wav ? ["-i", wav] : [])];
  const maps = wav ? ["-map", "0:v:0", "-map", "1:a:0"] : ["-map", "0:v:0"];
  const mp4 = join(OUT_DIR, `${OUT_NAME}.mp4`);
  const webm = join(OUT_DIR, `${OUT_NAME}.webm`);
  ff(
    [...input, ...maps, "-t", String(RUNTIME_S), "-vf", vf, "-c:v", "libx264", "-preset", "slow", "-crf", "24", "-tune", "stillimage",
      "-profile:v", "high", "-r", String(FPS), ...(wav ? ["-c:a", "aac", "-b:a", "128k"] : []), "-movflags", "+faststart", mp4],
    "mp4",
  );
  ff(
    [...input, ...maps, "-t", String(RUNTIME_S), "-vf", vf, "-c:v", "libvpx-vp9", "-crf", "36", "-b:v", "0", "-deadline", "good",
      "-cpu-used", "4", "-row-mt", "1", "-r", String(FPS), ...(wav ? ["-c:a", "libopus", "-b:a", "96k"] : []), webm],
    "webm",
  );
  return { mp4, webm };
}

function probe(file: string): { duration: number; width: number; height: number; audio: boolean } {
  const r = spawnSync(ffmpegPath(), ["-hide_banner", "-i", file], { encoding: "utf8" });
  const v = /Video: .*?, (\d{3,5})x(\d{3,5})/.exec(r.stderr);
  return { duration: mediaDuration(file), width: Number(v?.[1]), height: Number(v?.[2]), audio: /Audio: /.test(r.stderr) };
}

// ---------------------------------------------------------------------------------------------- main

async function main(): Promise<void> {
  const shots = parseShots(readFileSync(SCRIPT_MD, "utf8"));
  const voice = WITH_VOICE ? placeVoice(shots) : null;
  const cues = buildCues(shots, voice);
  if (PLAN_ONLY) {
    console.log(JSON.stringify({ shots: shots.map(({ id, in: i, out, transition }) => ({ id, in: i, out, transition })), voice, cues }, null, 1));
    return;
  }
  if (!existsSync(join(DIST, "index.html")) || !existsSync(join(DIST, "demo", "index.json"))) {
    throw new Error("frontend/dist is not a Pages build with the demo snapshot. Run `make build-pages` first.");
  }
  console.log("S09: running the withholding tests for real …");
  const pytest = capturePytest();
  console.log(`  ${pytest[pytest.length - 1].replace(/=/g, "").trim()}`);

  mkdirSync(OUT_DIR, { recursive: true });
  console.log(`recording ${shots.length} shots, ${RUNTIME_S} s, ${FRAME.width}×${FRAME.height} (${VIEW.width}×${VIEW.height} layout at ${SCALE * 100} %) …`);
  const reuse = process.argv.find((x) => x.startsWith("--reuse-raw="))?.slice("--reuse-raw=".length);
  const { raw, log } = reuse
    ? { raw: reuse, log: JSON.parse(readFileSync(join(OUT_DIR, ".raw", "shots.json"), "utf8")) as ShotLog[] }
    : await record(shots, cues, pytest);
  if (!reuse) writeFileSync(join(OUT_DIR, ".raw", "shots.json"), JSON.stringify(log));
  const late = Math.max(...log.map((l) => l.late));
  console.log(`  raw: ${raw}; latest shot start ${late.toFixed(3)} s after its timecode`);
  if (late > 0.25) throw new Error(`a shot started ${late.toFixed(2)} s late; timing is not trustworthy — re-run on an idle machine`);

  const offset = syncOffset(raw);
  console.log(`  sync marker ends at ${offset.toFixed(3)} s`);
  let wav: string | null = null;
  if (voice) {
    wav = join(OUT_DIR, ".raw", "voiceover.wav");
    buildVoiceTrack(voice, wav);
  }
  console.log("encoding mp4 + webm …");
  const { mp4, webm } = encode(raw, offset, wav);
  writeFileSync(join(OUT_DIR, `${OUT_NAME}.vtt`), toVtt(cues));

  const result = { mp4: probe(mp4), webm: probe(webm) };
  for (const [name, p] of Object.entries(result)) {
    if (Math.abs(p.duration - RUNTIME_S) > 0.1) throw new Error(`${name}: duration ${p.duration} s, expected ${RUNTIME_S}`);
    if (p.width !== FRAME.width || p.height !== FRAME.height) throw new Error(`${name}: ${p.width}×${p.height}, expected 1920×1080`);
    if (Boolean(voice) !== p.audio) throw new Error(`${name}: audio track ${p.audio ? "present" : "missing"}`);
  }
  const timeline = {
    generated_at: new Date().toISOString(),
    script: "video/script.md",
    runtime_s: RUNTIME_S,
    frame: FRAME,
    layout_css_px: VIEW,
    zoom: SCALE,
    fps: FPS,
    sync_offset_s: Number(offset.toFixed(3)),
    shots: log,
    voiceover: voice?.map(({ file, start, end, at, shots: s }) => ({ file, clip_from: start, clip_to: Number(end.toFixed(3)), at, shots: s })) ?? null,
    voice: voice ? "synthetic text-to-speech, disclosed on the end card" : null,
    captions: WITH_CAPTIONS ? "burned in + gridqueue-demo.vtt" : "gridqueue-demo.vtt only",
    s09_pytest_summary: pytest[pytest.length - 1].replace(/=/g, "").trim(),
    outputs: Object.fromEntries(Object.entries(result).map(([k, p]) => [k, { ...p, bytes: statSync(k === "mp4" ? mp4 : webm).size }])),
  };
  writeFileSync(join(OUT_DIR, `${OUT_NAME}.timeline.json`), JSON.stringify(timeline, null, 1) + "\n");
  if (!KEEP_RAW) rmSync(join(OUT_DIR, ".raw"), { recursive: true, force: true });
  console.log(JSON.stringify(timeline.outputs, null, 1));
}

main().catch((err) => {
  console.error(err instanceof Error ? err.message : err);
  process.exit(1);
});
