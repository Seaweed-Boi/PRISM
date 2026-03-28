"use client";

import { useState } from "react";
import { prismApi } from "../../lib/api";

type AdminData = {
  disruption_heatmap: Record<string, number>;
  risk_distribution: Record<string, number>;
  claim_stats: Record<string, number>;
  weekly_risk_forecast: Record<string, number>;
};

const ZONE_LABELS: Record<string, string> = {
  north: "North Delhi", south: "Bengaluru South", east: "Kolkata East",
  west: "Mumbai West", central: "Bengaluru Central",
};

function heatColor(score: number) {
  if (score < 0.3)  return "#5cc8a1";
  if (score < 0.55) return "#ffbe55";
  if (score < 0.75) return "#ff9d4a";
  return "#ff6d5a";
}

function HeatBar({ zone, score }: { zone: string; score: number }) {
  const pct = Math.round(score * 100);
  const color = heatColor(score);
  const label = pct < 30 ? "Low" : pct < 55 ? "Medium" : pct < 75 ? "High" : "Critical";
  return (
    <div className="glass rounded-xl p-4">
      <div className="flex items-start justify-between mb-2">
        <div>
          <div className="font-semibold text-sm text-white capitalize">{zone}</div>
          <div className="text-[10px] text-[rgba(232,240,254,0.4)] mono">{ZONE_LABELS[zone] ?? zone}</div>
        </div>
        <div className="text-right">
          <div className="mono font-bold text-sm" style={{ color }}>{pct}%</div>
          <div className="text-[10px]" style={{ color: `${color}aa` }}>{label}</div>
        </div>
      </div>
      <div className="h-2 rounded-full bg-white/5">
        <div
          className="h-full rounded-full score-bar-fill"
          style={{ width: `${pct}%`, background: `linear-gradient(90deg, ${color}66, ${color})` }}
        />
      </div>
    </div>
  );
}

