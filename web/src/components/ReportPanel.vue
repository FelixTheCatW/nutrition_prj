<template>
  <div class="rp">

    <!-- ── ПЕРСОНАЛЬНАЯ СТАТИСТИКА ─────────────────────── -->
    <template v-if="reportName === 'personal_statistics'">
      <div class="block">
        <div class="block-title">── СВОДКА ───────────────────────────────────────────</div>
        <pre class="mono">{{ ps.summary }}</pre>
      </div>
      <div class="block">
        <div class="block-title">── ИСТОРИЯ КАЛОРИЙ (последние 60 дней) ──────────────</div>
        <div class="chart-wrap">
          <Bar :data="ps.chartData" :options="ps.chartOpts" />
        </div>
      </div>
      <div class="block">
        <div class="block-title">── ПОСЛЕДНИЕ 15 ДНЕЙ ────────────────────────────────</div>
        <pre class="mono table-pre">{{ ps.tableText }}</pre>
      </div>
    </template>

    <!-- ── АНАЛИЗ МАКРОНУТРИЕНТОВ ───────────────────────── -->
    <template v-else-if="reportName === 'macro_analysis'">
      <div class="row-2">
        <div class="block flex-1">
          <div class="block-title">── РАСПРЕДЕЛЕНИЕ КАЛОРИЙ ───────</div>
          <div class="chart-wrap chart-sm">
            <Doughnut :data="ma.chartData" :options="ma.chartOpts" />
          </div>
        </div>
        <div class="block flex-1">
          <div class="block-title">── ДЕТАЛИ ──────────────────────</div>
          <pre class="mono">{{ ma.summary }}</pre>
        </div>
      </div>
    </template>

    <!-- ── ТОП БЛЮД ПО ЧАСТОТЕ ─────────────────────────── -->
    <template v-else-if="reportName === 'top_frequent_dishes'">
      <div class="block">
        <div class="block-title">── ТОП БЛЮД ПО КОЛИЧЕСТВУ ПРИЁМОВ ──────────────────</div>
        <div class="chart-wrap">
          <Bar :data="topFreq.chartData" :options="topFreq.chartOpts" />
        </div>
      </div>
      <div class="block">
        <pre class="mono table-pre">{{ topFreq.tableText }}</pre>
      </div>
    </template>

    <!-- ── ТОП БЛЮД ПО КАЛОРИЯМ ────────────────────────── -->
    <template v-else-if="reportName === 'top_caloric_dishes'">
      <div class="block">
        <div class="block-title">── ТОП БЛЮД ПО СРЕДНЕЙ КАЛОРИЙНОСТИ ────────────────</div>
        <div class="chart-wrap">
          <Bar :data="topCal.chartData" :options="topCal.chartOpts" />
        </div>
      </div>
      <div class="block">
        <pre class="mono table-pre">{{ topCal.tableText }}</pre>
      </div>
    </template>

    <!-- ── СРАВНЕНИЕ ПОЛЬЗОВАТЕЛЕЙ ─────────────────────── -->
    <template v-else-if="reportName === 'compare_users'">
      <div class="block">
        <div class="block-title">── СРЕДНЕЕ ПОТРЕБЛЕНИЕ vs ЦЕЛЬ ──────────────────────</div>
        <div class="chart-wrap">
          <Bar :data="cu.chartData" :options="cu.chartOpts" />
        </div>
      </div>
      <div class="block">
        <pre class="mono table-pre">{{ cu.tableText }}</pre>
      </div>
    </template>

    <!-- ── АНАЛИЗ ПРИЁМОВ ПО ВРЕМЕНИ ───────────────────── -->
    <template v-else-if="reportName === 'meal_time_analysis'">
      <div class="row-2">
        <div class="block flex-1">
          <div class="block-title">── КАЛОРИЙНОСТЬ ПО ТИПУ ────────</div>
          <div class="chart-wrap chart-sm">
            <Bar :data="mta.chartData" :options="mta.chartOpts" />
          </div>
        </div>
        <div class="block flex-1">
          <div class="block-title">── СВОДКА ──────────────────────</div>
          <pre class="mono">{{ mta.summary }}</pre>
          <template v-if="data.late_count > 0">
            <div class="block-title mt">── ПОЗДНИЕ ПЕРЕКУСЫ (после 21:00) ─</div>
            <pre class="mono table-pre">{{ mta.lateText }}</pre>
          </template>
        </div>
      </div>
    </template>

    <!-- ── КАЛЕНДАРЬ ПИТАНИЯ ────────────────────────────── -->
    <template v-else-if="reportName === 'nutrition_calendar'">
      <div class="block">
        <div class="block-title">── КАЛОРИИ ПО ДНЯМ ({{ data.year }}-{{ String(data.month).padStart(2,'0') }}) ── ЦЕЛЬ: {{ data.target }} ккал ──</div>
        <div class="chart-wrap chart-tall">
          <Bar :data="nc.chartData" :options="nc.chartOpts" />
        </div>
      </div>
      <div class="block">
        <pre class="mono table-pre">{{ nc.tableText }}</pre>
      </div>
    </template>

    <!-- ── ПРОГРЕСС К ЦЕЛИ ──────────────────────────────── -->
    <template v-else-if="reportName === 'progress_to_goal'">
      <div class="block">
        <div class="block-title">── СВОДКА ───────────────────────────────────────────</div>
        <pre class="mono">{{ ptg.summary }}</pre>
      </div>
      <div class="block">
        <div class="block-title">── ПРОГНОЗИРУЕМЫЙ ВЕС (кг) ──────────────────────────</div>
        <div class="chart-wrap">
          <Line :data="ptg.chartData" :options="ptg.chartOpts" />
        </div>
      </div>
    </template>

    <!-- ── ОБЩАЯ СТАТИСТИКА ─────────────────────────────── -->
    <template v-else-if="reportName === 'overall_statistics'">
      <div class="block">
        <div class="block-title">── ОБЩАЯ СТАТИСТИКА СИСТЕМЫ ─────────────────────────</div>
        <pre class="mono">{{ os_text }}</pre>
      </div>
      <div class="block">
        <div class="block-title">── РАСПРЕДЕЛЕНИЕ ЦЕЛЕЙ ──────────────────────────────</div>
        <div class="chart-wrap chart-sm">
          <Doughnut :data="os_chart" :options="os_chartOpts" />
        </div>
      </div>
    </template>

    <!-- ── ОТЧЁТ ПО ЭФФЕКТИВНОСТИ ──────────────────────── -->
    <template v-else-if="reportName === 'efficiency_report'">
      <div class="row-2">
        <div class="block flex-1">
          <div class="block-title">── ВЫПОЛНЕНИЕ ЦЕЛИ ─────────────</div>
          <div class="chart-wrap chart-sm">
            <Doughnut :data="er.chartData" :options="er.chartOpts" />
          </div>
        </div>
        <div class="block flex-1">
          <div class="block-title">── ДЕТАЛИ ──────────────────────</div>
          <pre class="mono">{{ er.summary }}</pre>
        </div>
      </div>
    </template>

  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import {
  Chart as ChartJS,
  CategoryScale, LinearScale,
  BarElement, LineElement, PointElement, ArcElement,
  Title, Tooltip, Legend, Filler
} from 'chart.js'
import { Bar, Line, Doughnut } from 'vue-chartjs'

