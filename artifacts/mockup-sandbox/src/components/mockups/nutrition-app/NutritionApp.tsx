import React, { useState, useEffect, useRef } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, ReferenceLine
} from 'recharts';

// ── Xterm-256 colors extracted from CLI source ─────────────────────────────
// curses.init_pair(N, N-1, -1)  → pair 171 = color 170, pair 140 = color 139, pair 99 = color 98
// Color 170 → #d75fd7 (orchid / bright purple)  — headers, borders, window bg
// Color 139 → #af87af (muted mauve / lilac)      — active/highlighted menu item
// Color 98  → #875fd7 (blue-violet)              — user info bar

const C = {
  bg:          '#0c0a12',   // near-black with purple tint
  panelBg:     '#120d1e',   // slightly lighter panel
  border:      '#3d1f5e',   // dark purple border
  primary:     '#d75fd7',   // pair 171 — orchid
  active:      '#af87af',   // pair 140 — muted mauve (active menu item)
  userBar:     '#875fd7',   // pair 98  — blue-violet (user bar)
  dim:         '#8b6fa8',   // dim text
  white:       '#e8d8f0',   // near-white with purple tint
  activeBg:    '#2a1040',   // active menu item bg
  hoverBg:     '#1e0d30',   // hover bg
  headerBg:    '#1a0b2e',   // header/footer bar bg
  chartBar:    '#d75fd7',   // chart bar color
  chartRef:    '#af87af',   // reference line
  chartGrid:   '#2a1040',   // chart grid
};

const MENU_ITEMS = [
  { id: 1,  key: '1', title: 'Персональная статистика',   desc: 'Суммарное потребление калорий и БЖУ, сравнение с целью, динамика по дням.' },
  { id: 2,  key: '2', title: 'Анализ макронутриентов',    desc: 'Соотношение белков, жиров, углеводов в процентах от калорий, сравнение с нормой.' },
  { id: 3,  key: '3', title: 'Топ блюд по частоте',       desc: 'Список блюд, которые пользователь заказывает чаще всего (по количеству приемов).' },
  { id: 4,  key: '4', title: 'Топ блюд по калориям',      desc: 'Самые калорийные блюда в рационе (средняя калорийность за прием).' },
  { id: 5,  key: '5', title: 'Сравнение пользователей',   desc: 'Сводная таблица по всем пользователям: ИМТ, активность, среднее отклонение от нормы.' },
  { id: 6,  key: '6', title: 'Анализ приемов по времени', desc: 'Средняя калорийность завтрака, обеда, ужина, перекусов; поздние приемы пищи.' },
  { id: 7,  key: '7', title: 'Календарь питания',         desc: 'Тепловая карта калорий по дням месяца, выделение дней с сильным превышением.' },
  { id: 8,  key: '8', title: 'Прогресс к цели',           desc: 'Прогноз изменения веса на основе дефицита/профицита калорий.' },
  { id: 9,  key: '9', title: 'Общая статистика',          desc: 'Количество приемов, общее потребление по всем пользователям, распределение целей.' },
  { id: 10, key: '0', title: 'Отчет по эффективности',    desc: 'Процент дней, когда калорийность в пределах ±10% от цели, пропуски приемов.' },
];

const USERS = [
  'Евфросиния Геннадиевна Носкова',
  'Смирнова Раиса Валериевна',
  'Титов Святослав Иосипович',
  'Самсон Аксёнович Евсеев',
  'Маслова Вера Богдановна',
  'Вера Даниловна Михайлова',
  'Ювеналий Елизарович Игнатьев',
  'Куликов Кирилл Абрамович',
  'Кирилл Филатович Козлов',
  'Наина Вадимовна Устинова',
];

const CHART_DATA = [
  { date: '06-01', calories: 2150 },
  { date: '06-02', calories: 1980 },
  { date: '06-03', calories: 2400 },
  { date: '06-04', calories: 2100 },
  { date: '06-05', calories: 2250 },
  { date: '06-06', calories: 2050 },
  { date: '06-07', calories: 2300 },
];

