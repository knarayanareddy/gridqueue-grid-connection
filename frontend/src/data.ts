/**
 * Data access for the two ways this UI runs:
 *
 *  - API mode (default, `npm run dev` / `make ui`): POST /v1/answer and GET /v1/ab-results on the FastAPI backend,
 *    proxied by Vite. Any postcode, any power, live or fixture retrieval.
 *  - Static demo mode (`vite build --mode pages`, VITE_STATIC_DEMO=true): the GitHub Pages build has no backend.
 *    Answers were precomputed by scripts/build_static_demo.py — the same pipeline, fixture mode, SYNTHETIC
 *    documents — and are read from `<base>/demo/`. Only the snapshot's postcode areas exist, at one fixed power.
 */
import type { AbExperimentResult, Direction, QueryResponse, Verdict } from "./types";

export const STATIC_DEMO = import.meta.env.VITE_STATIC_DEMO === "true";
const BASE = import.meta.env.BASE_URL; // "/" in dev, "/gridqueue-grid-connection/" on Pages; always ends in "/"

export interface SnapshotArea {
  postcode4: string;
  dso: string;
  gemeente: string | null;
  source: "sweep_sample" | "video_demo";
  note: string | null;
  verdicts: Record<Direction, Verdict>;
}

export interface SnapshotIndex {
  snapshot_id: string;
  generated_at: string;
  git_sha: string | null;
  mode: "fixture";
  synthetic: true;
  power_kw: number;
  directions: Direction[];
  note: string;
  areas: SnapshotArea[];
}

/** A postcode the static snapshot cannot answer. Carries the input so the UI can explain, not guess. */
export class NotInSnapshotError extends Error {
  constructor(public readonly postcode4: string) {
    super(
      `Postcode area ${postcode4} is not in this static snapshot. The Pages demo only has precomputed areas — ` +
        "pick one below, or run GridQueue locally (README, “Try it”: make api + npm run dev) to query any postcode.",
    );
    this.name = "NotInSnapshotError";
  }
}

const POSTCODE = /^\s*(\d{4})\s*([A-Za-z]{2})?\s*$/;

/** "5612 ab" → "5612"; null for anything that is not a Dutch postcode (4 digits, optional 2 letters). */
export function postcode4Of(input: string): string | null {
  const m = POSTCODE.exec(input);
  return m ? m[1] : null;
}

async function getJson<T>(url: string, signal?: AbortSignal): Promise<T> {
  const res = await fetch(url, { signal });
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new Error(typeof body?.detail === "string" ? body.detail : `The server returned ${res.status}.`);
  }
  return (await res.json()) as T;
}

let indexPromise: Promise<SnapshotIndex> | null = null;

/** The static snapshot's table of contents (static mode only). Cached; a failed load is retried next call. */
export function fetchSnapshotIndex(): Promise<SnapshotIndex> {
  if (!indexPromise) {
    indexPromise = getJson<SnapshotIndex>(`${BASE}demo/index.json`).catch((err) => {
      indexPromise = null;
      throw err;
    });
  }
  return indexPromise;
}

export async function fetchAnswer(
  req: { postcode: string; power_kw: number; direction: Direction },
  signal?: AbortSignal,
): Promise<QueryResponse> {
  if (!STATIC_DEMO) {
    const res = await fetch(`${BASE}v1/answer`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(req),
      signal,
    });
    if (!res.ok) {
      const body = await res.json().catch(() => null);
      const detail = Array.isArray(body?.detail) ? body.detail.map((d: { msg: string }) => d.msg).join("; ") : null;
      throw new Error(detail ? `Check your input: ${detail}` : `The server returned ${res.status}.`);
    }
    return (await res.json()) as QueryResponse;
  }

  const pc4 = postcode4Of(req.postcode);
  if (!pc4) throw new Error("Enter a Dutch postcode: four digits, optionally two letters (for example 5612 AB).");
  const index = await fetchSnapshotIndex();
  if (!index.areas.some((a) => a.postcode4 === pc4)) throw new NotInSnapshotError(pc4);
  return getJson<QueryResponse>(`${BASE}demo/answers/${pc4}.${req.direction}.json`, signal);
}

export function fetchAbResults(signal?: AbortSignal): Promise<AbExperimentResult> {
  return getJson<AbExperimentResult>(STATIC_DEMO ? `${BASE}demo/ab_experiment_results.json` : `${BASE}v1/ab-results`, signal);
}

/** Deep-link parameters: ?postcode=5612&direction=consumption&tab=ab&embed=1 */
export interface DeepLink {
  postcode: string | null;
  direction: Direction | null;
  tab: "direction" | "ab" | null;
  embed: boolean;
}

export function readDeepLink(search: string = window.location.search): DeepLink {
  const p = new URLSearchParams(search);
  const d = p.get("direction");
  const t = p.get("tab");
  return {
    postcode: p.get("postcode"),
    direction: d === "feed_in" || d === "consumption" ? d : null,
    tab: t === "ab" || t === "direction" ? t : null,
    embed: p.get("embed") === "1",
  };
}
