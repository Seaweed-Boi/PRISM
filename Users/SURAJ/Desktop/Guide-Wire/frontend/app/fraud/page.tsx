"use client";

import { useState } from "react";

// ── Types ─────────────────────────────────────────────────────
type FraudResult = {
  request_id: string;
  worker_id: number;
  policy_id: number;
  fraud_score: number;
  decision: string;
  decision_confidence: string;
  decision_message: string;
  anomaly_detection: {
    income_deviation_score: number;
    temporal_score: number;
    pattern_score: number;
    anomaly_score: number;
  };
  location_check: {
    sub_score: number;
    result: string;
    in_zone: boolean;
  };
  activity_validation: {
    sub_score: number;
    result: string;
    level?: string;
  };
  duplicate_check: {
    sub_score: number;
    result: string;
    is_duplicate: boolean;
  };
  weights: Record<string, number>;
  timestamp: string;
};

type PipelineStatus = {
  pipeline: Array<{
    layer: string;
    component: string;
    status: string;
    description: string;
  }>;
};

// ── Helpers ───────────────────────────────────────────────────
const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

function scoreColor(score: number) {
  if (score < 0.3)  return "#5cc8a1";
  if (score < 0.55) return "#ffbe55";
  if (score < 0.75) return "#ff9d4a";
  return "#ff6d5a";
}

function decisionColor(d: string) {
  if (d === "approve") return "#5cc8a1";
  if (d === "review")  return "#ffbe55";
  return "#ff6d5a";
}

// ── Sub-components ────────────────────────────────────────────

function ScoreBar({ score, label }: { score: number; label: string }) {
  const pct = Math.round(score * 100);
  const color = scoreColor(score);
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs">
        <span className="text-[rgba(232,240,254,0.6)]">{label}</span>
        <span className="mono font-semibold" style={{ color }}>{pct}%</span>
      </div>
      <div className="h-1.5 rounded-full w-full bg-white/5">
        <div
          className="h-full rounded-full score-bar-fill"
          style={{ width: `${pct}%`, background: `linear-gradient(90deg, ${color}99, ${color})` }}
        />
      </div>
    </div>
  );
}

