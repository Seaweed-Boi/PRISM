"use client";

import { ChangeEvent, useMemo, useState } from "react";
import { prismApi } from "../../lib/api";

type Worker = { id: number; name: string; zone: string; platform: string };
type Policy = { id: number; expected_hourly_income: number; premium: number; risk_tier: string };
type Dashboard = { expected_hourly_income: number; protected_income: number; active_policies: number; total_payout: number };
type ClaimResult = { id: number; status: string; loss_amount: number; fraud_score: number; payout?: number };

function StatCard({
  label, value, sub, icon, color,
}: {
  label: string; value: string; sub?: string; icon: string; color: string;
}) {
  return (
    <div
      className="glass rounded-2xl p-5 relative overflow-hidden"
      style={{ borderColor: `${color}30`, borderWidth: 1, borderStyle: "solid" }}
    >
      <div className="absolute top-3 right-3 text-xl opacity-30">{icon}</div>
      <div className="mono text-[10px] uppercase tracking-widest mb-1" style={{ color: `${color}aa` }}>
        {label}
      </div>
      <div className="text-2xl font-bold text-white">{value}</div>
      {sub && <div className="text-xs mt-1" style={{ color: `${color}80` }}>{sub}</div>}
    </div>
  );
}

function StepBadge({ step, label, done }: { step: number; label: string; done: boolean }) {
  return (
    <div className="flex items-center gap-2">
      <div
        className="flex h-6 w-6 items-center justify-center rounded-full text-xs font-bold shrink-0"
        style={{
          background: done ? "rgba(92,200,161,0.2)" : "rgba(255,255,255,0.05)",
          border: `1px solid ${done ? "rgba(92,200,161,0.5)" : "rgba(255,255,255,0.1)"}`,
          color: done ? "#5cc8a1" : "rgba(232,240,254,0.4)",
        }}
      >
        {done ? "✓" : step}
      </div>
      <span className="text-xs" style={{ color: done ? "#5cc8a1" : "rgba(232,240,254,0.5)" }}>
        {label}
      </span>
    </div>
  );
}

const PLATFORMS = ["Swiggy", "Zomato", "Amazon Flex", "Blinkit", "Dunzo"];
const ZONES = ["north", "south", "east", "west", "central"];
const HOURS = ["8:00-16:00", "10:00-18:00", "12:00-20:00", "16:00-24:00", "18:00-02:00"];