ChartJS.register(
  CategoryScale, LinearScale,
  BarElement, LineElement, PointElement, ArcElement,
  Title, Tooltip, Legend, Filler
)

const props = defineProps<{ reportName: string; data: any; user?: any }>()

// ── Shared chart theme ────────────────────────────────────────────────────────
const C = {
  primary:  '#d75fd7',
  active:   '#af87af',
  userBar:  '#875fd7',
  dim:      '#8b6fa8',
  white:    '#e8d8f0',
  bg:       '#0c0a12',
  panel:    '#120d1e',
  border:   '#3d1f5e',
  grid:     '#2a1040',
}

function baseOpts(indexAxis: 'x'|'y' = 'x'): any {
  return {
    indexAxis,
    responsive: true,
    maintainAspectRatio: false,
    animation: { duration: 300 },
    plugins: {
      legend: { labels: { color: C.dim, font: { family: "'Courier New', monospace", size: 11 }, boxWidth: 12 } },
      tooltip: {
        backgroundColor: C.panel, borderColor: C.border, borderWidth: 1,
        titleColor: C.active, bodyColor: C.white,
        titleFont: { family: "'Courier New', monospace", size: 11 },
        bodyFont:  { family: "'Courier New', monospace", size: 11 },
      },
    },
    scales: {
      x: {
        grid:   { color: C.grid },
        border: { color: C.border },
        ticks:  { color: C.dim, font: { family: "'Courier New', monospace", size: 10 }, maxTicksLimit: 12 },
      },
      y: {
        grid:   { color: C.grid },
        border: { color: C.border },
        ticks:  { color: C.dim, font: { family: "'Courier New', monospace", size: 10 } },
      },
    },
  }
}

