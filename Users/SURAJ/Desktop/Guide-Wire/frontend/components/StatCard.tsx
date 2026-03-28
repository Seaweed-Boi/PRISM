type Props = {
  label: string;
  value: string;
  tone?: "mint" | "amber" | "coral" | "deep";
};

const toneClass: Record<NonNullable<Props["tone"]>, string> = {
  mint: "bg-prism-mint/20 border-prism-mint/40",
  amber: "bg-prism-amber/20 border-prism-amber/40",
  coral: "bg-prism-coral/20 border-prism-coral/40",
  deep: "bg-prism-deep/10 border-prism-deep/20"
};

export default function StatCard({ label, value, tone = "deep" }: Props) {
  return (
    <div className={`rounded-2xl border p-4 ${toneClass[tone]}`}>
      <p className="mono text-xs uppercase tracking-wider text-prism-deep/70">{label}</p>
      <p className="mt-1 text-2xl font-bold text-prism-deep">{value}</p>
    </div>
  );
}