export default function WorkerPage() {
  const [name, setName] = useState("Suraj");
  const [platform, setPlatform] = useState("Swiggy");
  const [zone, setZone] = useState("central");
  const [hours, setHours] = useState("10:00-18:00");

  const [worker, setWorker] = useState<Worker | null>(null);
  const [policy, setPolicy] = useState<Policy | null>(null);
  const [dashboard, setDashboard] = useState<Dashboard | null>(null);
  const [claimResult, setClaimResult] = useState<ClaimResult | null>(null);
  const [loading, setLoading] = useState<string>("");
  const [log, setLog] = useState<string[]>([]);

  const canBuyPolicy = !!worker;
  const canSimulate = !!worker && !!policy;

  function addLog(msg: string) {
    setLog(prev => [`[${new Date().toLocaleTimeString()}] ${msg}`, ...prev].slice(0, 10));
  }

  async function onboard() {
    setLoading("onboard");
    try {
      const created = await prismApi.createWorker({ name, platform, zone, working_hours: hours }) as Worker;
      setWorker(created);
      addLog(`✅ Worker #${created.id} "${created.name}" onboarded on ${platform} — zone: ${zone}`);
    } catch (err) {
      addLog(`❌ ${String(err)}`);
    } finally { setLoading(""); }
  }

  async function buyPolicy() {
    if (!worker) return;
    setLoading("policy");
    try {
      const now = new Date();
      const next = new Date(now); next.setDate(now.getDate() + 7);
      const created = await prismApi.buyPolicy({
        worker_id: worker.id,
        week_start: now.toISOString().slice(0, 10),
        week_end: next.toISOString().slice(0, 10),
      }) as Policy;
      setPolicy(created);
      addLog(`📋 Policy #${created.id} purchased — ${created.risk_tier} risk · ₹${created.premium}/week · Expected: ₹${created.expected_hourly_income}/hr`);
      await refreshDashboard(worker.id);
    } catch (err) {
      addLog(`❌ ${String(err)}`);
    } finally { setLoading(""); }
  }

  async function simulateDisruption(type: string) {
    if (!worker || !policy) return;
    setLoading("simulate");
    try {
      const drops: Record<string, number> = { rain: 95, traffic: 70, pollution: 50, outage: 120 };
      const drop = drops[type] ?? 80;
      const actual = Math.max(policy.expected_hourly_income - drop, 30);
      const claim = await prismApi.triggerClaim({
        worker_id: worker.id,
        policy_id: policy.id,
        expected_income: policy.expected_hourly_income,
        actual_income: actual,
        trigger_source: type,
        lat: 12.9716,
        lon: 77.5946,
        activity_score: 0.82,
      }) as ClaimResult;
      setClaimResult(claim);
      addLog(
        `${claim.status === "approved" ? "💰" : "🚫"} Claim #${claim.id} — ${claim.status.toUpperCase()} ` +
        `| Loss: ₹${claim.loss_amount?.toFixed(2)} | Fraud: ${(claim.fraud_score * 100).toFixed(0)}%`
      );
      await refreshDashboard(worker.id);
    } catch (err) {
      addLog(`❌ ${String(err)}`);
    } finally { setLoading(""); }
  }

  async function refreshDashboard(wid: number) {
    const data = await prismApi.workerDashboard(wid) as Dashboard;
    setDashboard(data);
  }

  const riskColors: Record<string, string> = {
    low: "#5cc8a1", medium: "#ffbe55", high: "#ff6d5a",
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="glass-bright rounded-2xl p-6 flex items-start justify-between">
        <div>
          <p className="mono text-xs uppercase tracking-widest text-[#5cc8a1]">◆ Demo Flow</p>
          <h1 className="mt-1 text-3xl font-bold text-white">Worker Console</h1>
          <p className="mt-1 text-sm text-[rgba(232,240,254,0.5)]">
            Onboard → Buy Policy → Simulate Disruption → Auto Claim
          </p>
        </div>
        {/* Step progress */}
        <div className="hidden md:flex flex-col gap-2">
          <StepBadge step={1} label="Onboard" done={!!worker} />
          <StepBadge step={2} label="Buy Policy" done={!!policy} />
          <StepBadge step={3} label="Simulate" done={!!claimResult} />
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-[340px_1fr]">
        {/* ── Left: Controls ── */}
        <div className="space-y-5">
          {/* Onboarding form */}
          <div className="glass rounded-2xl p-5">
            <h2 className="font-semibold text-white mb-4 text-sm flex items-center gap-2">
              <span className="status-active">Step 1</span> Worker Registration
            </h2>
            <div className="space-y-3">
              <div>
                <label className="block text-xs text-[rgba(232,240,254,0.5)] mb-1">Full Name</label>
                <input
                  id="worker-name"
                  className="prism-input"
                  value={name}
                  onChange={(e: ChangeEvent<HTMLInputElement>) => setName(e.target.value)}
                  placeholder="Delivery partner name"
                />
              </div>
              <div>
                <label className="block text-xs text-[rgba(232,240,254,0.5)] mb-1">Platform</label>
                <select
                  id="worker-platform"
                  className="prism-select"
                  value={platform}
                  onChange={(e: ChangeEvent<HTMLSelectElement>) => setPlatform(e.target.value)}
                >
                  {PLATFORMS.map(p => <option key={p} value={p}>{p}</option>)}
                </select>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs text-[rgba(232,240,254,0.5)] mb-1">Zone</label>
                  <select
                    id="worker-zone"
                    className="prism-select"
                    value={zone}
                    onChange={(e: ChangeEvent<HTMLSelectElement>) => setZone(e.target.value)}
                  >
                    {ZONES.map(z => <option key={z} value={z}>{z}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-xs text-[rgba(232,240,254,0.5)] mb-1">Working Hours</label>
                  <select
                    id="worker-hours"
                    className="prism-select"
                    value={hours}
                    onChange={(e: ChangeEvent<HTMLSelectElement>) => setHours(e.target.value)}
                  >
                    {HOURS.map(h => <option key={h} value={h}>{h}</option>)}
                  </select>
                </div>
              </div>
            </div>
            <button
              id="onboard-btn"
              className="btn-primary w-full mt-4"
              onClick={onboard}
              disabled={loading === "onboard"}
            >
              {loading === "onboard" ? "Registering…" : worker ? `✓ Registered as #${worker.id}` : "Step 1: Onboard Worker"}
            </button>
          </div>

          {/* Policy purchase */}
          <div className="glass rounded-2xl p-5">
            <h2 className="font-semibold text-white mb-3 text-sm flex items-center gap-2">
              <span className={canBuyPolicy ? "status-active" : "status-degraded"}>Step 2</span>
              Weekly Policy
            </h2>
            {policy ? (
              <div className="rounded-xl p-3 text-sm space-y-1" style={{ background: `${riskColors[policy.risk_tier]}0f`, border: `1px solid ${riskColors[policy.risk_tier]}25` }}>
                <div className="flex justify-between">
                  <span className="text-[rgba(232,240,254,0.5)]">Risk Tier</span>
                  <span className="font-semibold capitalize" style={{ color: riskColors[policy.risk_tier] }}>{policy.risk_tier}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[rgba(232,240,254,0.5)]">Premium</span>
                  <span className="font-semibold text-white">₹{policy.premium}/week</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[rgba(232,240,254,0.5)]">Expected ₹/hr</span>
                  <span className="font-semibold text-white">₹{policy.expected_hourly_income?.toFixed(2)}</span>
                </div>
              </div>
            ) : (
              <p className="text-xs text-[rgba(232,240,254,0.4)] mb-3">
                AI will calculate your zone risk and set appropriate weekly premium.
              </p>
            )}
            <button
              id="buy-policy-btn"
              className="btn-primary w-full mt-3"
              onClick={buyPolicy}
              disabled={!canBuyPolicy || loading === "policy"}
            >
              {loading === "policy" ? "Processing…" : "Step 2: Buy Weekly Policy"}
            </button>
          </div>

          {/* Disruption simulation */}
          <div className="glass rounded-2xl p-5">
            <h2 className="font-semibold text-white mb-3 text-sm flex items-center gap-2">
              <span className={canSimulate ? "status-active" : "status-degraded"}>Step 3</span>
              Simulate Disruption
            </h2>
            <div className="grid grid-cols-2 gap-2">
              {[
                { type: "rain", icon: "🌧", label: "Heavy Rain", drop: 95 },
                { type: "traffic", icon: "🚗", label: "Traffic Jam", drop: 70 },
                { type: "pollution", icon: "😷", label: "AQI Spike", drop: 50 },
                { type: "outage", icon: "📵", label: "App Outage", drop: 120 },
              ].map(d => (
                <button
                  key={d.type}
                  id={`sim-${d.type}`}
                  className="glass rounded-xl p-3 text-left hover:scale-[1.02] transition-transform disabled:opacity-40 disabled:cursor-not-allowed"
                  onClick={() => simulateDisruption(d.type)}
                  disabled={!canSimulate || loading === "simulate"}
                >
                  <div className="text-xl mb-1">{d.icon}</div>
                  <div className="text-xs font-semibold text-white">{d.label}</div>
                  <div className="text-[10px] text-[rgba(232,240,254,0.4)] mono">−₹{d.drop}/hr impact</div>
                </button>
              ))}
            </div>
          </div>

          {/* Claim result */}
          {claimResult && (
            <div
              className="glass rounded-2xl p-5 border"
              style={{
                borderColor: claimResult.status === "approved" ? "rgba(92,200,161,0.35)" : "rgba(255,109,90,0.35)",
              }}
            >
              <h3 className="font-semibold text-sm text-white mb-3">Claim Result</h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-[rgba(232,240,254,0.5)]">Status</span>
                  <span
                    className="font-bold uppercase"
                    style={{ color: claimResult.status === "approved" ? "#5cc8a1" : "#ff6d5a" }}
                  >
                    {claimResult.status}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[rgba(232,240,254,0.5)]">Income Loss</span>
                  <span className="font-semibold text-white">₹{claimResult.loss_amount?.toFixed(2)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[rgba(232,240,254,0.5)]">Fraud Score</span>
                  <span className="font-semibold mono" style={{ color: claimResult.fraud_score < 0.5 ? "#5cc8a1" : "#ff6d5a" }}>
                    {(claimResult.fraud_score * 100).toFixed(0)}%
                  </span>
                </div>
                {claimResult.status === "approved" && (
                  <div className="flex justify-between border-t border-white/10 pt-2 mt-2">
                    <span className="text-[rgba(232,240,254,0.5)]">Payout (90%)</span>
                    <span className="font-bold text-[#5cc8a1]">₹{(claimResult.loss_amount * 0.9).toFixed(2)}</span>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* ── Right: Dashboard stats + log ── */}
        <div className="space-y-5">
          {/* Stats */}
          <div className="grid gap-4 sm:grid-cols-2">
            <StatCard
              label="Expected ₹/hr"
              value={`₹${dashboard?.expected_hourly_income?.toFixed(2) ?? "—"}`}
              sub="AI earnings prediction"
              icon="🎯"
              color="#4891f7"
            />
            <StatCard
              label="Protected Income"
              value={`₹${dashboard?.protected_income?.toFixed(2) ?? "—"}`}
              sub="Weekly (8hr × 6 days)"
              icon="🛡"
              color="#5cc8a1"
            />
            <StatCard
              label="Active Policies"
              value={String(dashboard?.active_policies ?? "—")}
              sub="Currently insured"
              icon="📋"
              color="#ffbe55"
            />
            <StatCard
              label="Total Payout"
              value={`₹${dashboard?.total_payout?.toFixed(2) ?? "—"}`}
              sub="Cumulative payouts received"
              icon="💰"
              color="#ff6d5a"
            />
          </div>

          {/* Worker profile */}
          {worker && (
            <div className="glass rounded-2xl p-5">
              <h3 className="font-semibold text-white text-sm mb-3">Worker Profile</h3>
              <div className="flex items-center gap-4">
                <div className="h-12 w-12 rounded-full bg-gradient-to-br from-[#5cc8a1] to-[#4891f7] flex items-center justify-center text-white font-bold text-lg">
                  {worker.name.charAt(0)}
                </div>
                <div>
                  <div className="font-semibold text-white">{worker.name}</div>
                  <div className="text-xs text-[rgba(232,240,254,0.5)]">
                    {worker.platform} · {worker.zone} zone · ID #{worker.id}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Activity log */}
          <div className="glass rounded-2xl p-5">
            <h3 className="font-semibold text-white text-sm mb-3 flex items-center justify-between">
              <span>Activity Log</span>
              <span className="mono text-[10px] text-[rgba(232,240,254,0.3)]">{log.length} events</span>
            </h3>
            <div className="space-y-1.5 max-h-64 overflow-y-auto">
              {log.length === 0 ? (
                <p className="mono text-xs text-[rgba(232,240,254,0.3)]">
                  No activity yet. Run the demo steps above.
                </p>
              ) : (
                log.map((entry, i) => (
                  <div
                    key={i}
                    className="mono text-xs rounded-lg px-3 py-2 bg-black/20 text-[rgba(232,240,254,0.65)]"
                  >
                    {entry}
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Pipeline reference */}
          <div className="glass rounded-2xl p-5">
            <h3 className="font-semibold text-white text-sm mb-3">PRISM Architecture Flow</h3>
            <div className="flex flex-wrap gap-2 items-center text-xs text-[rgba(232,240,254,0.45)]">
              {["External APIs", "Disruption Engine", "AI Risk Model", "Policy Engine", "Fraud Detection", "Payout System"].map((s, i, arr) => (
                <span key={s} className="flex items-center gap-2">
                  <span className="px-2 py-0.5 rounded-md glass mono" style={{ border: "1px solid rgba(92,200,161,0.15)" }}>{s}</span>
                  {i < arr.length - 1 && <span className="text-[rgba(92,200,161,0.4)]">→</span>}
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