function doughnutOpts(): any {
  return {
    responsive: true,
    maintainAspectRatio: false,
    animation: { duration: 300 },
    plugins: {
      legend: {
        position: 'right',
        labels: { color: C.active, font: { family: "'Courier New', monospace", size: 12 }, padding: 14 },
      },
      tooltip: {
        backgroundColor: C.panel, borderColor: C.border, borderWidth: 1,
        titleColor: C.active, bodyColor: C.white,
        titleFont: { family: "'Courier New', monospace" },
        bodyFont:  { family: "'Courier New', monospace" },
        callbacks: { label: (ctx: any) => ` ${ctx.label}: ${ctx.parsed}%` },
      },
    },
  }
}

// ── PERSONAL STATISTICS ────────────────────────────────────────────────────
const ps = computed(() => {
  const d = props.data
  const s = d.summary
  const summary = [
    `ПЕРИОД:        ${s.period_start} → ${s.period_end}  (${s.total_days} дней)`,
    `ЦЕЛЬ КАЛОРИЙ:  ${s.target_cal} ккал/день`,
    ``,
    `СРЕДНЕСУТОЧНО`,
    `  Калории:     ${s.avg_cal} ккал   (${s.pct_of_target}% от цели, отклонение ${s.deviation > 0 ? '+' : ''}${s.deviation} ккал)`,
    `  Белки:       ${s.avg_protein} г`,
    `  Жиры:        ${s.avg_fat} г`,
    `  Углеводы:    ${s.avg_carbs} г`,
  ].join('\n')

  const chartData = {
    labels:   d.chart_data.map((r: any) => r.date.slice(5)),
    datasets: [
      {
        label: 'Калории',
        data: d.chart_data.map((r: any) => r.calories),
        backgroundColor: C.primary + 'cc',
        borderColor: C.primary,
        borderWidth: 1,
        borderRadius: 2,
      },
      {
        label: 'Цель',
        data: d.chart_data.map((r: any) => r.target),
        type: 'line' as any,
        borderColor: C.active,
        borderWidth: 2,
        borderDash: [4, 3],
        pointRadius: 0,
        fill: false,
      },
    ],
  }

  const chartOpts = baseOpts()

  const hdr = 'ДАТА       │ КАЛОРИИ │ БЕЛКИ │ ЖИРЫ  │ УГЛЕВ.'
  const sep = '───────────┼─────────┼───────┼───────┼───────'
  const rows = d.table_data.map((r: any) =>
    `${r.date} │ ${String(r.calories).padStart(7)} │ ${String(r.protein).padStart(5)} │ ${String(r.fat).padStart(5)} │ ${String(r.carbs).padStart(5)}`
  )
  const tableText = [hdr, sep, ...rows].join('\n')

  return { summary, chartData, chartOpts, tableText }
})

