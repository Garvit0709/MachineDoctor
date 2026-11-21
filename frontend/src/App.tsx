
import { Activity, ArrowRight, Cpu, ShieldCheck } from 'lucide-react'

function App() {
  return (
    <main className="min-h-screen bg-[#0B1220] text-slate-100">
      <header className="border-b border-slate-800/80">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-5">
          <div className="flex items-center gap-3">
            <div className="rounded-xl bg-cyan-400/10 p-3 text-cyan-400">
              <Activity size={25} strokeWidth={2.2} />
            </div>

            <div>
              <h1 className="text-xl font-bold tracking-tight">
                MachineDoctor
              </h1>
              <p className="text-xs font-medium tracking-[0.2em] text-cyan-400">
                POWERED BY AURA
              </p>
            </div>
          </div>

          <span className="rounded-full border border-slate-700 px-4 py-2 text-xs text-slate-400">
            Research Prototype v0.1
          </span>
        </div>
      </header>

      <section className="mx-auto max-w-7xl px-6 py-24">
        <div className="max-w-3xl">
          <div className="mb-7 inline-flex items-center gap-2 rounded-full border border-cyan-400/20 bg-cyan-400/5 px-4 py-2 text-sm text-cyan-300">
            <Cpu size={16} />
            Intelligent Motor-Bearing Diagnostics
          </div>

          <h2 className="text-5xl font-semibold leading-tight tracking-tight md:text-7xl">
            Understand your machines.
            <span className="block text-cyan-400">
              Before problems escalate.
            </span>
          </h2>

          <p className="mt-8 max-w-2xl text-lg leading-8 text-slate-400">
            MachineDoctor is an experimental condition-monitoring
            platform powered by AURA, a research algorithm for
            analyzing motor-bearing vibration, persistent anomalies,
            and operating-condition uncertainty.
          </p>

          <div className="mt-10 flex flex-wrap gap-4">
            <a
              href="#capabilities"
              className="inline-flex items-center gap-2 rounded-xl bg-cyan-400 px-6 py-3 font-semibold text-slate-950 transition hover:bg-cyan-300"
            >
              Explore Capabilities
              <ArrowRight size={18} />
            </a>

            <span className="flex items-center gap-2 rounded-xl border border-slate-700 px-6 py-3 text-sm text-slate-400">
              <ShieldCheck size={18} />
              Research and validation in progress
            </span>
          </div>
        </div>

        <div
          id="capabilities"
          className="mt-24 grid gap-5 md:grid-cols-3"
        >
          {[
            {
              title: 'Vibration Analysis',
              description:
                'Explore motor-bearing vibration signals and extracted diagnostic features.',
            },
            {
              title: 'AURA Intelligence',
              description:
                'Inspect residual evidence, short-term memory, and operating-condition uncertainty.',
            },
            {
              title: 'Diagnostic History',
              description:
                'Review analysis sessions and track changes in machine condition.',
            },
          ].map((item) => (
            <article
              key={item.title}
              className="rounded-2xl border border-slate-800 bg-[#111C2D] p-7"
            >
              <div className="mb-5 h-1 w-10 rounded-full bg-cyan-400" />
              <h3 className="text-xl font-semibold">
                {item.title}
              </h3>
              <p className="mt-3 leading-7 text-slate-400">
                {item.description}
              </p>
            </article>
          ))}
        </div>
      </section>
    </main>
  )
}

export default App
