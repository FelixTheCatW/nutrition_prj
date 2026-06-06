<template>
  <div class="app" tabindex="0">

    <!-- ── TOP BAR ───────────────────────────────────── -->
    <div class="topbar">
      <span class="brand">NUTRITION TRACKER v1.0</span>
      <span class="user-info">
        Клиент:&nbsp;
        <span class="user-name">{{ currentUser ? currentUser.name : '—' }}</span>
        <template v-if="currentUser">
          &nbsp;·&nbsp;{{ currentUser.city }}&nbsp;·&nbsp;{{ currentUser.gender[0].toUpperCase() }}&nbsp;·&nbsp;{{ currentUser.age }} лет
        </template>
        &nbsp;|&nbsp;{{ today }}
      </span>
      <span class="topbar-keys">[U] Пользователь &nbsp; [Q] Выход</span>
    </div>

    <!-- ── MAIN SPLIT ─────────────────────────────────── -->
    <div class="split">

      <!-- LEFT MENU -->
      <div class="menu-panel">
        <div class="panel-hdr">═══ Доступные отчеты ═══</div>
        <div class="menu-list">
          <div
            v-for="item in MENU_ITEMS"
            :key="item.id"
            class="menu-item"
            :class="{ active: activeId === item.id }"
            @click="selectItem(item.id)"
          >
            <span class="cur">{{ activeId === item.id ? '►' : '\u00a0' }}</span>
            <span class="hk">[{{ item.key }}]</span>
            <span class="ti">{{ item.title }}</span>
          </div>
        </div>
      </div>

      <!-- RIGHT PANEL -->
      <div class="right-panel">

        <!-- Description bar -->
        <div class="desc-bar">
          <div class="desc-lbl">═══ Описание ════════════════════════════════════════════</div>
          <div class="desc-txt">{{ activeItem.desc }}</div>
        </div>

        <!-- Report body -->
        <div class="report-body">
          <div v-if="loading" class="status">⣾ Загрузка данных…</div>
          <div v-else-if="error" class="status err">✖ {{ error }}</div>
          <div v-else-if="!reportData" class="status hint">
            Нажмите [Enter] для запуска отчёта или кликните на пункт меню
          </div>
          <ReportPanel
            v-else
            :reportName="activeName"
            :data="reportData"
            :user="currentUser"
          />
        </div>

      </div>
    </div>

    <!-- ── BOTTOM BAR ─────────────────────────────────── -->
    <div class="bottombar">
      <span><span class="k">[↑↓]</span>&nbsp;Навигация</span>
      <span class="sep">│</span>
      <span><span class="k">[Enter]</span>&nbsp;Запустить</span>
      <span class="sep">│</span>
      <span><span class="k">[U]</span>&nbsp;<span class="ku">Пользователь</span></span>
      <span class="sep">│</span>
      <span><span class="k">[1–0]</span>&nbsp;Быстрый переход</span>
      <span class="sep">│</span>
      <span class="dim">API:&nbsp;<span :class="apiOk ? 'ok' : 'err'">{{ apiOk ? '● online' : '○ offline' }}</span></span>
    </div>

    <!-- ── USER MODAL ─────────────────────────────────── -->
    <UserModal
      v-if="showModal"
      :users="users"
      :currentId="currentUser?.id"
      @select="onSelectUser"
      @close="showModal = false"
    />

  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import ReportPanel from './components/ReportPanel.vue'
import UserModal   from './components/UserModal.vue'
import { getUsers, getReport, type User } from './api'

const MENU_ITEMS = [
  { id: 1,  key: '1', name: 'personal_statistics',   needsUser: true,  title: 'Персональная статистика',   desc: 'Суммарное потребление калорий и БЖУ, сравнение с целью, динамика по дням.' },
  { id: 2,  key: '2', name: 'macro_analysis',         needsUser: true,  title: 'Анализ макронутриентов',    desc: 'Соотношение белков, жиров, углеводов в процентах от калорий, сравнение с нормой.' },
  { id: 3,  key: '3', name: 'top_frequent_dishes',    needsUser: true,  title: 'Топ блюд по частоте',       desc: 'Список блюд, которые пользователь заказывает чаще всего (по количеству приёмов).' },
  { id: 4,  key: '4', name: 'top_caloric_dishes',     needsUser: true,  title: 'Топ блюд по калориям',      desc: 'Самые калорийные блюда в рационе (средняя калорийность за приём).' },
  { id: 5,  key: '5', name: 'compare_users',          needsUser: false, title: 'Сравнение пользователей',   desc: 'Сводная таблица по всем пользователям: ИМТ, активность, среднее отклонение от нормы.' },
  { id: 6,  key: '6', name: 'meal_time_analysis',     needsUser: true,  title: 'Анализ приёмов по времени', desc: 'Средняя калорийность завтрака, обеда, ужина, перекусов; поздние приёмы пищи.' },
  { id: 7,  key: '7', name: 'nutrition_calendar',     needsUser: true,  title: 'Календарь питания',         desc: 'Тепловая карта калорий по дням месяца, выделение дней с сильным превышением.' },
  { id: 8,  key: '8', name: 'progress_to_goal',       needsUser: true,  title: 'Прогресс к цели',           desc: 'Прогноз изменения веса на основе дефицита/профицита калорий.' },
  { id: 9,  key: '9', name: 'overall_statistics',     needsUser: false, title: 'Общая статистика',          desc: 'Количество приёмов, общее потребление по всем пользователям, распределение целей.' },
  { id: 10, key: '0', name: 'efficiency_report',      needsUser: true,  title: 'Отчет по эффективности',    desc: 'Процент дней, когда калорийность в пределах ±10% от цели, пропуски приёмов.' },
]