// ── MACRO ANALYSIS ────────────────────────────────────────────────────────
const ma = computed(() => {
  const s = props.data.summary
  const summary = [
    `СРЕДНЕЕ ПОТРЕБЛЕНИЕ В ДЕНЬ:`,
    ``,
    `  Белки:      ${s.avg_protein} г → ${s.cal_from_protein} ккал   (${s.pct_protein}%)  [норма: 30%]`,
    `  Жиры:       ${s.avg_fat} г → ${s.cal_from_fat} ккал   (${s.pct_fat}%)  [норма: 20%]`,
    `  Углеводы:   ${s.avg_carbs} г → ${s.cal_from_carbs} ккал   (${s.pct_carbs}%)  [норма: 50%]`,
    ``,
    `  Всего:      ${s.total_cal} ккал/день`,
  ].join('\n')

  const pd = props.data.pie_data
  const chartData = {
    labels: pd.map((p: any) => `${p.name} (${p.value}%)`),
    datasets: [{
      data: pd.map((p: any) => p.value),
      backgroundColor: [C.primary + 'dd', C.active + 'dd', C.userBar + 'dd'],
      borderColor:     [C.primary, C.active, C.userBar],
      borderWidth: 2,
    }],
  }
  return { summary, chartData, chartOpts: doughnutOpts() }
})

// ── TOP FREQUENT DISHES ─────────────────────────────────────────────────
const topFreq = computed(() => {
  const items = props.data.items || []
  const chartData = {
    labels: items.map((r: any) => r.dish_name.length > 22 ? r.dish_name.slice(0, 22) + '…' : r.dish_name),
    datasets: [{
      label: 'Количество приёмов',
      data: items.map((r: any) => r.frequency),
      backgroundColor: C.primary + 'cc',
      borderColor: C.primary,
      borderWidth: 1,
      borderRadius: 2,
    }],
  }
  const opts = { ...baseOpts('y'), indexAxis: 'y' as any }

  const hdr = ' №  │ БЛЮДО                          │ ПРИЁМОВ'
  const sep = '────┼────────────────────────────────┼────────'
  const rows = items.map((r: any, i: number) =>
    `${String(i+1).padStart(3)} │ ${r.dish_name.padEnd(30).slice(0,30)} │ ${String(r.frequency).padStart(6)}`
  )
  return { chartData, chartOpts: opts, tableText: [hdr, sep, ...rows].join('\n') }
})

// ── TOP CALORIC DISHES ──────────────────────────────────────────────────
const topCal = computed(() => {
  const items = props.data.items || []
  const chartData = {
    labels: items.map((r: any) => r.dish_name.length > 22 ? r.dish_name.slice(0, 22) + '…' : r.dish_name),
    datasets: [{
      label: 'Ккал (ср. за приём)',
      data: items.map((r: any) => r.avg_cal_per_meal),
      backgroundColor: C.userBar + 'cc',
      borderColor: C.userBar,
      borderWidth: 1,
      borderRadius: 2,
    }],
  }
  const opts = { ...baseOpts('y'), indexAxis: 'y' as any }

  const hdr = ' №  │ БЛЮДО                          │ ККАЛ/ПРИЁМ'
  const sep = '────┼────────────────────────────────┼───────────'
  const rows = items.map((r: any, i: number) =>
    `${String(i+1).padStart(3)} │ ${r.dish_name.padEnd(30).slice(0,30)} │ ${String(r.avg_cal_per_meal).padStart(9)}`
  )
  return { chartData, chartOpts: opts, tableText: [hdr, sep, ...rows].join('\n') }
})

