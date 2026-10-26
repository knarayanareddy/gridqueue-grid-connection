import { useRef, useState, type FormEvent } from "react";
import {
  AlertTriangle,
  Check,
  CircleDashed,
  Copy,
  FileText,
  HelpCircle,
  Loader2,
  Lock,
  PlugZap,
  Search,
  ShieldCheck,
  Sun,
  X,
} from "lucide-react";
import type {
  BindingChip as BindingChipValue,
  Citation,
  Direction,
  DirectionResult,
  FlexOption,
  QueryResponse,
  SourceDocument,
  Verdict,
} from "./types";

// ---------------------------------------------------------------------------------------------- formatting

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

/** "2028-Q3" → "Q3 2028". Display only — the value itself has already passed the gate on the server. */
export function formatPartialDate(value: string): string {
  if (value.includes("/")) return value.split("/").map(formatPartialDate).join(" – ");
  const q = /^(\d{4})-(Q[1-4]|H[12])$/.exec(value);
  if (q) return `${q[2]} ${q[1]}`;
  const m = /^(\d{4})-(\d{2})(?:-(\d{2}))?$/.exec(value);
  if (m) return `${m[3] ? `${Number(m[3])} ` : ""}${MONTHS[Number(m[2]) - 1]} ${m[1]}`;
  return value;
}

const VERDICT_LABEL: Record<Verdict, string> = {
  CAPACITY_AVAILABLE: "Capacity available",
  PARTIAL_CAPACITY: "Partial capacity",
  WAITLIST_ONLY: "Waiting list only",
  NON_FIRM_ONLY: "Non-firm only",
  NO_FIRM_CAPACITY: "No firm capacity",
  UNDETERMINED: "Undetermined",
  NO_OFFICIAL_POSITION_FOUND: "No official position found",
};

const VERDICT_TONE: Record<Verdict, "available" | "congested" | "critical" | "neutral"> = {
  CAPACITY_AVAILABLE: "available",
  PARTIAL_CAPACITY: "congested",
  WAITLIST_ONLY: "congested",
  NON_FIRM_ONLY: "congested",
  NO_FIRM_CAPACITY: "critical",
  UNDETERMINED: "neutral",
  NO_OFFICIAL_POSITION_FOUND: "neutral",
};

const CHIP: Record<BindingChipValue, { label: string; Icon: typeof Lock; style: string }> = {
  BINDING: { label: "Binding", Icon: Lock, style: "solid" },
  NON_BINDING: { label: "Non-binding forecast", Icon: CircleDashed, style: "dashed" },
  UNKNOWN: { label: "Binding status not stated", Icon: HelpCircle, style: "dotted" },
  NOT_APPLICABLE: { label: "No date published", Icon: HelpCircle, style: "dotted" },
};

const DIRECTION_LABEL: Record<Direction, string> = {
  feed_in: "Feed-in · teruglevering",
  consumption: "Consumption · afname",
};

function shortSha(sha: string | null | undefined): string {
  return sha ? `${sha.slice(0, 12)}…` : "—";
}

function formatTimestamp(iso: string): string {
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? iso : d.toISOString().replace("T", " ").replace(/:\d{2}\.\d{3}Z$|:\d{2}Z$/, " UTC");
}

// ---------------------------------------------------------------------------------------------- components

function BindingChip({ value }: { value: BindingChipValue }) {
  const { label, Icon, style } = CHIP[value];
  return (
    <span className={`chip chip--${style}`}>
      <Icon size={14} aria-hidden="true" />
      {label}
    </span>
  );
}

function CopyButton({ text, label }: { text: string; label: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <button
      type="button"
      className="btn btn--ghost"
      onClick={async () => {
        try {
          await navigator.clipboard.writeText(text);
          setCopied(true);
          window.setTimeout(() => setCopied(false), 1800);
        } catch {
          setCopied(false);
        }
      }}
    >
      {copied ? <Check size={14} aria-hidden="true" /> : <Copy size={14} aria-hidden="true" />}
      {copied ? "Copied" : label}
    </button>
  );
}