function RingChart({ low, medium, high }: { low: number; medium: number; high: number }) {
  const total = low + medium + high || 1;
  const pcts = {
    low: Math.round((low / total) * 100),
    medium: Math.round((medium / total) * 100),
    high: Math.round((high / total) * 100),
  };
  return (
    <div className="flex items-center gap-6">
      <div className="relative h-24 w-24 shrink-0">
        <svg viewBox="0 0 36 36" className="h-24 w-24 -rotate-90">
          <circle cx="18" cy="18" r="15.9" fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="3" />
          {/* high */}
          <circle cx="18" cy="18" r="15.9" fill="none" stroke="#ff6d5a" strokeWidth="3"
            strokeDasharray={`${pcts.high} ${100 - pcts.high}`} strokeDashoffset="0" />
          {/* medium */}
          <circle cx="18" cy="18" r="15.9" fill="none" stroke="#ffbe55" strokeWidth="3"
            strokeDasharray={`${pcts.medium} ${100 - pcts.medium}`}
            strokeDashoffset={`${-pcts.high}`} />
          {/* low */}
          <circle cx="18" cy="18" r="15.9" fill="none" stroke="#5cc8a1" strokeWidth="3"
            strokeDasharray={`${pcts.low} ${100 - pcts.low}`}
            strokeDashoffset={`${-(pcts.high + pcts.medium)}`} />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-xs font-bold text-white">{total}</span>
          <span className="text-[9px] text-[rgba(232,240,254,0.4)]">policies</span>
        </div>
      </div>
      <div className="space-y-2 text-sm">
        {[
          { label: "Low Risk", count: low, pct: pcts.low, color: "#5cc8a1" },
          { label: "Medium Risk", count: medium, pct: pcts.medium, color: "#ffbe55" },
          { label: "High Risk", count: high, pct: pcts.high, color: "#ff6d5a" },
        ].map(r => (
          <div key={r.label} className="flex items-center gap-2">
            <div className="h-2 w-2 rounded-full" style={{ background: r.color }} />
            <span className="text-[rgba(232,240,254,0.6)] text-xs">{r.label}</span>
            <span className="mono text-xs font-bold ml-auto" style={{ color: r.color }}>
              {r.count} <span className="font-normal opacity-60">({r.pct}%)</span>
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function AdminPage() {
  const [data, setData] = useState<AdminData | null>(null);
  const [loading, setLoading] = useState(false);
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null);

  async function load() {
    setLoading(true);
    try {
      const d = await prismApi.adminDashboard() as AdminData;
      setData(d);
      setLastRefresh(new Date());
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  const approvalRate = data
    ? data.claim_stats.total > 0
      ? Math.round((data.claim_stats.approved / data.claim_stats.total) * 100)
      : 0
    : null;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="glass-bright rounded-2xl p-6 flex items-start justify-between gap-4">
        <div>
          <p className="mono text-xs uppercase tracking-widest text-[#4891f7]">◆ Operations Center</p>
          <h1 className="mt-1 text-3xl font-bold text-white">Admin Console</h1>
          <p className="mt-1 text-sm text-[rgba(232,240,254,0.5)]">
            System-wide disruption monitoring, risk distribution, and claim analytics
          </p>
        </div>
        <div className="text-right">
          <button
            id="refresh-analytics"
            className="btn-primary"
            onClick={load}
            disabled={loading}
          >
            {loading ? "Loading…" : "↺ Refresh Analytics"}
          </button>
          {lastRefresh && (
            <div className="mt-2 mono text-[10px] text-[rgba(232,240,254,0.3)]">
              Last: {lastRefresh.toLocaleTimeString()}
            </div>
          )}
        </div>
      </div>

      {!data ? (
        <div className="glass rounded-2xl p-12 text-center">
          <div className="text-4xl mb-4">📊</div>
          <p className="text-[rgba(232,240,254,0.4)] text-sm">Click Refresh Analytics to load real-time data</p>
        </div>
      ) : (
        <>
          {/* Top stats */}
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {[
              { label: "Total Claims", value: data.claim_stats.total, icon: "📋", color: "#4891f7" },
              { label: "Approved", value: data.claim_stats.approved, icon: "✅", color: "#5cc8a1" },
              { label: "Rejected", value: data.claim_stats.rejected, icon: "❌", color: "#ff6d5a" },
              {
                label: "Approval Rate",
                value: `${approvalRate}%`,
                icon: "📈",
                color: approvalRate && approvalRate > 70 ? "#5cc8a1" : "#ffbe55",
              },
            ].map(s => (
              <div
                key={s.label}
                className="glass rounded-2xl p-5 relative overflow-hidden"
                style={{ border: `1px solid ${s.color}25` }}
              >
                <div className="absolute top-3 right-3 text-2xl opacity-20">{s.icon}</div>
                <div className="mono text-[10px] uppercase tracking-widest mb-1" style={{ color: `${s.color}99` }}>
                  {s.label}
                </div>
                <div className="text-3xl font-bold text-white">{s.value}</div>
              </div>
            ))}
          </div>

          <div className="grid gap-6 lg:grid-cols-2">
            {/* Disruption Heatmap */}
            <div className="glass rounded-2xl p-5">
              <h2 className="font-semibold text-white mb-4 flex items-center gap-2">
                <span className="text-lg">🌡</span> Disruption Heatmap
              </h2>
              <div className="space-y-3">
                {Object.entries(data.disruption_heatmap).map(([zone, score]) => (
                  <HeatBar key={zone} zone={zone} score={score} />
                ))}
              </div>
            </div>

            {/* Risk distribution */}
            <div className="space-y-5">
              <div className="glass rounded-2xl p-5">
                <h2 className="font-semibold text-white mb-4 flex items-center gap-2">
                  <span className="text-lg">🎯</span> Risk Distribution
                </h2>
                <RingChart
                  low={data.risk_distribution.low}
                  medium={data.risk_distribution.medium}
                  high={data.risk_distribution.high}
                />
              </div>

              {/* Weekly forecast */}
              <div className="glass rounded-2xl p-5">
                <h2 className="font-semibold text-white mb-4 flex items-center gap-2">
                  <span className="text-lg">📅</span> Weekly Risk Forecast
                </h2>
                <div className="space-y-2">
                  {Object.entries(data.weekly_risk_forecast).map(([zone, score]) => {
                    const pct = Math.round(score * 100);
                    const color = heatColor(score);
                    return (
                      <div key={zone} className="flex items-center gap-3">
                        <span className="w-16 text-xs capitalize text-[rgba(232,240,254,0.6)]">{zone}</span>
                        <div className="flex-1 h-1.5 rounded-full bg-white/5">
                          <div className="h-full rounded-full score-bar-fill" style={{ width: `${pct}%`, background: color }} />
                        </div>
                        <span className="mono text-xs w-8 text-right" style={{ color }}>{pct}%</span>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