// ── COMPARE USERS ────────────────────────────────────────────────────────
const cu = computed(() => {
  const cd = props.data.chart_data || []
  const chartData = {
    labels: cd.map((r: any) => r.name),
    datasets: [
      {
        label: 'Среднее потребление',
        data: cd.map((r: any) => r.avg_cal),
        backgroundColor: C.primary + 'cc',
        borderColor: C.primary, borderWidth: 1, borderRadius: 2,
      },
      {
        label: 'Цель',
        data: cd.map((r: any) => r.target),
        backgroundColor: C.active + 'cc',
        borderColor: C.active, borderWidth: 1, borderRadius: 2,
      },
    ],
  }

  const users = props.data.users || []
  const hdr = 'ИМЯ              │ ИМТ  │ ЦЕЛЬ  │  СР.КАЛ │ ОТКЛ.  │  %ЦЕЛИ'
  const sep = '─────────────────┼──────┼───────┼─────────┼────────┼───────'
  const rows = users.map((u: any) => {
    const name = (u.name.split(' ').slice(0,2).join(' ')).padEnd(16).slice(0,16)
    return `${name} │ ${String(u.bmi).padStart(4)} │ ${String(u.target_cal_per_day).padStart(5)} │ ${String(u.avg_cal).padStart(7)} │ ${(u.deviation > 0 ? '+' : '') + String(u.deviation).padStart(6)} │ ${String(u.pct_of_target).padStart(5)}%`
  })
  return { chartData, chartOpts: baseOpts(), tableText: [hdr, sep, ...rows].join('\n') }
})

// ── MEAL TIME ANALYSIS ───────────────────────────────────────────────────
const mta = computed(() => {
  const ms = props.data.meal_stats || []
  const chartData = {
    labels: ms.map((r: any) => r.meal_type),
    datasets: [{
      label: 'Ср. калорийность (ккал)',
      data: ms.map((r: any) => r.avg_cal),
      backgroundColor: C.primary + 'cc',
      borderColor: C.primary, borderWidth: 1, borderRadius: 2,
    }],
  }

  const lines = ['ТИПЫ ПРИЁМОВ ПИЩИ:', '']
  ms.forEach((r: any) => lines.push(`  ${r.meal_type.padEnd(12)} — ${r.avg_cal} ккал  (${r.count} приёмов)`))
  lines.push('')
  lines.push(`ПОЗДНИЕ ПЕРЕКУСЫ (после 21:00): ${props.data.late_count}`)

  const lh = 'ДАТА       │ БЛЮДО                      │ ПОРЦ. │ ККАЛ'
  const ls = '───────────┼────────────────────────────┼───────┼──────'
  const lr = (props.data.late_snacks || []).map((r: any) =>
    `${r.date} │ ${(r.dish_name || '').padEnd(26).slice(0,26)} │ ${String(r.servings).padStart(5)} │ ${String(r.dish_calories).padStart(4)}`
  )
  return {
    chartData, chartOpts: baseOpts(),
    summary: lines.join('\n'),
    lateText: [lh, ls, ...lr].join('\n'),
  }
})

// ── NUTRITION CALENDAR ───────────────────────────────────────────────────
const nc = computed(() => {
  const daily = props.data.daily || []
  const target = props.data.target
  const statusColor = (s: string) =>
    s === 'превышение' ? C.primary : s === 'недобор' ? C.userBar : C.active

  const chartData = {
    labels: daily.map((r: any) => r.date.slice(8)),
    datasets: [{
      label: 'Калории',
      data: daily.map((r: any) => r.calories),
      backgroundColor: daily.map((r: any) => statusColor(r.status) + 'cc'),
      borderColor:     daily.map((r: any) => statusColor(r.status)),
      borderWidth: 1, borderRadius: 2,
    }, {
      label: 'Цель',
      data: daily.map(() => target),
      type: 'line' as any,
      borderColor: C.dim,
      borderWidth: 1,
      borderDash: [4, 3],
      pointRadius: 0,
      fill: false,
    }],
  }

  const hdr = 'ДАТА       │ КАЛОРИИ │ ОТКЛ.   │ СТАТУС'
  const sep = '───────────┼─────────┼─────────┼────────────'
  const rows = daily.map((r: any) =>
    `${r.date} │ ${String(r.calories).padStart(7)} │ ${((r.deviation > 0 ? '+' : '') + r.deviation).padStart(7)} │ ${r.status}`
  )
  return { chartData, chartOpts: baseOpts(), tableText: [hdr, sep, ...rows].join('\n') }
})