function PipelineRow({
  icon, title, layer, status, description, subScore, details, index,
}: {
  icon: string; title: string; layer: string; status: string;
  description: string; subScore?: number; details?: Record<string, unknown>; index: number;
}) {
  const [expanded, setExpanded] = useState(false);
  const color = subScore !== undefined ? scoreColor(subScore) : "#5cc8a1";
  const isActive = status === "active";

  return (
    <div className="relative">
      {/* Vertical connector */}
      {index > 0 && (
        <div className="absolute -top-3 left-[18px] h-3 w-px bg-gradient-to-b from-[rgba(92,200,161,0.3)] to-transparent" />
      )}

      <div
        className="glass rounded-xl p-4 cursor-pointer hover:border-[rgba(92,200,161,0.35)] transition-all duration-200"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center gap-3">
          {/* Icon */}
          <div className="h-9 w-9 shrink-0 rounded-lg flex items-center justify-center text-base"
            style={{ background: `${color}15`, border: `1px solid ${color}25` }}>
            {icon}
          </div>

          {/* Title + layer */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <span className="font-semibold text-sm text-white">{title}</span>
              <span className="mono text-[9px] uppercase tracking-widest text-[rgba(232,240,254,0.35)] hidden sm:inline">
                {layer}
              </span>
            </div>
            <p className="text-xs text-[rgba(232,240,254,0.4)] mt-0.5 leading-snug line-clamp-1">{description}</p>
          </div>

          {/* Status + score */}
          <div className="flex items-center gap-3 shrink-0">
            {subScore !== undefined && (
              <div className="text-right">
                <div className="mono font-bold text-sm leading-none" style={{ color }}>
                  {Math.round(subScore * 100)}%
                </div>
                <div className="text-[9px] text-[rgba(232,240,254,0.3)] mt-0.5">risk score</div>
              </div>
            )}
            <span className={isActive ? "status-active" : "status-degraded"}>
              {isActive ? "active" : "degraded"}
            </span>
            <span className="text-[rgba(232,240,254,0.25)] text-xs select-none">
              {expanded ? "▲" : "▼"}
            </span>
          </div>
        </div>

        {/* Score bar */}
        {subScore !== undefined && (
          <div className="mt-3 h-1 rounded-full bg-white/5">
            <div
              className="h-full rounded-full score-bar-fill"
              style={{ width: `${Math.round(subScore * 100)}%`, background: color }}
            />
          </div>
        )}

        {/* Expanded detail rows */}
        {expanded && details && (
          <div className="mt-3 grid grid-cols-2 gap-x-6 gap-y-1 rounded-lg bg-black/25 p-3">
            {Object.entries(details).map(([k, v]) => (
              <div key={k} className="flex justify-between text-xs">
                <span className="mono text-[rgba(232,240,254,0.4)]">{k}</span>
                <span className="mono font-medium text-white">
                  {typeof v === "number" ? v.toFixed(3) : String(v)}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// ── Component status table (shown before any analysis is run) ─
const STATIC_COMPONENTS = [
  {
    layer: "Security",
    component: "Cloudflare Middleware",
    description: "Rate limiting · Bot scoring · CF-Ray · Country block",
    status: "active",
    weight: "—",
  },
  {
    layer: "Fraud Detection",
    component: "Anomaly Detection (ML)",
    description: "Income deviation · Temporal pattern · Repeat-value detection",
    status: "active",
    weight: "30%",
  },
  {
    layer: "Fraud Detection",
    component: "Location Check (GPS)",
    description: "Bounding-box validation against delivery zone polygon",
    status: "active",
    weight: "25%",
  },
  {
    layer: "Fraud Detection",
    component: "Activity Validation",
    description: "Worker activity score threshold during claim window",
    status: "active",
    weight: "25%",
  },
  {
    layer: "Fraud Detection",
    component: "Duplicate Check (Redis)",
    description: "SHA-1 claim fingerprint dedup with 1-hour Redis TTL",
    status: "active",
    weight: "20%",
  },
  {
    layer: "Scoring",
    component: "Fraud Score Aggregator",
    description: "Weighted composite of all sub-component scores",
    status: "active",
    weight: "—",
  },
  {
    layer: "Decision",
    component: "Decision Engine",
    description: "<0.30 approve · 0.30–0.55 approve+monitor · 0.55–0.75 review · ≥0.75 reject",
    status: "active",
    weight: "—",
  },
];

// ── Main page ─────────────────────────────────────────────────
export default function FraudEnginePage() {
  const [workerId,      setWorkerId]      = useState("1");
  const [policyId,      setPolicyId]      = useState("1");
  const [expectedIncome, setExpectedIncome] = useState("220");
  const [actualIncome,  setActualIncome]  = useState("80");
  const [lat,           setLat]           = useState("12.97");
  const [lon,           setLon]           = useState("77.59");
  const [zone,          setZone]          = useState("central");
  const [activityScore, setActivityScore] = useState("0.82");
  const [requestHour,   setRequestHour]   = useState("14");

  const [result,         setResult]         = useState<FraudResult | null>(null);
  const [pipelineStatus, setPipelineStatus] = useState<PipelineStatus | null>(null);
  const [loading,        setLoading]        = useState(false);
  const [error,          setError]          = useState("");

  async function loadPipelineStatus() {
    try {
      const r = await fetch(`${API}/fraud/pipeline-status`);
      const data = await r.json() as PipelineStatus;
      setPipelineStatus(data);
    } catch { /* noop */ }
  }

  async function runAnalysis() {
    setLoading(true);
    setError("");
    try {
      const body = {
        worker_id:      parseInt(workerId),
        policy_id:      parseInt(policyId),
        expected_income: parseFloat(expectedIncome),
        actual_income:  parseFloat(actualIncome),
        lat:            parseFloat(lat),
        lon:            parseFloat(lon),
        zone,
        activity_score: parseFloat(activityScore),
        request_hour:   parseInt(requestHour),
      };
      const r = await fetch(`${API}/fraud/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!r.ok) throw new Error(await r.text());
      const data = await r.json() as FraudResult;
      setResult(data);
      await loadPipelineStatus();
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }

  const redisStatus =
    pipelineStatus?.pipeline.find(c => c.component.includes("Redis"))?.status ?? "active";

  const pipelineNodes = result
    ? [
        {
          icon: "☁️",
          title: "Cloudflare Security",
          layer: "Security Layer",
          status: "active",
          description: "Rate limiting, bot score, CF-Ray validation, country blocking",
          subScore: undefined as number | undefined,
          details: { rate_limit: "120 req/min", bot_min_score: "20", local_dev: "allowed" },
        },
        {
          icon: "🧠",
          title: "Anomaly Detection (ML)",
          layer: "Fraud Detection",
          status: "active",
          description: "Income deviation, temporal pattern, repeat-value detection",
          subScore: result.anomaly_detection.anomaly_score,
          details: result.anomaly_detection as unknown as Record<string, unknown>,
        },
        {
          icon: "📍",
          title: "Location Check (GPS)",
          layer: "Fraud Detection",
          status: "active",
          description: "GPS bounding-box validation against delivery zone polygon",
          subScore: result.location_check.sub_score,
          details: result.location_check as unknown as Record<string, unknown>,
        },
        {
          icon: "✅",
          title: "Activity Validation",
          layer: "Fraud Detection",
          status: "active",
          description: "Worker activity level during the claim window",
          subScore: result.activity_validation.sub_score,
          details: result.activity_validation as unknown as Record<string, unknown>,
        },
        {
          icon: "🔁",
          title: "Duplicate Check (Redis)",
          layer: "Fraud Detection",
          status: redisStatus,
          description: "SHA-1 claim fingerprint dedup stored in Redis with 1-hour TTL",
          subScore: result.duplicate_check.sub_score,
          details: result.duplicate_check as unknown as Record<string, unknown>,
        },
        {
          icon: "📊",
          title: "Fraud Score",
          layer: "Scoring",
          status: "active",
          description: `Weighted composite — anomaly ×${result.weights.anomaly} · location ×${result.weights.location} · activity ×${result.weights.activity} · duplicate ×${result.weights.duplicate}`,
          subScore: result.fraud_score,
          details: { composite_fraud_score: result.fraud_score, ...result.weights } as Record<string, unknown>,
        },
        {
          icon: "⚖️",
          title: "Decision Engine",
          layer: "Decision",
          status: "active",
          description: result.decision_message,
          subScore: undefined as number | undefined,
          details: { verdict: result.decision, confidence: result.decision_confidence } as Record<string, unknown>,
        },
      ]
    : [];

  return (
    <div className="space-y-6">
      {/* ── Page header ── */}
      <div className="glass-bright rounded-2xl p-6">
        <p className="mono text-xs uppercase tracking-widest text-[#a78bfa]">
          ◆ Multi-Layer Fraud Detection
        </p>
        <h1 className="mt-1 text-3xl font-bold text-white">Fraud Detection Engine</h1>
        <p className="mt-2 text-sm text-[rgba(232,240,254,0.5)] max-w-2xl">
          Every claim traverses a 4-layer pipeline — ML anomaly detection, GPS validation,
          activity verification, and Redis dedup — before a weighted fraud score drives the decision engine.
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-[360px_1fr]">

        {/* ── Left: Input form ── */}
        <div className="space-y-5">
          <div className="glass rounded-2xl p-5">
            <h2 className="font-semibold text-white text-sm mb-4">Claim Parameters</h2>
            <div className="space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs text-[rgba(232,240,254,0.5)] mb-1">Worker ID</label>
                  <input id="fraud-worker-id" className="prism-input" type="number"
                    value={workerId} onChange={e => setWorkerId(e.target.value)} />
                </div>
                <div>
                  <label className="block text-xs text-[rgba(232,240,254,0.5)] mb-1">Policy ID</label>
                  <input id="fraud-policy-id" className="prism-input" type="number"
                    value={policyId} onChange={e => setPolicyId(e.target.value)} />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs text-[rgba(232,240,254,0.5)] mb-1">Expected ₹/hr</label>
                  <input id="fraud-expected" className="prism-input" type="number"
                    value={expectedIncome} onChange={e => setExpectedIncome(e.target.value)} />
                </div>
                <div>
                  <label className="block text-xs text-[rgba(232,240,254,0.5)] mb-1">Actual ₹/hr</label>
                  <input id="fraud-actual" className="prism-input" type="number"
                    value={actualIncome} onChange={e => setActualIncome(e.target.value)} />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs text-[rgba(232,240,254,0.5)] mb-1">Latitude</label>
                  <input id="fraud-lat" className="prism-input" type="number" step="0.001"
                    value={lat} onChange={e => setLat(e.target.value)} />
                </div>
                <div>
                  <label className="block text-xs text-[rgba(232,240,254,0.5)] mb-1">Longitude</label>
                  <input id="fraud-lon" className="prism-input" type="number" step="0.001"
                    value={lon} onChange={e => setLon(e.target.value)} />
                </div>
              </div>

              <div>
                <label className="block text-xs text-[rgba(232,240,254,0.5)] mb-1">Delivery Zone</label>
                <select id="fraud-zone" className="prism-select" value={zone}
                  onChange={e => setZone(e.target.value)}>
                  {["north", "south", "east", "west", "central", "unknown"].map(z => (
                    <option key={z} value={z}>{z}</option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs text-[rgba(232,240,254,0.5)] mb-1">
                    Activity Score <span className="opacity-40">(0–1)</span>
                  </label>
                  <input id="fraud-activity" className="prism-input" type="number"
                    step="0.01" min="0" max="1"
                    value={activityScore} onChange={e => setActivityScore(e.target.value)} />
                </div>
                <div>
                  <label className="block text-xs text-[rgba(232,240,254,0.5)] mb-1">Request Hour</label>
                  <input id="fraud-hour" className="prism-input" type="number" min="0" max="23"
                    value={requestHour} onChange={e => setRequestHour(e.target.value)} />
                </div>
              </div>
            </div>

            {/* Presets */}
            <div className="mt-4 grid grid-cols-2 gap-2">
              <button
                className="btn-ghost text-xs py-2"
                onClick={() => {
                  setLat("0"); setLon("0");
                  setActualIncome("10"); setActivityScore("0.05"); setRequestHour("3");
                }}
              >
                🚨 High-risk Preset
              </button>
              <button
                className="btn-ghost text-xs py-2"
                onClick={() => {
                  setLat("12.97"); setLon("77.59");
                  setActualIncome("80"); setActivityScore("0.82"); setRequestHour("14");
                }}
              >
                ✅ Clean Preset
              </button>
            </div>

            <button
              id="run-fraud-analysis"
              className="btn-primary w-full mt-3"
              onClick={runAnalysis}
              disabled={loading}
            >
              {loading ? "Analyzing…" : "▶  Run Fraud Pipeline"}
            </button>

            {error && (
              <p className="mt-3 text-xs text-[#ff6d5a] mono bg-[rgba(255,109,90,0.07)] rounded-lg p-2 border border-[rgba(255,109,90,0.2)]">
                {error}
              </p>
            )}
          </div>

          {/* Result summary — only shown after analysis */}
          {result && (
            <div
              className="glass rounded-2xl p-5 border"
              style={{ borderColor: `${decisionColor(result.decision)}35` }}
            >
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold text-white text-sm">Analysis Result</h3>
                <span
                  className="mono text-xs font-bold px-3 py-1 rounded-full border"
                  style={{
                    color: decisionColor(result.decision),
                    borderColor: `${decisionColor(result.decision)}35`,
                    background: `${decisionColor(result.decision)}10`,
                  }}
                >
                  {result.decision.toUpperCase()}
                </span>
              </div>

              {/* Score gauge */}
              <div className="flex items-center gap-4 mb-4">
                <div
                  className="flex h-16 w-16 shrink-0 items-center justify-center rounded-full border-[3px]"
                  style={{
                    borderColor: scoreColor(result.fraud_score),
                    background: `${scoreColor(result.fraud_score)}10`,
                    boxShadow: `0 0 20px ${scoreColor(result.fraud_score)}25`,
                  }}
                >
                  <div className="text-center">
                    <div className="mono font-bold text-lg leading-none" style={{ color: scoreColor(result.fraud_score) }}>
                      {Math.round(result.fraud_score * 100)}
                    </div>
                    <div className="text-[8px] text-[rgba(232,240,254,0.3)] uppercase tracking-widest mt-0.5">risk</div>
                  </div>
                </div>
                <p className="text-xs text-[rgba(232,240,254,0.5)] leading-relaxed">
                  {result.decision_message}
                </p>
              </div>

              <div className="space-y-2">
                <ScoreBar score={result.anomaly_detection.anomaly_score} label="Anomaly (ML)" />
                <ScoreBar score={result.location_check.sub_score}        label="Location (GPS)" />
                <ScoreBar score={result.activity_validation.sub_score}   label="Activity" />
                <ScoreBar score={result.duplicate_check.sub_score}       label="Duplicate (Redis)" />
              </div>

              <div className="mt-3 mono text-[9px] text-[rgba(232,240,254,0.25)] text-right">
                {result.request_id.slice(0, 16)}… · {new Date(result.timestamp).toLocaleTimeString()}
              </div>
            </div>
          )}
        </div>

        {/* ── Right: Pipeline components ── */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-semibold text-white text-sm">
              Pipeline Components
              {result && <span className="ml-2 status-active">Live</span>}
            </h2>
            {result && (
              <button className="btn-ghost text-xs py-1.5 px-3" onClick={() => setResult(null)}>
                Reset
              </button>
            )}
          </div>

          {!result ? (
            /* ── Component status table (idle state) ── */
            <div className="glass rounded-2xl overflow-hidden">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-white/5">
                    <th className="py-3 pl-4 pr-2 text-left mono text-[10px] uppercase tracking-widest text-[rgba(232,240,254,0.35)] font-normal">
                      Layer
                    </th>
                    <th className="py-3 px-2 text-left mono text-[10px] uppercase tracking-widest text-[rgba(232,240,254,0.35)] font-normal">
                      Component
                    </th>
                    <th className="py-3 px-2 text-left mono text-[10px] uppercase tracking-widest text-[rgba(232,240,254,0.35)] font-normal hidden md:table-cell">
                      Description
                    </th>
                    <th className="py-3 px-2 text-center mono text-[10px] uppercase tracking-widest text-[rgba(232,240,254,0.35)] font-normal">
                      Weight
                    </th>
                    <th className="py-3 pl-2 pr-4 text-center mono text-[10px] uppercase tracking-widest text-[rgba(232,240,254,0.35)] font-normal">
                      Status
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {STATIC_COMPONENTS.map((row, i) => (
                    <tr
                      key={row.component}
                      className="border-b border-white/[0.04] hover:bg-white/[0.02] transition-colors"
                    >
                      <td className="py-3.5 pl-4 pr-2">
                        <span className="mono text-[10px] uppercase tracking-widest text-[rgba(232,240,254,0.35)]">
                          {row.layer}
                        </span>
                      </td>
                      <td className="py-3.5 px-2">
                        <span className="font-medium text-white text-xs">{row.component}</span>
                      </td>
                      <td className="py-3.5 px-2 hidden md:table-cell">
                        <span className="text-xs text-[rgba(232,240,254,0.4)] leading-snug">{row.description}</span>
                      </td>
                      <td className="py-3.5 px-2 text-center">
                        <span className="mono text-xs font-semibold text-[#4891f7]">{row.weight}</span>
                      </td>
                      <td className="py-3.5 pl-2 pr-4 text-center">
                        <span className="status-active">active</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <div className="px-4 py-3 border-t border-white/5">
                <p className="text-xs text-[rgba(232,240,254,0.3)]">
                  Run the fraud pipeline analyzer on the left to see live per-component risk scores.
                </p>
              </div>
            </div>
          ) : (
            /* ── Live pipeline rows (post-analysis) ── */
            <div className="space-y-3">
              {pipelineNodes.map((node, i) => (
                <PipelineRow key={node.title} {...node} index={i} />
              ))}

              {/* Decision banner */}
              <div
                className="rounded-xl p-4 flex items-center gap-4 border"
                style={{
                  borderColor: `${decisionColor(result.decision)}35`,
                  background:  `${decisionColor(result.decision)}08`,
                }}
              >
                <div className="text-2xl">
                  {result.decision === "approve" ? "✅" : result.decision === "review" ? "⚠️" : "❌"}
                </div>
                <div>
                  <div className="font-bold text-sm" style={{ color: decisionColor(result.decision) }}>
                    {result.decision.toUpperCase()} — {result.decision_confidence.toUpperCase()} CONFIDENCE
                  </div>
                  <p className="text-xs text-[rgba(232,240,254,0.45)] mt-0.5">{result.decision_message}</p>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
