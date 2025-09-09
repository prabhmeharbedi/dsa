"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import trackerData from "./tracker_data.json";
import { motion } from "framer-motion";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";

// Helpers to create persistent keys
const makeDSAKey = (p: { number: string; title: string }) => `dsa:${p.number}:${p.title}`;
const makeSDKey = (weekNum: number, dayNum: number, index: number) => `sd:${weekNum}:${dayNum}:${index}`;

type CompletionMap = Record<string, boolean>;

export default function Home() {
  const weeks = trackerData.weeks as Array<{
    number: number;
    days: Array<{
      number: number;
      dsa_problems: Array<{ number: string; title: string; difficulty: string; url: string }>;
      system_design_tasks: Array<{ description: string; is_bonus: boolean }>;
    }>;
  }>;

  const [activeTab, setActiveTab] = useState<"overview" | "dsa" | "system">("overview");

  // --- MODIFICATION 1: Use `null` to represent "not yet loaded" state ---
  const [completion, setCompletion] = useState<CompletionMap | null>(null);
  const [lastSynced, setLastSynced] = useState<string>("");
  const [isSyncing, setIsSyncing] = useState(false);
  const [syncError, setSyncError] = useState<string | null>(null);
  const saveTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Load from server on mount
  useEffect(() => {
    let cancelled = false;
    const loadState = async () => {
      try {
        setSyncError(null);
        const res = await fetch("/api/state", { cache: "no-store" });
        if (!res.ok) throw new Error(`Failed to load state (${res.status})`);
        const data = (await res.json()) as { completion?: CompletionMap; updatedAt?: number };
        if (cancelled) return;
        setCompletion(data.completion || {}); // Set to empty object if no data
        if (data.updatedAt) setLastSynced(new Date(data.updatedAt).toLocaleString());
      } catch (e: any) {
        if (!cancelled) {
          setSyncError(e?.message || "Failed to load from cloud. Check network.");
          // Don't set an empty state on failure, let it stay null
        }
      }
    };

    loadState();

    return () => {
      cancelled = true;
    };
  }, []);

  // Debounced save to cloud
  useEffect(() => {
    // --- MODIFICATION 2: Do NOT save if completion state is `null` (not loaded yet) ---
    if (completion === null) {
      return;
    }

    if (saveTimer.current) clearTimeout(saveTimer.current);
    saveTimer.current = setTimeout(async () => {
      try {
        setIsSyncing(true);
        setSyncError(null);
        const res = await fetch("/api/state", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ completion, updatedAt: Date.now() }),
        });
        if (!res.ok) throw new Error("Failed to sync");
        const data = (await res.json()) as { updatedAt?: number };
        const ts = new Date(data.updatedAt || Date.now()).toLocaleString();
        setLastSynced(ts);
      } catch (e: any) {
        setSyncError(e?.message || "Sync failed");
      } finally {
        setIsSyncing(false);
      }
    }, 500); // Debounce saves by 500ms

    return () => {
      if (saveTimer.current) clearTimeout(saveTimer.current);
    };
  }, [completion]); // Only depends on completion now

  const toggleKey = (key: string) => {
    if (completion === null) return; // Prevent toggling if not loaded
    setCompletion((prev) => ({ ...prev, [key]: !prev?.[key] }));
  };

  const resetProgress = () => {
    if (confirm("Reset all progress?")) {
      setCompletion({});
    }
  };

  // Totals and progress calculations
  const { totals, weeklyProgress } = useMemo(() => {
    // Return zeroed-out stats if data hasn't loaded yet
    const safeCompletion = completion || {};
    let totalDSA = 0, doneDSA = 0, totalSD = 0, doneSD = 0;

    const wp: Array<{ week: string; completed: number }> = [];

    weeks.forEach((week) => {
      let wTotal = 0;
      let wDone = 0;

      week.days.forEach((day) => {
        day.dsa_problems.forEach((p) => {
          totalDSA += 1;
          wTotal += 1;
          if (safeCompletion[makeDSAKey(p)]) {
            doneDSA += 1;
            wDone += 1;
          }
        });
        day.system_design_tasks.forEach((_, idx) => {
          totalSD += 1;
          wTotal += 1;
          if (safeCompletion[makeSDKey(week.number, day.number, idx)]) {
            doneSD += 1;
            wDone += 1;
          }
        });
      });
      wp.push({ week: `W${week.number}`, completed: wTotal ? Math.round((wDone / wTotal) * 100) : 0 });
    });

    const totalAll = totalDSA + totalSD;
    const doneAll = doneDSA + doneSD;
    const pct = (n: number, d: number) => (d ? Math.round((n / d) * 100) : 0);

    return {
      weeklyProgress: wp,
      totals: { totalDSA, doneDSA, totalSD, doneSD, totalAll, doneAll,
        pctAll: pct(doneAll, totalAll),
        pctDSA: pct(doneDSA, totalDSA),
        pctSD: pct(doneSD, totalSD),
      },
    };
  }, [completion, weeks]);

  // If data is not loaded yet, show a loading screen. This is critical.
  if (completion === null) {
    return (
      <div className="min-h-screen bg-[#0a0a0a] flex flex-col items-center justify-center text-gray-400">
        <p>Loading your progress from the database...</p>
        {syncError && <p className="mt-4 text-rose-400">Error: {syncError}</p>}
      </div>
    );
  }

  const TabButton = ({ id, label }: { id: "overview" | "dsa" | "system"; label: string }) => (
      <button
        onClick={() => setActiveTab(id)}
        className={`px-4 py-2 rounded-md text-sm transition-all border ${
          activeTab === id
            ? "bg-gradient-to-r from-blue-500/80 to-purple-600/80 text-white border-transparent shadow"
            : "bg-[#0b0b0b] border-[#1f1f1f] text-gray-300 hover:border-[#2a2a2a] hover:text-white"
        }`}
        aria-pressed={activeTab === id}
      >
        {label}
      </button>
  );

  const ProgressBar = ({ pct, colorFrom, colorTo }: { pct: number; colorFrom: string; colorTo: string }) => (
    <div className="w-full bg-[#151515] border border-[#262626] rounded-md h-2.5 overflow-hidden">
      <div
        className={`h-2.5 rounded-md bg-gradient-to-r ${colorFrom} ${colorTo}`}
        style={{ width: `${Math.min(100, Math.max(0, pct))}%`, filter: "saturate(0.9) brightness(0.95)" }}
        aria-valuenow={pct}
        aria-valuemin={0}
        aria-valuemax={100}
        role="progressbar"
      />
    </div>
  );

  return (
    <div className="min-h-screen bg-gradient-to-b from-[#0a0a0a] to-[#0e0e0e] text-white px-5 py-8">
       <motion.header initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} className="max-w-6xl mx-auto mb-6">
         <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
           <div>
             <h1 className="text-2xl md:text-4xl font-semibold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-blue-400/90 to-purple-500/90">
               DSA 100-Day Tracker
             </h1>
             <p className="text-sm text-gray-400 mt-1">Stay focused. Progress with clarity. Build momentum daily.</p>
           </div>
 
           <div className="flex items-center gap-3 text-sm text-gray-400">
             <TabButton id="overview" label="Overview" />
             <TabButton id="dsa" label="DSA" />
             <TabButton id="system" label="System Design" />
             <span className={isSyncing ? "text-yellow-300" : "text-gray-400"}>
               {isSyncing ? "Syncing…" : lastSynced ? `Last synced: ${lastSynced}` : "Not yet synced"}
             </span>
             {syncError && <span className="text-rose-400">{syncError}</span>}
           </div>
         </div>
       </motion.header>
 
       <main className="max-w-6xl mx-auto space-y-6">
         <section className="grid grid-cols-1 md:grid-cols-3 gap-5">
           <motion.div whileHover={{ scale: 1.01 }} className="bg-[#111] border border-[#1f1f1f] p-5 rounded-xl">
             <h2 className="text-sm text-gray-400 mb-2">Overall Progress</h2>
             <div className="flex items-end justify-between">
               <div className="text-4xl font-bold text-blue-300">{totals.pctAll}%</div>
               <button onClick={resetProgress} className="text-xs text-gray-300 hover:text-white underline">
                 Reset
               </button>
             </div>
             <div className="mt-3">
               <ProgressBar pct={totals.pctAll} colorFrom="from-blue-500" colorTo="to-purple-600" />
             </div>
             <p className="text-xs text-gray-500 mt-2">
               {totals.doneAll} of {totals.totalAll} items completed
             </p>
           </motion.div>
 
           <motion.div whileHover={{ scale: 1.01 }} className="bg-[#111] border border-[#1f1f1f] p-5 rounded-xl">
             <h2 className="text-sm text-gray-400 mb-2">DSA Progress</h2>
             <div className="text-3xl font-semibold text-orange-300">{totals.pctDSA}%</div>
             <div className="mt-3">
               <ProgressBar pct={totals.pctDSA} colorFrom="from-orange-500" colorTo="to-amber-500" />
             </div>
             <p className="text-xs text-gray-500 mt-2">
               {totals.doneDSA} of {totals.totalDSA} problems completed
             </p>
           </motion.div>
 
           <motion.div whileHover={{ scale: 1.01 }} className="bg-[#111] border border-[#1f1f1f] p-5 rounded-xl">
             <h2 className="text-sm text-gray-400 mb-2">System Design Progress</h2>
             <div className="text-3xl font-semibold text-emerald-300">{totals.pctSD}%</div>
             <div className="mt-3">
               <ProgressBar pct={totals.pctSD} colorFrom="from-emerald-500" colorTo="to-green-500" />
             </div>
             <p className="text-xs text-gray-500 mt-2">
               {totals.doneSD} of {totals.totalSD} tasks completed
             </p>
           </motion.div>
         </section>
 
         <section className="bg-[#111] border border-[#1f1f1f] p-5 rounded-xl">
           <div className="flex items-center justify-between mb-3">
             <h3 className="text-sm text-gray-300">Weekly Completion</h3>
             {lastSynced && <span className="text-xs text-gray-500">Last synced: {lastSynced}</span>}
           </div>
           <ResponsiveContainer width="100%" height={220}>
             <LineChart data={weeklyProgress}>
               <XAxis dataKey="week" stroke="#888" tick={{ fill: "#aaa", fontSize: 12 }} />
               <YAxis stroke="#888" tick={{ fill: "#aaa", fontSize: 12 }} domain={[0, 100]} />
               <Tooltip contentStyle={{ background: "#151515", border: "1px solid #2a2a2a", color: "#fff" }} />
               <Line type="monotone" dataKey="completed" stroke="#a78bfa" strokeWidth={2} dot={false} />
             </LineChart>
           </ResponsiveContainer>
         </section>
 
         <section className="space-y-5">
           {weeks.map((week) => (
             <motion.div
               key={week.number}
               initial={{ opacity: 0, y: 16 }}
               whileInView={{ opacity: 1, y: 0 }}
               viewport={{ once: true }}
               className="bg-[#111] border border-[#1f1f1f] rounded-xl p-5"
             >
               <div className="flex items-center justify-between mb-4">
                 <h2 className="text-xl font-semibold">Week {week.number}</h2>
                 <span className="text-xs text-gray-400">
                   {(() => {
                     let wTotal = 0;
                     let wDone = 0;
                     week.days.forEach((day) => {
                       day.dsa_problems.forEach((p) => {
                         wTotal += 1;
                         if (completion[makeDSAKey(p)]) wDone += 1;
                       });
                       day.system_design_tasks.forEach((_, idx) => {
                         wTotal += 1;
                         if (completion[makeSDKey(week.number, day.number, idx)]) wDone += 1;
                       });
                     });
                     const pct = wTotal ? Math.round((wDone / wTotal) * 100) : 0;
                     return `${pct}% complete`;
                   })()}
                 </span>
               </div>
 
               <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                 {week.days.map((day) => (
                   <div key={day.number} className="bg-[#0d0d0d] border border-[#1a1a1a] rounded-lg p-4">
                     <h3 className="text-lg font-medium mb-3 text-gray-200">Day {day.number}</h3>
 
                     {(activeTab === "overview" || activeTab === "dsa") && (
                       <div className="mb-4">
                         <div className="flex items-center justify-between mb-2">
                           <h4 className="text-sm uppercase tracking-wide text-orange-300">DSA Problems</h4>
                           <span className="text-xs text-gray-500">
                             {(() => {
                               const t = day.dsa_problems.length;
                               const d = day.dsa_problems.filter((p) => completion[makeDSAKey(p)]).length;
                               const pct = t ? Math.round((d / t) * 100) : 0;
                               return `${pct}%`;
                             })()}
                           </span>
                         </div>
                         <ul className="space-y-2">
                           {day.dsa_problems.map((problem) => {
                             const key = makeDSAKey(problem);
                             const checked = !!completion[key];
                             return (
                               <li key={key} className="flex items-center gap-3 text-sm">
                                 <input
                                   aria-label={`Mark DSA problem ${problem.title} as completed`}
                                   type="checkbox"
                                   className="h-5 w-5 rounded border-[#333] bg-transparent"
                                   checked={checked}
                                   onChange={() => toggleKey(key)}
                                 />
                                 <a
                                   href={problem.url}
                                   target="_blank"
                                   rel="noopener noreferrer"
                                   className={`flex-1 hover:underline ${checked ? "text-gray-400" : "text-blue-300"}`}
                                 >
                                   {problem.number}: {problem.title}
                                 </a>
                                 <span
                                   className={`px-2 py-0.5 rounded text-[10px] uppercase tracking-wider border ${
                                     problem.difficulty.toLowerCase() === "easy"
                                       ? "text-emerald-300 border-emerald-900/40 bg-emerald-500/5"
                                       : problem.difficulty.toLowerCase() === "medium"
                                       ? "text-amber-300 border-amber-900/40 bg-amber-500/5"
                                       : "text-rose-300 border-rose-900/40 bg-rose-500/5"
                                   }`}
                                 >
                                   {problem.difficulty}
                                 </span>
                               </li>
                             );
                           })}
                         </ul>
                       </div>
                     )}
 
                     {(activeTab === "overview" || activeTab === "system") && (
                       <div>
                         <div className="flex items-center justify-between mb-2">
                           <h4 className="text-sm uppercase tracking-wide text-emerald-300">System Design</h4>
                           <span className="text-xs text-gray-500">
                             {(() => {
                               const t = day.system_design_tasks.length;
                               const d = day.system_design_tasks.filter((_, idx) => completion[makeSDKey(week.number, day.number, idx)]).length;
                               const pct = t ? Math.round((d / t) * 100) : 0;
                               return `${pct}%`;
                             })()}
                           </span>
                         </div>
                         <ul className="space-y-2">
                           {day.system_design_tasks.map((task, idx) => {
                             const key = makeSDKey(week.number, day.number, idx);
                             const checked = !!completion[key];
                             return (
                               <li key={key} className="flex items-center gap-3 text-sm">
                                 <input
                                   aria-label={`Mark system design task as completed`}
                                   type="checkbox"
                                   className="h-5 w-5 rounded border-[#333] bg-transparent"
                                   checked={checked}
                                   onChange={() => toggleKey(key)}
                                 />
                                 <span className={`flex-1 ${checked ? "text-gray-400 line-through" : "text-gray-200"}`}>
                                   {task.description} {task.is_bonus ? <em className="text-violet-300">(Bonus)</em> : null}
                                 </span>
                               </li>
                             );
                           })}
                         </ul>
                       </div>
                     )}
                   </div>
                 ))}
               </div>
             </motion.div>
           ))}
         </section>
 
         <footer className="py-6 text-center text-xs text-gray-500">Designed for deep focus • Minimalist dark theme • Data from your 100-Day plan</footer>
       </main>
     </div>
   );
}