// ── PROGRESS TO GOAL ─────────────────────────────────────────────────────
const ptg = computed(() => {
  const s = props.data.summary
  const summary = [
    `НАЧАЛЬНЫЙ ВЕС:        ${s.initial_weight} кг`,
    `TDEE (норма расхода): ${s.tdee} ккал/день`,
    `ЦЕЛЕВОЕ ПОТРЕБЛЕНИЕ:  ${s.target_cal} ккал/день`,
    `СРЕДНЕЕ ФАКТИЧЕСКОЕ:  ${s.avg_actual_cal} ккал/день`,
    ``,
    `ИТОГОВЫЙ ДЕФИЦИТ:     ${s.total_deficit > 0 ? '+' : ''}${s.total_deficit} ккал`,
    `ИЗМЕНЕНИЕ ВЕСА:       ${s.weight_change > 0 ? '+' : ''}${s.weight_change} кг`,
    `ПРОГНОЗИРУЕМЫЙ ВЕС:   ${s.predicted_weight} кг`,
  ].join('\n')

  const cd = props.data.chart_data || []
  const chartData = {
    labels: cd.map((r: any) => r.date.slice(5)),
    datasets: [{
      label: 'Прогноз веса (кг)',
      data: cd.map((r: any) => r.predicted_weight),
      borderColor: C.primary,
      backgroundColor: C.primary + '22',
      borderWidth: 2,
      pointRadius: 0,
      fill: true,
      tension: 0.3,
    }],
  }
  const opts = { ...baseOpts(), plugins: { ...baseOpts().plugins, legend: { labels: { color: C.dim } } } }
  return { summary, chartData, chartOpts: opts }
})

// ── OVERALL STATISTICS ───────────────────────────────────────────────────
const os_text = computed(() => {
  const s = props.data.stats
  const goals = props.data.goals || []
  const lines = [
    `ПЕРИОД ДАННЫХ:          ${s.min_date} → ${s.max_date}`,
    `ВСЕГО ПОЛЬЗОВАТЕЛЕЙ:    ${s.total_users}`,
    `ВСЕГО ПРИЁМОВ ПИЩИ:     ${s.total_meals}`,
    `УНИКАЛЬНЫХ БЛЮД:        ${s.total_dishes}`,
    `СР. КАЛОРИЙ/ПРИЁМ:      ${s.avg_cal_per_meal} ккал`,
    ``,
    `РАСПРЕДЕЛЕНИЕ ЦЕЛЕЙ:`,
    ...goals.map((g: any) => `  ${(g.goal || '—').padEnd(20)} — ${g.cnt} чел.`),
  ]
  return lines.join('\n')
})
const os_chart = computed(() => {
  const goals = props.data.goals || []
  return {
    labels: goals.map((g: any) => g.goal || '—'),
    datasets: [{
      data: goals.map((g: any) => g.cnt),
      backgroundColor: [C.primary + 'cc', C.active + 'cc', C.userBar + 'cc', '#5f5faf' + 'cc', '#af5f5f' + 'cc'],
      borderColor:     [C.primary, C.active, C.userBar, '#5f5faf', '#af5f5f'],
      borderWidth: 2,
    }],
  }
})
const os_chartOpts = computed(() => ({
  ...doughnutOpts(),
  plugins: { ...doughnutOpts().plugins, legend: { ...doughnutOpts().plugins.legend, labels: { ...doughnutOpts().plugins.legend.labels, color: C.active } } },
}))

// ── EFFICIENCY REPORT ────────────────────────────────────────────────────
const er = computed(() => {
  const s = props.data.summary
  const summary = [
    `ЦЕЛЬ:                  ${s.target} ккал/день`,
    `ВСЕГО ДНЕЙ С ДАННЫМИ:  ${s.total_days}`,
    ``,
    `В НОРМЕ (±10%):        ${s.within_10pct} дней  (${s.pct_within}%)`,
    `ПРЕВЫШЕНИЕ (>110%):    ${s.over_days} дней`,
    `НЕДОБОР (<90%):        ${s.under_days} дней`,
    `МАЛО ПРИЁМОВ (<3):     ${s.low_meal_days} дней`,
  ].join('\n')

  const bd = props.data.breakdown || []
  const chartData = {
    labels: bd.map((b: any) => `${b.label} (${b.value})`),
    datasets: [{
      data: bd.map((b: any) => b.value),
      backgroundColor: bd.map((b: any) => b.color + 'dd'),
      borderColor:     bd.map((b: any) => b.color),
      borderWidth: 2,
    }],
  }
  return { summary, chartData, chartOpts: doughnutOpts() }
})
</script>

