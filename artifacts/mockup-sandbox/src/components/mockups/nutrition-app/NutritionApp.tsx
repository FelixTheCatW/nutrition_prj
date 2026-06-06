import React, { useState } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine
} from 'recharts';

const MENU_ITEMS = [
  { id: 1, key: '1', title: 'Personal Statistics' },
  { id: 2, key: '2', title: 'Macro Analysis' },
  { id: 3, key: '3', title: 'Top Frequent Dishes' },
  { id: 4, key: '4', title: 'Top Caloric Dishes' },
  { id: 5, key: '5', title: 'Compare Users' },
  { id: 6, key: '6', title: 'Meal Time Analysis' },
  { id: 7, key: '7', title: 'Nutrition Calendar' },
  { id: 8, key: '8', title: 'Progress to Goal' },
  { id: 9, key: '9', title: 'Overall Statistics' },
  { id: 10, key: '0', title: 'Efficiency Report' },
];

const CHART_DATA = [
  { date: '06-01', calories: 2150, protein: 140, fat: 65, carbs: 250 },
  { date: '06-02', calories: 1980, protein: 135, fat: 55, carbs: 230 },
  { date: '06-03', calories: 2400, protein: 160, fat: 80, carbs: 260 },
  { date: '06-04', calories: 2100, protein: 145, fat: 60, carbs: 245 },
  { date: '06-05', calories: 2250, protein: 150, fat: 70, carbs: 255 },
  { date: '06-06', calories: 2050, protein: 130, fat: 58, carbs: 250 },
  { date: '06-07', calories: 2300, protein: 155, fat: 75, carbs: 250 },
];