const users       = ref<User[]>([])
const currentUser = ref<User | null>(null)
const activeId    = ref(1)
const reportData  = ref<any>(null)
const loading     = ref(false)
const error       = ref<string | null>(null)
const showModal   = ref(false)
const apiOk       = ref(false)

const activeItem = computed(() => MENU_ITEMS.find(m => m.id === activeId.value)!)
const activeName = computed(() => activeItem.value.name)
const today      = computed(() => new Date().toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric' }))

async function loadReport() {
  const item = activeItem.value
  if (item.needsUser && !currentUser.value) {
    error.value = 'Выберите пользователя — нажмите [U]'
    return
  }
  loading.value  = true
  error.value    = null
  reportData.value = null
  try {
    reportData.value = await getReport(
      item.name,
      item.needsUser ? currentUser.value!.id : undefined
    )
  } catch (e: any) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

function selectItem(id: number) {
  activeId.value   = id
  reportData.value = null
  error.value      = null
  loadReport()
}

function onSelectUser(u: User) {
  currentUser.value = u
  showModal.value   = false
  reportData.value  = null
  if (activeItem.value.needsUser) loadReport()
}

function onKey(e: KeyboardEvent) {
  if (showModal.value) return
  const tag = (e.target as HTMLElement)?.tagName
  if (tag === 'INPUT' || tag === 'TEXTAREA') return

  if (e.key === 'ArrowUp')   { e.preventDefault(); activeId.value = Math.max(1, activeId.value - 1);  reportData.value = null; error.value = null }
  if (e.key === 'ArrowDown') { e.preventDefault(); activeId.value = Math.min(10, activeId.value + 1); reportData.value = null; error.value = null }
  if (e.key === 'Enter')     { loadReport() }
  if (e.key === 'u' || e.key === 'U') { showModal.value = true }
  if (e.key === 'q' || e.key === 'Q') { /* graceful exit noop */ }

  const n = parseInt(e.key)
  if (!isNaN(n)) selectItem(n === 0 ? 10 : n)
}

onMounted(async () => {
  window.addEventListener('keydown', onKey)
  try {
    users.value = await getUsers()
    apiOk.value = true
    if (users.value.length) {
      currentUser.value = users.value[0]
      await loadReport()
    }
  } catch {
    apiOk.value = false
    error.value = 'Не удалось подключиться к серверу API'
  }
})
onUnmounted(() => window.removeEventListener('keydown', onKey))
</script>

<style scoped>
.app {
  display: flex; flex-direction: column;
  width: 100vw; height: 100vh;
  background: #0c0a12; color: #d75fd7;
  font-family: 'Courier New', Consolas, monospace;
  font-size: 13px; overflow: hidden; user-select: none;
  outline: none;
}

/* TOP BAR */
.topbar {
  display: flex; align-items: center; justify-content: space-between;
  padding: 4px 12px;
  background: #1a0b2e; border-bottom: 1px solid #3d1f5e;
  min-height: 28px; flex-shrink: 0;
}
.brand      { color: #d75fd7; letter-spacing: 0.06em; font-weight: bold; }
.user-info  { color: #e8d8f0; }
.user-name  { color: #875fd7; font-weight: bold; }
.topbar-keys { color: #8b6fa8; font-size: 12px; }

/* SPLIT */
.split { display: flex; flex: 1; overflow: hidden; }

/* LEFT MENU */
.menu-panel {
  width: 240px; flex-shrink: 0;
  display: flex; flex-direction: column;
  background: #120d1e; border-right: 1px solid #3d1f5e;
}
.panel-hdr {
  background: #d75fd7; color: #0c0a12;
  text-align: center; padding: 4px 6px;
  font-weight: bold; font-size: 11px; letter-spacing: 0.08em; flex-shrink: 0;
}
.menu-list  { flex: 1; overflow-y: auto; padding: 4px 0; }
.menu-item  {
  display: flex; align-items: center;
  padding: 5px 8px; cursor: pointer;
  border-left: 3px solid transparent; color: #d75fd7;
}
.menu-item:hover:not(.active) { background: #1e0d30; }
.menu-item.active {
  background: #2a1040; color: #af87af;
  border-left-color: #af87af;
}
.cur { width: 14px; color: #af87af; flex-shrink: 0; }
.hk  { width: 26px; color: #8b6fa8; font-size: 11px; flex-shrink: 0; }
.ti  { font-size: 12px; }

/* RIGHT PANEL */
.right-panel { flex: 1; display: flex; flex-direction: column; overflow: hidden; background: #0c0a12; }

.desc-bar {
  flex-shrink: 0; background: #120d1e;
  border-bottom: 1px solid #3d1f5e;
  padding: 6px 14px; min-height: 56px;
}
.desc-lbl { color: #8b6fa8; font-size: 11px; margin-bottom: 3px; }
.desc-txt { color: #e8d8f0; font-style: italic; font-size: 13px; }

.report-body { flex: 1; overflow-y: auto; padding: 12px 14px; }

.status { color: #8b6fa8; padding: 24px 0; text-align: center; font-style: italic; }
.status.err  { color: #ef4444; }
.status.hint { color: #3d1f5e; }

/* BOTTOM BAR */
.bottombar {
  display: flex; align-items: center; justify-content: center; gap: 10px;
  padding: 3px 12px;
  background: #1a0b2e; border-top: 1px solid #3d1f5e;
  color: #d75fd7; font-size: 12px; flex-shrink: 0; min-height: 24px;
}
.k   { color: #8b6fa8; }
.ku  { color: #875fd7; }
.sep { color: #3d1f5e; }
.dim { color: #8b6fa8; font-size: 11px; }
.ok  { color: #af87af; }
.err { color: #ef4444; }
</style>