function QuotePill({ citation, document, dso }: { citation?: Citation; document?: SourceDocument; dso: string }) {
  if (!citation?.quote) return null;
  const published = document?.publication_date ? ` · published ${formatPartialDate(document.publication_date)}` : "";
  return (
    <details className="quote-pill">
      <summary>
        <FileText size={14} aria-hidden="true" />
        <span>
          Official quote · {dso}
          {published}
        </span>
      </summary>
      <blockquote lang="nl">{citation.quote}</blockquote>
      {document && (
        <dl className="cite-meta">
          <dt>Document</dt>
          <dd>{document.title}</dd>
          <dt>Publisher</dt>
          <dd>{document.publisher}</dd>
          <dt>Source</dt>
          <dd>
            <a href={document.url} target="_blank" rel="noreferrer noopener">
              {document.url}
            </a>
          </dd>
          <dt>Retrieved</dt>
          <dd>{formatTimestamp(citation.retrieved_at)}</dd>
          <dt>SHA-256</dt>
          <dd className="mono" title={citation.sha256 ?? undefined}>
            {shortSha(citation.sha256)}
          </dd>
        </dl>
      )}
    </details>
  );
}

function DirectionCard({ result, data }: { result: DirectionResult; data: QueryResponse }) {
  const claim = result.position_claim;
  const dso = data.answer.location.dso ?? "grid operator";
  const citation = data.citations.find((c) => c.id === claim?.citation_id);
  const document = data.documents.find((d) => d.document_id === claim?.document_id);
  const tone = VERDICT_TONE[result.verdict];
  const date = result.indicative_earliest_date;

  return (
    <section className={`card direction-card tone--${tone}`} aria-labelledby="verdict-heading">
      <div className="direction-card__eyebrow">
        {result.direction === "feed_in" ? <Sun size={14} aria-hidden="true" /> : <PlugZap size={14} aria-hidden="true" />}
        {DIRECTION_LABEL[result.direction]} · {data.answer.location.postcode ?? "—"}
        {data.answer.location.gemeente ? ` ${data.answer.location.gemeente}` : ""} · {dso}
      </div>

      <div className="verdict-badge" id="verdict-heading">
        {date ? (
          <>
            <span className="verdict-badge__date">{formatPartialDate(date)}</span>
            <span className="verdict-badge__sep" aria-hidden="true">
              —
            </span>
            <BindingChip value={result.binding_chip} />
          </>
        ) : (
          <span className="verdict-badge__date">{VERDICT_LABEL[result.verdict]}</span>
        )}
      </div>

      <div className="verdict-row">
        <span className={`status status--${tone}`}>{VERDICT_LABEL[result.verdict]}</span>
        {!date && <BindingChip value={result.binding_chip} />}
        {result.available_capacity_kw !== null && (
          <span className="status status--neutral">{result.available_capacity_kw} kW stated available</span>
        )}
      </div>

      <p className="headline">{result.headline}</p>

      {claim && claim.non_binding_markers_found.length > 0 && (
        <p className="muted small">
          Non-binding wording found in the source:{" "}
          {claim.non_binding_markers_found.map((m) => (
            <span key={m} className="marker" lang="nl">
              {m}
            </span>
          ))}
        </p>
      )}

      <QuotePill citation={citation} document={document} dso={dso} />
    </section>
  );
}