// ── User Selection Modal ───────────────────────────────────────────────────
function UserModal({ currentUser, onSelect, onClose }: {
  currentUser: string;
  onSelect: (u: string) => void;
  onClose: () => void;
}) {
  const [cursor, setCursor] = useState(USERS.indexOf(currentUser));
  const listRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = listRef.current?.children[cursor] as HTMLElement;
    el?.scrollIntoView({ block: 'nearest' });
  }, [cursor]);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'ArrowUp')   { e.preventDefault(); setCursor(c => Math.max(0, c - 1)); }
      if (e.key === 'ArrowDown') { e.preventDefault(); setCursor(c => Math.min(USERS.length - 1, c + 1)); }
      if (e.key === 'Enter')     { onSelect(USERS[cursor]); }
      if (e.key === 'Escape')    { onClose(); }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [cursor, onSelect, onClose]);

  return (
    <div
      className="fixed inset-0 flex items-center justify-center z-50"
      style={{ backgroundColor: 'rgba(12,10,18,0.85)' }}
      onClick={onClose}
    >
      <div
        className="flex flex-col"
        style={{
          backgroundColor: C.panelBg,
          border: `2px solid ${C.primary}`,
          minWidth: 420,
          maxWidth: 520,
          fontFamily: "'Courier New', Consolas, monospace",
          boxShadow: `0 0 40px ${C.primary}55`,
        }}
        onClick={e => e.stopPropagation()}
      >
        {/* Modal title bar */}
        <div
          className="px-4 py-2 text-center font-bold tracking-widest"
          style={{ backgroundColor: C.primary, color: C.bg, fontSize: 13 }}
        >
          ╔══ ВЫБЕРИТЕ ПОЛЬЗОВАТЕЛЯ ══╗
        </div>

        {/* User list */}
        <div
          ref={listRef}
          className="overflow-y-auto"
          style={{ maxHeight: 320, backgroundColor: C.panelBg }}
        >
          {USERS.map((u, i) => (
            <div
              key={u}
              onClick={() => onSelect(u)}
              onMouseEnter={() => setCursor(i)}
              className="px-6 py-2 cursor-pointer"
              style={{
                backgroundColor: i === cursor ? C.primary : 'transparent',
                color:           i === cursor ? C.bg      : C.primary,
                fontSize: 13,
              }}
            >
              {i === cursor ? `  ★ ${u}  ` : `     ${u}`}
            </div>
          ))}
        </div>

        {/* Footer */}
        <div
          className="px-4 py-1 text-center"
          style={{ backgroundColor: C.headerBg, color: C.dim, fontSize: 11, borderTop: `1px solid ${C.border}` }}
        >
          [↑↓] навигация  [Enter] выбрать  [Esc] отмена
        </div>
      </div>
    </div>
  );
}

