import { useEffect, useRef, useState, type FormEvent, type KeyboardEvent } from "react";
import {
  AlertTriangle,
  Check,
  CircleDashed,
  FlaskConical,
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
  AbCounterName,
  AbExperimentResult,
  AbLabel,
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

function QueryView() {
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
    <>
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
    </>
  );
}

// ---------------------------------------------------------------------------------------------- A/B gate evidence

const AB_ROWS: { key: AbCounterName; label: string; good: "zero" | "all" | "context" }[] = [
  { key: "fabricated_dates", label: "Fabricated dates", good: "zero" },
  { key: "fabricated_kw", label: "Fabricated kW figures", good: "zero" },
  { key: "fabricated_binding", label: "Fabricated binding claims", good: "zero" },
  { key: "fabricated_routes", label: "Fabricated application routes", good: "zero" },
  { key: "misattributed", label: "Misattributed (real quote, wrong meaning)", good: "context" },
  { key: "genuine", label: "Genuine values kept", good: "all" },
];

function formatLabelValue(lab: AbLabel): string {
  if (lab.value === null) return lab.kind ?? "—";
  if (lab.field === "date") return formatPartialDate(String(lab.value));
  if (lab.field === "kw" || lab.field === "option_kw") return `${lab.value} kW`;
  return String(lab.value);
}

function Reached({ reached }: { reached: boolean }) {
  return reached ? (
    <span className="reach reach--yes">
      <Check size={13} aria-hidden="true" /> in answer
    </span>
  ) : (
    <span className="reach reach--no">
      <X size={13} aria-hidden="true" /> blocked
    </span>
  );
}

/** One counter, both arms, as two bars. Width is the share of labelled values that reached the answer. */
function CounterBars({ total, on, off }: { total: number; on: number; off: number }) {
  const pct = (n: number) => (total ? `${(100 * n) / total}%` : "0%");
  return (
    <div className="ab-bars" aria-hidden="true">
      <span className="ab-bar ab-bar--off" style={{ width: pct(off) }} />
      <span className="ab-bar ab-bar--on" style={{ width: pct(on) }} />
    </div>
  );
}