function NoPositionCard({ result }: { result: DirectionResult }) {
  const script = result.phone_script;
  return (
    <section className="card no-position" aria-label="What to do next">
      <h3>
        <AlertTriangle size={16} aria-hidden="true" /> We will not guess
      </h3>
      {result.abstentions.map((a) => (
        <p key={a.reason}>{a.message}</p>
      ))}
      {script && (
        <>
          <p className="muted small">Ask {script.dso} directly — this question uses their own vocabulary:</p>
          <blockquote lang="nl" className="script">
            {script.text_nl}
          </blockquote>
          <div className="row">
            <CopyButton text={script.text_nl} label="Copy Dutch script" />
            {!script.native_speaker_verified_by && <span className="muted small">Not yet checked by a native speaker.</span>}
          </div>
          {script.text_en && (
            <details className="plain-details">
              <summary>English translation</summary>
              <p>{script.text_en}</p>
            </details>
          )}
        </>
      )}
    </section>
  );
}

function OptionCard({ option, requestedKw }: { option: FlexOption; requestedKw: number }) {
  const kw = option.estimated_kw_enabled;
  const covers = kw !== null && kw >= requestedKw;
  return (
    <li className="card option-card">
      <div className="option-card__rank" aria-label={`Rank ${option.rank}`}>
        {option.rank}
      </div>
      <div className="option-card__body">
        <h4>{option.title}</h4>
        <div className="row">
          {kw !== null ? (
            <span className={`status ${covers ? "status--available" : "status--congested"}`}>
              Up to {kw} kW (stated){covers ? " · covers your request" : ""}
            </span>
          ) : (
            <span className="status status--neutral">Capacity not stated</span>
          )}
          <span className="muted small">Contact: {option.who_to_contact}</span>
        </div>
        <blockquote lang="nl" className="route">
          {option.application_route}
        </blockquote>
        <p className="muted small">{option.rank_rationale}</p>
      </div>
    </li>
  );
}

function GateReport({ data }: { data: QueryResponse }) {
  const g = data.answer.gate;
  return (
    <details className="card gate">
      <summary>
        <ShieldCheck size={16} aria-hidden="true" />
        Citation gate: {g.checks_passed}/{g.checks_run} checks passed · {g.rejected_claims.length} rejected ·{" "}
        {g.dates_dropped} date{g.dates_dropped === 1 ? "" : "s"} dropped · {g.llm_calls_in_gate} LLM calls in gate
      </summary>
      {g.rejected_claims.length > 0 ? (
        <ul className="rejections">
          {g.rejected_claims.map((r, i) => (
            <li key={`${r.reason}-${i}`}>
              <span className="mono reason">{r.reason}</span>
              <span>{r.claim}</span>
            </li>
          ))}
        </ul>
      ) : (
        <p className="muted small">Every model-proposed quote, date and figure was found verbatim in the source.</p>
      )}
      <p className="muted small mono">determinism {shortSha(g.determinism_hash)}</p>
    </details>
  );
}

// ---------------------------------------------------------------------------------------------- app

