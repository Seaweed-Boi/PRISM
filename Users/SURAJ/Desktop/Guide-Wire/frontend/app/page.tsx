import Link from "next/link";

export default function HomePage() {
  return (
    <div className="space-y-12">
      {/* Hero */}
      <section className="relative overflow-hidden rounded-3xl glass-bright p-10 md:p-16 glow-mint">
        {/* Background decoration */}
        <div className="pointer-events-none absolute inset-0 overflow-hidden rounded-3xl">
          <div className="absolute -top-20 -right-20 h-72 w-72 rounded-full bg-[#4891f7] opacity-10 blur-3xl" />
          <div className="absolute -bottom-20 -left-20 h-64 w-64 rounded-full bg-[#5cc8a1] opacity-10 blur-3xl" />
        </div>

        <div className="relative z-10">
          <p className="mono text-xs uppercase tracking-[0.25em] text-[#5cc8a1]">
            ◆ AI-Powered Parametric Insurance
          </p>
          <h1 className="mt-4 text-5xl font-bold leading-tight md:text-6xl">
            <span className="gradient-text">PRISM</span>
          </h1>
          <p className="mt-2 text-xl font-light text-[rgba(232,240,254,0.7)]">
            Predictive Income Protection for Gig Workers
          </p>
          <p className="mt-5 max-w-2xl text-base text-[rgba(232,240,254,0.55)] leading-relaxed">
            AI risk scoring, real-time disruption monitoring, multi-layer fraud detection,
            and parametric claims with instant payout simulation — all in one platform.
          </p>

          <div className="mt-8 flex flex-wrap gap-3">
            <Link href="/worker" className="btn-primary">
              Worker Dashboard →
            </Link>
            <Link href="/admin" className="btn-ghost">
              Admin Console
            </Link>
            <Link href="/fraud" className="btn-ghost" style={{ borderColor: "rgba(167,139,250,0.4)", color: "#a78bfa" }}>
              Fraud Engine
            </Link>
          </div>
        </div>
      </section>

      {/* Architecture pipeline overview */}
      <section>
        <h2 className="mb-6 text-xl font-semibold text-[rgba(232,240,254,0.7)]">
          System Architecture
        </h2>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {[
            {
              icon: "🌦",
              title: "Disruption Monitoring",
              desc: "Real-time weather, traffic & AQI feeds drive the parametric trigger engine",
              color: "#4891f7",
            },
            {
              icon: "🧠",
              title: "AI Risk Scoring",
              desc: "ML earnings prediction + zone-based risk tiers generate dynamic weekly premiums",
              color: "#5cc8a1",
            },
            {
              icon: "🔍",
              title: "Fraud Detection",
              desc: "4-layer pipeline: ML anomaly detection, GPS location, activity validation, Redis dedup",
              color: "#a78bfa",
            },
            {
              icon: "⚡",
              title: "Instant Payout",
              desc: "Decision engine auto-approves claims and triggers 90% loss-coverage payouts",
              color: "#ffbe55",
            },
          ].map((item) => (
            <div key={item.title} className="glass rounded-2xl p-5 hover:scale-[1.02] transition-transform duration-300">
              <div
                className="mb-3 flex h-11 w-11 items-center justify-center rounded-xl text-xl"
                style={{ background: `${item.color}18`, border: `1px solid ${item.color}30` }}
              >
                {item.icon}
              </div>
              <h3 className="font-semibold text-sm text-white mb-1">{item.title}</h3>
              <p className="text-xs text-[rgba(232,240,254,0.5)] leading-relaxed">{item.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Demo flow steps */}
      <section>
        <h2 className="mb-6 text-xl font-semibold text-[rgba(232,240,254,0.7)]">
          Demo Flow
        </h2>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
          {[
            { step: "01", label: "Register", desc: "Onboard with platform + zone", href: "/worker" },
            { step: "02", label: "Buy Policy", desc: "Weekly parametric plan", href: "/worker" },
            { step: "03", label: "AI Prediction", desc: "Earnings forecast created", href: "/worker" },
            { step: "04", label: "Disruption", desc: "Simulate rain / traffic", href: "/worker" },
            { step: "05", label: "Instant Payout", desc: "Auto claim + payout", href: "/worker" },
          ].map((s, i) => (
            <Link
              key={s.step}
              href={s.href}
              className="group glass rounded-xl p-4 hover:border-[rgba(92,200,161,0.4)] transition-all duration-300 block"
            >
              <div className="mono text-[#5cc8a1] text-xs mb-2 opacity-70">{s.step}</div>
              <div className="font-semibold text-sm text-white group-hover:text-[#5cc8a1] transition-colors">
                {s.label}
              </div>
              <div className="text-xs text-[rgba(232,240,254,0.45)] mt-1">{s.desc}</div>
              {i < 4 && (
                <div className="hidden lg:block absolute -right-2 top-1/2 -translate-y-1/2 text-[rgba(92,200,161,0.4)] text-lg z-10">
                  →
                </div>
              )}
            </Link>
          ))}
        </div>
      </section>

      {/* Quick links */}
      <section className="grid gap-4 md:grid-cols-3">
        {[
          {
            title: "Worker Dashboard",
            desc: "Onboard, buy policy, simulate disruption & auto-trigger parametric claim",
            href: "/worker",
            gradient: "from-[#5cc8a1] to-[#4891f7]",
            icon: "👷",
          },
          {
            title: "Admin Console",
            desc: "Disruption heatmaps, risk distribution, claim stats & weekly forecasts",
            href: "/admin",
            gradient: "from-[#4891f7] to-[#a78bfa]",
            icon: "📊",
          },
          {
            title: "Fraud Engine",
            desc: "Live fraud pipeline: ML anomaly → GPS → activity → Redis dedup → decision",
            href: "/fraud",
            gradient: "from-[#a78bfa] to-[#ff6d5a]",
            icon: "🛡",
          },
        ].map((card) => (
          <Link
            key={card.href}
            href={card.href}
            className="group glass rounded-2xl p-6 hover:scale-[1.02] transition-all duration-300 block"
          >
            <div
              className={`mb-4 inline-flex h-12 w-12 items-center justify-center rounded-xl text-2xl bg-gradient-to-br ${card.gradient} bg-opacity-20`}
              style={{ background: "transparent", fontSize: "1.5rem" }}
            >
              {card.icon}
            </div>
            <h3 className={`font-bold text-lg bg-gradient-to-r ${card.gradient} bg-clip-text text-transparent`}>
              {card.title}
            </h3>
            <p className="mt-2 text-sm text-[rgba(232,240,254,0.5)] leading-relaxed">
              {card.desc}
            </p>
            <span className="mt-4 inline-block text-xs text-[rgba(232,240,254,0.35)] group-hover:text-[#5cc8a1] transition-colors">
              Open →
            </span>
          </Link>
        ))}
      </section>
    </div>
  );
}