function AbEvidence() {
  const [result, setResult] = useState<AbExperimentResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const ac = new AbortController();
    fetch("/v1/ab-results", { signal: ac.signal })
      .then(async (res) => {
        if (!res.ok) {
          const body = await res.json().catch(() => null);
          throw new Error(typeof body?.detail === "string" ? body.detail : `The server returned ${res.status}.`);
        }
        setResult((await res.json()) as AbExperimentResult);
      })
      .catch((err: Error) => {
        if (err.name !== "AbortError") setError(err.message || "Could not load the A/B results.");
      });
    return () => ac.abort();
  }, []);

  if (error) {
    return (
      <p className="card error" role="alert">
        <AlertTriangle size={16} aria-hidden="true" /> {error}
      </p>
    );
  }
  if (!result) {
    return (
      <p className="muted row">
        <Loader2 size={16} className="spin" aria-hidden="true" /> Loading measured results…
      </p>
    );
  }

  const ex = result.execution;
  const ts = result.test_set;
  return (
    <div className="results">
      {ts.synthetic && (
        <p className="banner" role="note">
          <AlertTriangle size={16} aria-hidden="true" />
          SYNTHETIC test set — {ts.n_cases} hand-written adversarial cases over synthetic operator documents, not real
          model output.
        </p>
      )}
      {!ex.token_factory_sandbox && (
        <p className="banner" role="note">
          <AlertTriangle size={16} aria-hidden="true" />
          Ran as a local process, not in a Token Factory Sandbox. Both arms started from the same snapshot.
        </p>
      )}

      <section className="card" aria-labelledby="ab-heading">
        <h2 id="ab-heading" className="section-title">
          <FlaskConical size={18} aria-hidden="true" /> Same inputs, gate on vs gate off
        </h2>
        <p className="headline">{result.headline}</p>
        <div className="ab-legend small muted">
          <span>
            <span className="ab-swatch ab-bar--off" /> Gate OFF (model proposals accepted as-is)
          </span>
          <span>
            <span className="ab-swatch ab-bar--on" /> Gate ON (deterministic citation gate)
          </span>
        </div>
        <table className="ab-table">
          <caption className="sr-only">Labelled values that reached the final answer, per arm</caption>
          <thead>
            <tr>
              <th scope="col">Labelled values</th>
              <th scope="col" className="num">
                Gate OFF
              </th>
              <th scope="col" className="num">
                Gate ON
              </th>
              <th scope="col">
                <span className="sr-only">Chart</span>
              </th>
            </tr>
          </thead>
          <tbody>
            {AB_ROWS.map(({ key, label, good }) => {
              const d = result.delta[key];
              return (
                <tr key={key} className={good === "context" ? "is-limit" : undefined}>
                  <th scope="row">{label}</th>
                  <td className="num mono">
                    {d.gate_off}/{d.total}
                  </td>
                  <td className="num mono">
                    <strong>
                      {d.gate_on}/{d.total}
                    </strong>
                  </td>
                  <td>
                    <CounterBars total={d.total} on={d.gate_on} off={d.gate_off} />
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
        <p className="muted small">
          Each number counts labelled values that reached the final answer. For fabricated values, lower is better; for
          genuine values, all should be kept. Gate ON ran {result.arms.find((a) => a.arm === "gate_on")?.gate_checks_run}{" "}
          checks with {result.arms.find((a) => a.arm === "gate_on")?.llm_calls_in_gate} LLM calls.
        </p>
      </section>

      <section className="card" aria-labelledby="limits-heading">
        <h2 id="limits-heading" className="section-title">
          What this does not show
        </h2>
        <ul className="limits">
          {result.limitations.map((l) => (
            <li key={l}>{l}</li>
          ))}
        </ul>
      </section>

      <details className="card gate">
        <summary>
          <FileText size={16} aria-hidden="true" /> Per-case results · {result.per_case.length} cases
        </summary>
        <ol className="ab-cases">
          {result.per_case.map((c) => (
            <li key={c.case_id}>
              <div className="row">
                <span className="mono">{c.case_id}</span>
                <strong>{c.title}</strong>
                <span className="muted small">
                  {c.dso} · {DIRECTION_LABEL[c.direction]}
                </span>
              </div>
              <ul className="ab-labels">
                {c.labels.map((lab, i) => (
                  <li key={`${c.case_id}-${i}`}>
                    <span className={`chip chip--${lab.label === "genuine" ? "solid" : "dashed"}`}>{lab.label}</span>
                    <span className="mono">
                      {lab.field}: {formatLabelValue(lab)}
                    </span>
                    <span className="small">
                      OFF <Reached reached={lab.reached_gate_off} /> · ON <Reached reached={lab.reached_gate_on} />
                    </span>
                    <span className="muted small ab-why">{lab.why}</span>
                  </li>
                ))}
              </ul>
              <p className="muted small">
                Verdict: OFF {VERDICT_LABEL[c.verdict.gate_off]} · ON {VERDICT_LABEL[c.verdict.gate_on]}
                {c.rejected_reasons_gate_on.length > 0 && (
                  <>
                    {" "}
                    · gate reasons <span className="mono">{c.rejected_reasons_gate_on.join(", ")}</span>
                  </>
                )}
              </p>
            </li>
          ))}
        </ol>
      </details>

      <footer className="foot muted small">
        <p>
          {result.experiment_id} · test set {ts.version} <span className="mono">sha256 {shortSha(ts.sha256)}</span> ·
          snapshot <span className="mono">{shortSha(result.snapshot_id)}</span> · generated{" "}
          {formatTimestamp(result.generated_at)}
        </p>
        <p>{ex.note}</p>
      </footer>
    </div>
  );
}

// ---------------------------------------------------------------------------------------------- shell

const TABS = [
  { id: "direction", label: "Direction Card" },
  { id: "ab", label: "A/B Gate Evidence" },
] as const;
type TabId = (typeof TABS)[number]["id"];

export default function App() {
  const [tab, setTab] = useState<TabId>("direction");
  const [abOpened, setAbOpened] = useState(false);
  const tabRefs = useRef<Record<string, HTMLButtonElement | null>>({});

  function select(id: TabId) {
    setTab(id);
    if (id === "ab") setAbOpened(true);
  }

  function onKey(e: KeyboardEvent<HTMLDivElement>) {
    if (e.key !== "ArrowRight" && e.key !== "ArrowLeft") return;
    const i = TABS.findIndex((t) => t.id === tab);
    const next = TABS[(i + (e.key === "ArrowRight" ? 1 : TABS.length - 1)) % TABS.length].id;
    select(next);
    tabRefs.current[next]?.focus();
  }

  return (
    <div className="shell">
      <header className="masthead">
        <div className="brand">
          <span className="brand__mark" aria-hidden="true" />
          GridQueue
        </div>
        <p className="muted">Grid-connection answers in the operator's own words — or an honest “we don't know”.</p>
      </header>

      <div className="tabs" role="tablist" aria-label="Views" onKeyDown={onKey}>
        {TABS.map((t) => (
          <button
            key={t.id}
            ref={(el) => (tabRefs.current[t.id] = el)}
            type="button"
            role="tab"
            id={`tab-${t.id}`}
            aria-selected={tab === t.id}
            aria-controls={`panel-${t.id}`}
            tabIndex={tab === t.id ? 0 : -1}
            className={tab === t.id ? "tab is-active" : "tab"}
            onClick={() => select(t.id)}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Both panels stay mounted so a query survives switching tabs. */}
      <div role="tabpanel" id="panel-direction" aria-labelledby="tab-direction" hidden={tab !== "direction"}>
        <div className="results">
          <QueryView />
        </div>
      </div>
      <div role="tabpanel" id="panel-ab" aria-labelledby="tab-ab" hidden={tab !== "ab"}>
        {abOpened && <AbEvidence />}
      </div>
    </div>
  );
}