export default function App() {
  const [postcode, setPostcode] = useState("5612 AB");
  const [kw, setKw] = useState("60");
  const [direction, setDirection] = useState<Direction>("feed_in");
  const [data, setData] = useState<QueryResponse | null>(null);
  const [requestedKw, setRequestedKw] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const controller = useRef<AbortController | null>(null);

  async function submit(e: FormEvent) {
    e.preventDefault();
    controller.current?.abort();
    const ac = new AbortController();
    controller.current = ac;
    setLoading(true);
    setError(null);
    const power = Number(kw);
    try {
      const res = await fetch("/v1/answer", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ postcode, power_kw: power, direction }),
        signal: ac.signal,
      });
      if (!res.ok) {
        const body = await res.json().catch(() => null);
        const detail = Array.isArray(body?.detail) ? body.detail.map((d: { msg: string }) => d.msg).join("; ") : null;
        throw new Error(detail ? `Check your input: ${detail}` : `The server returned ${res.status}.`);
      }
      setData((await res.json()) as QueryResponse);
      setRequestedKw(power);
    } catch (err) {
      if ((err as Error).name !== "AbortError") {
        setError((err as Error).message || "Request failed.");
      }
    } finally {
      if (controller.current === ac) {
        setLoading(false);
        controller.current = null;
      }
    }
  }

  function cancel() {
    controller.current?.abort();
    controller.current = null;
    setLoading(false);
  }

  const result = data?.answer.per_direction[0];

  return (
    <div className="shell">
      <header className="masthead">
        <div className="brand">
          <span className="brand__mark" aria-hidden="true" />
          GridQueue
        </div>
        <p className="muted">Grid-connection answers in the operator's own words — or an honest “we don't know”.</p>
      </header>

      <form className="card query" onSubmit={submit} aria-label="Grid position query">
        <label className="field">
          <span>Postcode</span>
          <input
            value={postcode}
            onChange={(e) => setPostcode(e.target.value)}
            placeholder="5612 AB"
            autoComplete="postal-code"
            required
            minLength={4}
            maxLength={8}
          />
        </label>
        <label className="field field--kw">
          <span>Power (kW)</span>
          <input
            type="number"
            inputMode="decimal"
            min={0.1}
            step="any"
            value={kw}
            onChange={(e) => setKw(e.target.value)}
            required
          />
        </label>
        <fieldset className="field segmented">
          <legend>Direction</legend>
          {(["feed_in", "consumption"] as const).map((d) => (
            <label key={d} className={direction === d ? "is-active" : ""}>
              <input type="radio" name="direction" value={d} checked={direction === d} onChange={() => setDirection(d)} />
              {d === "feed_in" ? <Sun size={14} aria-hidden="true" /> : <PlugZap size={14} aria-hidden="true" />}
              {d === "feed_in" ? "Feed-in" : "Consumption"}
            </label>
          ))}
        </fieldset>
        <div className="query__actions">
          <button type="submit" className="btn btn--primary" disabled={loading}>
            {loading ? <Loader2 size={16} className="spin" aria-hidden="true" /> : <Search size={16} aria-hidden="true" />}
            {loading ? "Checking…" : "Check grid position"}
          </button>
          {loading && (
            <button type="button" className="btn btn--ghost" onClick={cancel}>
              <X size={14} aria-hidden="true" /> Cancel
            </button>
          )}
        </div>
      </form>

      <div aria-live="polite" className="results">
        {error && (
          <p className="card error" role="alert">
            <AlertTriangle size={16} aria-hidden="true" /> {error}
          </p>
        )}

        {data && result && (
          <>
            {data.retrieval.synthetic && (
              <p className="banner" role="note">
                <AlertTriangle size={16} aria-hidden="true" />
                Demo mode — answers below come from SYNTHETIC fixture documents, not official publications.
              </p>
            )}

            <DirectionCard result={result} data={data} />

            {result.verdict === "NO_OFFICIAL_POSITION_FOUND" && <NoPositionCard result={result} />}

            {data.answer.options_ranked.length > 0 && (
              <section aria-labelledby="options-heading">
                <h2 id="options-heading" className="section-title">
                  Flexibility options <span className="muted">· ranked, each route quoted from the source</span>
                </h2>
                <ol className="options">
                  {data.answer.options_ranked.map((o) => (
                    <OptionCard key={o.id} option={o} requestedKw={requestedKw} />
                  ))}
                </ol>
              </section>
            )}

            <GateReport data={data} />

            <footer className="foot muted small">
              <p>
                Retrieval: {data.retrieval.mode}
                {data.retrieval.synthetic ? " (synthetic)" : ""} · {data.retrieval.results_used} document
                {data.retrieval.results_used === 1 ? "" : "s"} · {data.retrieval.tavily_calls} Tavily calls · extraction{" "}
                {data.retrieval.extraction}
                {data.retrieval.model ? ` (${data.retrieval.model})` : ""} · {data.answer.timings_ms.total ?? "—"} ms
              </p>
              <p>{data.answer.disclaimer}</p>
            </footer>
          </>
        )}
      </div>
    </div>
  );
}