export function NutritionApp() {
  const [activeId, setActiveId] = useState(1);

  return (
    <div
      className="flex flex-col w-screen h-screen font-mono overflow-hidden select-none"
      style={{
        backgroundColor: '#0a0a0f',
        color: '#22c55e',
        fontFamily: "'Courier New', 'Fira Code', 'JetBrains Mono', Consolas, monospace",
      }}
    >
      <style dangerouslySetInnerHTML={{__html: `
        ::-webkit-scrollbar {
          width: 12px;
          background: #0a0a0f;
          border-left: 1px solid #1e3a1e;
        }
        ::-webkit-scrollbar-thumb {
          background: #1e3a1e;
        }
        ::-webkit-scrollbar-thumb:hover {
          background: #22c55e;
        }
      `}} />

      {/* TOP BAR */}
      <div
        className="flex justify-between items-center px-4 py-1 shrink-0"
        style={{ backgroundColor: '#052e16', borderBottom: '1px solid #1e3a1e' }}
      >
        <div>NUTRITION TRACKER v1.0 | USER: Евфросиния Геннадиевна Носкова | 2025-06-06</div>
        <div className="flex gap-4">
          <span>[F1] Help</span>
          <span>[F2] Reports</span>
          <span>[F10] Quit</span>
        </div>
      </div>

      {/* SPLIT */}
      <div className="flex flex-1 overflow-hidden">
        {/* LEFT PANEL */}
        <div
          className="w-1/4 flex flex-col shrink-0"
          style={{ backgroundColor: '#0d1117', borderRight: '1px solid #1e3a1e' }}
        >
          <div className="p-4 uppercase font-bold border-b" style={{ borderColor: '#1e3a1e', color: '#bbf7d0' }}>
            Available Reports
          </div>
          <div className="flex-1 overflow-y-auto py-2">
            {MENU_ITEMS.map((item) => {
              const isActive = item.id === activeId;
              return (
                <div
                  key={item.id}
                  onClick={() => setActiveId(item.id)}
                  className="px-4 py-2 flex items-center cursor-pointer transition-colors duration-0"
                  style={{
                    backgroundColor: isActive ? '#1a2e1a' : 'transparent',
                    color: isActive ? '#fbbf24' : '#22c55e'
                  }}
                  onMouseEnter={(e) => {
                    if (!isActive) e.currentTarget.style.backgroundColor = '#1a2e1a';
                  }}
                  onMouseLeave={(e) => {
                    if (!isActive) e.currentTarget.style.backgroundColor = 'transparent';
                  }}
                >
                  <span className="w-6 shrink-0">{isActive ? '►' : ' '}</span>
                  <span className="w-8 shrink-0">[{item.key}]</span>
                  <span className="truncate">{item.title}</span>
                </div>
              );
            })}
          </div>
        </div>

        {/* RIGHT PANEL */}
        <div className="w-3/4 flex flex-col flex-1" style={{ backgroundColor: '#111827' }}>
          {/* DESCRIPTION PANEL */}
          <div
            className="p-4 shrink-0"
            style={{
              backgroundColor: '#0d1117',
              borderBottom: '1px solid #1e3a1e',
              minHeight: '80px'
            }}
          >
            <div style={{ color: '#4ade80' }} className="italic whitespace-pre-wrap">
              {activeId === 1
                ? "Displays your personal nutrition summary including daily averages, macronutrient breakdown, and calorie history vs. targets over the selected period."
                : "Description not available for this report."}
            </div>
          </div>

          {/* BODY / REPORT CONTENT */}
          <div className="p-6 flex-1 overflow-y-auto flex flex-col gap-6">
            {/* SUMMARY STATS */}
            <div className="border border-dashed p-4" style={{ borderColor: '#1e3a1e', backgroundColor: '#0a0a0f' }}>
              <pre className="m-0 leading-relaxed" style={{ color: '#bbf7d0' }}>
{`REPORT:     Personal Statistics
PERIOD:     2025-06-01 to 2025-06-07 (7 days)
TARGET:     2200 kcal/day

DAILY AVERAGES
--------------
Calories:   2175 kcal (Target Dev: -1.1%)
Protein:    145g
Fat:        66g
Carbs:      248g`}
              </pre>
            </div>

            {/* CHART */}
            <div className="border p-4 flex flex-col gap-2" style={{ borderColor: '#1e3a1e', backgroundColor: '#0a0a0f' }}>
              <div className="text-center font-bold" style={{ color: '#4ade80' }}>-- 7-DAY CALORIE HISTORY --</div>
              <div className="h-64 w-full mt-4">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={CHART_DATA} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1e3a1e" vertical={false} />
                    <XAxis dataKey="date" stroke="#22c55e" tick={{ fill: '#22c55e', fontSize: 12, fontFamily: 'monospace' }} axisLine={{ stroke: '#1e3a1e' }} tickLine={false} />
                    <YAxis stroke="#22c55e" tick={{ fill: '#22c55e', fontSize: 12, fontFamily: 'monospace' }} axisLine={{ stroke: '#1e3a1e' }} tickLine={false} />
                    <Tooltip
                      cursor={{ fill: '#1a2e1a' }}
                      contentStyle={{ backgroundColor: '#0d1117', border: '1px solid #1e3a1e', color: '#bbf7d0', fontFamily: 'monospace' }}
                      itemStyle={{ color: '#22c55e' }}
                    />
                    <ReferenceLine y={2200} stroke="#fbbf24" strokeDasharray="3 3" label={{ position: 'top', value: 'TARGET', fill: '#fbbf24', fontSize: 10, fontFamily: 'monospace' }} />
                    <Bar dataKey="calories" fill="#22c55e" radius={[2, 2, 0, 0]} maxBarSize={50} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* DATA TABLE */}
            <div>
              <pre className="w-full whitespace-pre font-mono text-sm leading-tight border p-4" style={{ borderColor: '#1e3a1e', backgroundColor: '#0a0a0f', color: '#22c55e' }}>
{`DATE       | CALORIES | PROTEIN | FAT  | CARBS
-----------+----------+---------+------+------
2025-06-01 |     2150 |     140 |   65 |   250
2025-06-02 |     1980 |     135 |   55 |   230
2025-06-03 |     2400 |     160 |   80 |   260
2025-06-04 |     2100 |     145 |   60 |   245
2025-06-05 |     2250 |     150 |   70 |   255
2025-06-06 |     2050 |     130 |   58 |   250
2025-06-07 |     2300 |     155 |   75 |   250
-----------+----------+---------+------+------
AVERAGE    |     2175 |     145 |   66 |   248`}
              </pre>
            </div>
          </div>
        </div>
      </div>

      {/* BOTTOM BAR */}
      <div
        className="px-4 py-1 shrink-0 flex justify-center gap-6"
        style={{ backgroundColor: '#052e16', borderTop: '1px solid #1e3a1e' }}
      >
        <span>[↑↓] Navigate</span>
        <span>[Enter] Run Report</span>
        <span>[R] Refresh</span>
        <span>[Q] Quit</span>
        <span>[Tab] Next User</span>
      </div>
    </div>
  );
}
