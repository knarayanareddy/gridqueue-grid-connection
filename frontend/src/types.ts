// Subset of schemas/core-schemas.json (v1.2.0) used by the UI. QueryResponse is the /v1/answer envelope.

export type Direction = "feed_in" | "consumption";

export type Verdict =
  | "CAPACITY_AVAILABLE"
  | "PARTIAL_CAPACITY"
  | "WAITLIST_ONLY"
  | "NON_FIRM_ONLY"
  | "NO_FIRM_CAPACITY"
  | "UNDETERMINED"
  | "NO_OFFICIAL_POSITION_FOUND";

export type BindingChip = "BINDING" | "NON_BINDING" | "UNKNOWN" | "NOT_APPLICABLE";

export interface PositionClaim {
  id: string;
  dso: string;
  direction: Direction;
  congestion_registered: boolean | "unknown";
  queue_status: string;
  indicative_earliest_date: string | null;
  binding: "binding" | "non_binding" | "unknown";
  binding_evidence_quote: string | null;
  non_binding_markers_found: string[];
  available_capacity_kw: number | null;
  capacity_basis_quote: string | null;
  document_id: string;
  citation_id: string;
  verbatim_quote: string;
  publication_date: string | null;
}

export interface Abstention {
  reason: string;
  scope: string;
  message: string;
  fix_instruction: string;
}

export interface PhoneScript {
  dso: string;
  text_nl: string;
  text_en: string | null;
  native_speaker_verified_by: string | null;
}

export interface DirectionResult {
  direction: Direction;
  verdict: Verdict;
  headline: string;
  position_claim: PositionClaim | null;
  binding_chip: BindingChip;
  available_capacity_kw: number | null;
  indicative_earliest_date: string | null;
  abstentions: Abstention[];
  phone_script: PhoneScript | null;
}

export interface FlexOption {
  id: string;
  kind: string;
  title: string;
  rank: number;
  rank_rationale: string;
  estimated_kw_enabled: number | null;
  application_route: string;
  who_to_contact: string;
  evidence_document_ids: string[];
  citation_ids: string[];
}

export interface RejectedClaim {
  claim: string;
  reason: string;
  document_id: string | null;
}

export interface Answer {
  answer_id: string;
  location: {
    postcode: string | null;
    gemeente: string | null;
    dso: string | null;
    resolved: boolean;
  };
  per_direction: DirectionResult[];
  options_ranked: FlexOption[];
  gate: {
    checks_run: number;
    checks_passed: number;
    rejected_claims: RejectedClaim[];
    dates_surviving: number;
    dates_dropped: number;
    determinism_hash: string;
    llm_calls_in_gate: number;
  };
  corpus_snapshot_id: string;
  timings_ms: Record<string, number>;
  generated_at: string;
  disclaimer: string;
}

export interface SourceDocument {
  document_id: string;
  publisher: string;
  title: string;
  url: string;
  publication_date: string | null;
  retrieved_at: string;
  sha256: string;
}

export interface Citation {
  id: string;
  document_id: string | null;
  quote: string | null;
  retrieved_at: string;
  sha256: string | null;
}

export interface QueryResponse {
  answer: Answer;
  documents: SourceDocument[];
  citations: Citation[];
  retrieval: {
    mode: "live" | "fixture";
    synthetic: boolean;
    performed_at: string;
    queries?: string[];
    tavily_calls: number;
    results_seen: number;
    results_used: number;
    extraction: "live_model" | "replay" | "not_run";
    model?: string | null;
  };
}

// ------------------------------------------------------------------ A/B gate evidence (schemas/core-schemas.json#/$defs/AbExperimentResult)

export type AbCounterName =
  | "fabricated_dates"
  | "fabricated_kw"
  | "fabricated_binding"
  | "fabricated_routes"
  | "misattributed"
  | "genuine";

export interface AbCount {
  total: number;
  passed: number;
}

export interface AbArm {
  arm: "gate_on" | "gate_off";
  gate_enabled: boolean;
  n_cases: number;
  counters: Record<AbCounterName, AbCount>;
  fabricated_values: AbCount;
  false_rejects: number;
  verdicts: Partial<Record<Verdict, number>>;
  gate_checks_run: number;
  llm_calls_in_gate: number;
}

export interface AbLabel {
  field: "date" | "kw" | "option_kw" | "binding" | "route";
  value: string | number | null;
  label: "fabricated" | "misattributed" | "genuine";
  why: string;
  kind?: string;
  counter: AbCounterName;
  reached_gate_on: boolean;
  reached_gate_off: boolean;
}

export interface AbCase {
  case_id: string;
  title: string;
  dso: string;
  direction: Direction;
  snapshot_sha256: string;
  verdict: { gate_on: Verdict; gate_off: Verdict };
  gate_checks_run: { gate_on: number; gate_off: number };
  rejected_reasons_gate_on: string[];
  labels: AbLabel[];
}

export interface AbExperimentResult {
  experiment_id: string;
  generated_at: string;
  headline: string;
  execution: {
    environment: "local_process" | "token_factory_sandbox";
    token_factory_sandbox: boolean;
    network_disabled: boolean | null;
    sandbox_image_uuid: string | null;
    branch_operation_ids: string[] | null;
    note: string;
  };
  test_set: {
    path: string;
    version: string;
    sha256: string;
    synthetic: boolean;
    proposal_source: string;
    n_cases: number;
    n_labelled_values: number;
  };
  snapshot_id: string;
  arms: AbArm[];
  delta: Record<AbCounterName, { gate_on: number; gate_off: number; total: number }>;
  limitations: string[];
  per_case: AbCase[];
}