<style scoped>
.rp { display: flex; flex-direction: column; gap: 10px; font-size: 13px; }

.block {
  border: 1px solid #3d1f5e;
  background: #120d1e;
  padding: 8px 12px;
}

.block-title {
  color: #8b6fa8;
  font-size: 11px;
  margin-bottom: 6px;
  letter-spacing: 0.05em;
}

.mono {
  color: #e8d8f0;
  font-family: 'Courier New', Consolas, monospace;
  font-size: 12px;
  line-height: 1.65;
  white-space: pre;
  margin: 0;
}

.table-pre {
  overflow-x: auto;
  color: #d75fd7;
  scrollbar-width: thin;
  scrollbar-color: #3d1f5e #0c0a12;
}

.chart-wrap {
  height: 220px;
  width: 100%;
}
.chart-sm   { height: 200px; }
.chart-tall { height: 240px; }

.row-2 {
  display: flex;
  gap: 10px;
}
.flex-1 { flex: 1; min-width: 0; }

.mt { margin-top: 10px; }

/* ──────────────────────────────────────────────────────────
   RESPONSIVE / MOBILE STYLES
   ────────────────────────────────────────────────────────── */
@media (max-width: 768px) {
  .rp {
    font-size: 12px;
    gap: 8px;
  }

  .block {
    padding: 6px 10px;
  }

  .block-title {
    font-size: 10px;
    margin-bottom: 4px;
  }

  .mono {
    font-size: 11px;
    line-height: 1.5;
  }

  .chart-wrap {
    height: 180px;
  }

  .chart-sm {
    height: 160px;
  }

  .chart-tall {
    height: 200px;
  }

  /* Stack row-2 vertically on mobile */
  .row-2 {
    flex-direction: column;
    gap: 8px;
  }

  .flex-1 {
    width: 100%;
  }

  .mt {
    margin-top: 8px;
  }
}

@media (max-width: 480px) {
  .rp {
    font-size: 11px;
    gap: 6px;
  }

  .block {
    padding: 5px 8px;
  }

  .block-title {
    font-size: 9px;
  }

  .mono {
    font-size: 10px;
    line-height: 1.4;
  }

  .chart-wrap {
    height: 150px;
  }

  .chart-sm {
    height: 140px;
  }

  .chart-tall {
    height: 170px;
  }
}
/* ──────────────────────────────────────────────────────────
   RESPONSIVE / MOBILE STYLES
   ────────────────────────────────────────────────────────── */
@media (max-width: 768px) {
  .rp {
    font-size: 12px;
    gap: 8px;
  }

  .block {
    padding: 6px 10px;
  }

  .block-title {
    font-size: 10px;
    margin-bottom: 4px;
  }

  .mono {
    font-size: 11px;
    line-height: 1.5;
  }

  .chart-wrap {
    height: 180px;
  }

  .chart-sm {
    height: 160px;
  }

  .chart-tall {
    height: 200px;
  }

  /* Stack row-2 vertically on mobile */
  .row-2 {
    flex-direction: column;
    gap: 8px;
  }

  .flex-1 {
    width: 100%;
  }

  .mt {
    margin-top: 8px;
  }
}

@media (max-width: 480px) {
  .rp {
    font-size: 14px;
    gap: 6px;
  }

  .block {
    padding: 5px 8px;
  }

  .block-title {
    font-size: 14px;
  }

  .mono {
    font-size: 14px;
    line-height: 1.4;
  }

  .chart-wrap {
    height: 150px;
  }

  .chart-sm {
    height: 140px;
  }

  .chart-tall {
    height: 170px;
  }
}
</style>