// ── Main App ───────────────────────────────────────────────────────────────
export function NutritionApp() {
  const [activeId, setActiveId]       = useState(1);
  const [user, setUser]               = useState(USERS[0]);
  const [showModal, setShowModal]     = useState(false);

  const activeItem = MENU_ITEMS.find(m => m.id === activeId)!;

  // Global keyboard handler
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (showModal) return;
      const tag = (e.target as HTMLElement)?.tagName;
      if (tag === 'INPUT' || tag === 'TEXTAREA') return;

      if (e.key === 'ArrowUp')   setActiveId(id => Math.max(1,  id - 1));
      if (e.key === 'ArrowDown') setActiveId(id => Math.min(10, id + 1));
      if (e.key === 'u' || e.key === 'U') setShowModal(true);
      if (e.key === 'q' || e.key === 'Q') { /* quit — noop in browser */ }
      const num = parseInt(e.key);
      if (!isNaN(num)) setActiveId(num === 0 ? 10 : num);
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [showModal]);

  return (
    <div
      className="flex flex-col w-screen h-screen overflow-hidden select-none"
      style={{
        backgroundColor: C.bg,
        color: C.primary,
        fontFamily: "'Courier New', 'Fira Code', Consolas, monospace",
        fontSize: 13,
      }}
    >
      <style dangerouslySetInnerHTML={{__html: `
        * { box-sizing: border-box; }
        ::-webkit-scrollbar { width: 8px; background: ${C.bg}; }
        ::-webkit-scrollbar-thumb { background: ${C.border}; }
        ::-webkit-scrollbar-thumb:hover { background: ${C.primary}; }
      `}} />

      {/* ── TOP BAR ─────────────────────────────────────────────────── */}
      <div
        className="flex items-center justify-between px-3 py-1 shrink-0"
        style={{ backgroundColor: C.headerBg, borderBottom: `1px solid ${C.border}`, minHeight: 28 }}
      >
        <span style={{ color: C.primary, letterSpacing: '0.04em' }}>
          NUTRITION TRACKER v1.0
        </span>
        <span style={{ color: C.white }}>
          Клиент:{' '}
          <span style={{ color: C.userBar, fontWeight: 'bold' }}>{user}</span>
          {'  '}| 2025-06-06
        </span>
        <span style={{ color: C.dim }}>
          [U] Выбор пользователя  [Q] Выход
        </span>
      </div>

      {/* ── SPLIT AREA ──────────────────────────────────────────────── */}
      <div className="flex flex-1 overflow-hidden">

        {/* LEFT PANEL — menu ─────────────────────────────────────── */}
        <div
          className="flex flex-col shrink-0"
          style={{ width: 240, backgroundColor: C.panelBg, borderRight: `1px solid ${C.border}` }}
        >
          {/* Panel header */}
          <div
            className="px-3 py-1 text-center font-bold tracking-wider shrink-0"
            style={{ backgroundColor: C.primary, color: C.bg, fontSize: 12 }}
          >
            ═══ Доступные отчеты ═══
          </div>

          {/* Menu list */}
          <div className="flex-1 overflow-y-auto py-1">
            {MENU_ITEMS.map(item => {
              const isActive = item.id === activeId;
              return (
                <div
                  key={item.id}
                  onClick={() => setActiveId(item.id)}
                  className="flex items-center px-2 py-1 cursor-pointer"
                  style={{
                    backgroundColor: isActive ? C.activeBg : 'transparent',
                    color: isActive ? C.active : C.primary,
                    borderLeft: isActive ? `3px solid ${C.active}` : '3px solid transparent',
                    transition: 'none',
                  }}
                  onMouseEnter={e => { if (!isActive) e.currentTarget.style.backgroundColor = C.hoverBg; }}
                  onMouseLeave={e => { if (!isActive) e.currentTarget.style.backgroundColor = 'transparent'; }}
                >
                  <span style={{ width: 14, color: C.active }}>{isActive ? '►' : ' '}</span>
                  <span style={{ width: 22, color: C.dim, flexShrink: 0 }}>[{item.key}]</span>
                  <span style={{ fontSize: 12 }}>{item.title}</span>
                </div>
              );
            })}
          </div>
        </div>

        {/* RIGHT PANEL ──────────────────────────────────────────── */}
        <div className="flex flex-col flex-1 overflow-hidden" style={{ backgroundColor: C.bg }}>

          {/* Description bar */}
          <div
            className="px-4 py-2 shrink-0"
            style={{
              backgroundColor: C.panelBg,
              borderBottom: `1px solid ${C.border}`,
              minHeight: 62,
            }}
          >
            <div style={{ color: C.dim, fontSize: 11, marginBottom: 2 }}>
              ═══ Описание ═══════════════════════════════════════════════
            </div>
            <div style={{ color: C.white, fontStyle: 'italic', fontSize: 13 }}>
              {activeItem.desc}
            </div>
          </div>

          {/* Report body */}
          <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-4">

            {/* Stats block */}
            <div
              className="p-3"
              style={{ border: `1px solid ${C.border}`, backgroundColor: C.panelBg }}
            >
              <div style={{ color: C.active, marginBottom: 6, fontSize: 11 }}>
                ┌── ПЕРСОНАЛЬНАЯ СТАТИСТИКА ─────────────────────────────────────┐
              </div>
              <pre style={{ margin: 0, lineHeight: 1.7, color: C.white, fontSize: 13 }}>{`ПЕРИОД:           2025-06-01 → 2025-06-07 (7 дней)
ЦЕЛЬ КАЛОРИЙ:     2 200 ккал/день

СРЕДНЕСУТОЧНО
  Калории:        2 175 ккал   (отклонение: −25 ккал / −1.1%)
  Белки:          145 г
  Жиры:            66 г
  Углеводы:       248 г`}</pre>
              <div style={{ color: C.active, marginTop: 6, fontSize: 11 }}>
                └────────────────────────────────────────────────────────────────┘
              </div>
            </div>

            {/* Chart */}
            <div
              className="p-3"
              style={{ border: `1px solid ${C.border}`, backgroundColor: C.panelBg }}
            >
              <div
                className="text-center mb-3"
                style={{ color: C.active, fontSize: 11, letterSpacing: '0.1em' }}
              >
                ─────────── ИСТОРИЯ КАЛОРИЙ (7 ДНЕЙ) ───────────
              </div>
              <div style={{ height: 200 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={CHART_DATA} margin={{ top: 8, right: 8, left: -10, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="2 4" stroke={C.chartGrid} vertical={false} />
                    <XAxis
                      dataKey="date"
                      stroke={C.border}
                      tick={{ fill: C.dim, fontSize: 11, fontFamily: 'monospace' }}
                      axisLine={{ stroke: C.border }}
                      tickLine={false}
                    />
                    <YAxis
                      stroke={C.border}
                      tick={{ fill: C.dim, fontSize: 11, fontFamily: 'monospace' }}
                      axisLine={{ stroke: C.border }}
                      tickLine={false}
                      domain={[1600, 2600]}
                    />
                    <Tooltip
                      cursor={{ fill: C.hoverBg }}
                      contentStyle={{
                        backgroundColor: C.panelBg,
                        border: `1px solid ${C.border}`,
                        color: C.white,
                        fontFamily: 'monospace',
                        fontSize: 12,
                      }}
                      itemStyle={{ color: C.primary }}
                      labelStyle={{ color: C.active }}
                    />
                    <ReferenceLine
                      y={2200}
                      stroke={C.chartRef}
                      strokeDasharray="4 3"
                      label={{ position: 'right', value: 'ЦЕЛЬ', fill: C.chartRef, fontSize: 10, fontFamily: 'monospace' }}
                    />
                    <Bar dataKey="calories" fill={C.chartBar} radius={[2, 2, 0, 0]} maxBarSize={42} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Data table */}
            <div style={{ border: `1px solid ${C.border}`, backgroundColor: C.panelBg }}>
              <pre
                style={{
                  margin: 0, padding: '10px 12px',
                  fontSize: 12, lineHeight: 1.6,
                  color: C.primary,
                  fontFamily: "'Courier New', Consolas, monospace",
                }}
              >{`ДАТА       │ КАЛОРИИ │ БЕЛКИ │ ЖИРЫ │ УГЛЕВ.
───────────┼─────────┼───────┼──────┼───────
2025-06-01 │   2 150 │   140 │   65 │   250
2025-06-02 │   1 980 │   135 │   55 │   230
2025-06-03 │   2 400 │   160 │   80 │   260
2025-06-04 │   2 100 │   145 │   60 │   245
2025-06-05 │   2 250 │   150 │   70 │   255
2025-06-06 │   2 050 │   130 │   58 │   250
2025-06-07 │   2 300 │   155 │   75 │   250
───────────┼─────────┼───────┼──────┼───────`}
                <span style={{ color: C.active }}>{`
СРЕДНЕЕ    │   2 175 │   145 │   66 │   248`}</span>
              </pre>
            </div>

          </div>
        </div>
      </div>

      {/* ── BOTTOM BAR ──────────────────────────────────────────────── */}
      <div
        className="flex items-center justify-center gap-6 px-4 py-1 shrink-0"
        style={{
          backgroundColor: C.headerBg,
          borderTop: `1px solid ${C.border}`,
          color: C.primary,
          fontSize: 12,
          minHeight: 26,
        }}
      >
        <span style={{ color: C.dim }}>[↑↓]</span> Навигация
        <span style={{ color: C.dim }}> │ </span>
        <span style={{ color: C.dim }}>[Enter]</span> Запустить отчет
        <span style={{ color: C.dim }}> │ </span>
        <span style={{ color: C.dim }}>[U]</span> <span style={{ color: C.userBar }}>Выбор пользователя</span>
        <span style={{ color: C.dim }}> │ </span>
        <span style={{ color: C.dim }}>[1–0]</span> Быстрый переход
        <span style={{ color: C.dim }}> │ </span>
        <span style={{ color: C.dim }}>[Q]</span> Выход
      </div>

      {/* ── USER MODAL ──────────────────────────────────────────────── */}
      {showModal && (
        <UserModal
          currentUser={user}
          onSelect={u => { setUser(u); setShowModal(false); }}
          onClose={() => setShowModal(false)}
        />
      )}
    </div>
  );
}
