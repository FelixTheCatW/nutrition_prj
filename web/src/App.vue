<template>
  <div class="app" tabindex="0">
    <!-- ── TOP BAR ───────────────────────────────────── -->
    <div class="topbar">
      <button class="hamburger" @click="toggleMenu" :class="{ active: isMenuOpen }" aria-label="Меню">
        <span></span>
        <span></span>
        <span></span>
      </button>
      <span class="brand">NUTRITION TRACKER</span>
      <span class="user-info">
        <template v-if="currentUser">
          {{ currentUser.name }} · {{ currentUser.age }} лет
        </template>
        <template v-else>—</template>
      </span>
      <span class="topbar-keys">[U] Пользователь</span>
    </div>
    <!-- ── MAIN SPLIT ─────────────────────────────────── -->
    <div class="split">
      <!-- OVERLAY for mobile -->
      <div class="menu-overlay" v-if="isMenuOpen" @click="closeMenu"></div>
      <!-- LEFT MENU -->
      <div class="menu-panel" :class="{ open: isMenuOpen }">
        <div class="panel-hdr">═══ Доступные отчеты ═══</div>
        <div class="menu-list">
          <div v-for="item in MENU_ITEMS" :key="item.id" class="menu-item" :class="{ active: activeId === item.id }"
            @click="selectItem(item.id)">
            <span class="cur">{{ activeId === item.id ? '►' : ' ' }}</span>
            <span class="hk">[{{ item.key }}]</span>
            <span class="ti">{{ item.title }}</span>
          </div>
        </div>
      </div>
      <!-- RIGHT PANEL -->
      <div class="right-panel">
        <!-- Description bar -->
        <div class="desc-bar">
          <div class="desc-lbl">═══ Описание ═══</div>
          <div class="desc-txt">{{ activeItem.desc }}</div>
        </div>
        <!-- Report body -->
        <div class="report-body">
          <div v-if="loading" class="status">⣾ Загрузка данных…</div>
          <div v-else-if="error" class="status err">✖ {{ error }}</div>
          <div v-else-if="!reportData" class="status hint">
            Нажмите [Enter] для запуска отчёта или кликните на пункт меню
          </div>
          <ReportPanel v-else :reportName="activeName" :data="reportData" :user="currentUser" />
        </div>
      </div>
    </div>
    <!-- ── BOTTOM BAR ─────────────────────────────────── -->
    <div class="bottombar">
      <span><span class="k">[↑↓]</span> Навигация</span>
      <span class="sep">│</span>
      <span><span class="k">[Enter]</span> Запустить</span>
      <span class="sep hide-mobile">│</span>
      <span class="hide-mobile"><span class="k">[U]</span> <span class="ku">Пользователь</span></span>
      <span class="sep hide-mobile">│</span>
      <span class="hide-mobile"><span class="k">[1–0]</span> Быстрый переход</span>
      <span class="sep">│</span>
      <span class="dim">API: <span :class="apiOk ? 'ok' : 'err'">{{ apiOk ? '● online' : '○ offline' }}</span></span>
    </div>
    <!-- ── USER MODAL ─────────────────────────────────── -->
    <UserModal v-if="showUserModal" :users="users" :currentId="currentUser?.id" @select="onUserSelect"
      @close="showUserModal = false" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import ReportPanel from './components/ReportPanel.vue'
import UserModal from './components/UserModal.vue'
import { getUsers, getReport, type User } from './api'

const MENU_ITEMS = [
  { id: 1, key: '1', title: 'Персональная статистика', desc: 'Среднее потребление, сравнение с целью, динамика по дням.' },
  { id: 2, key: '2', title: 'Анализ макронутриентов', desc: 'Соотношение БЖУ в калориях, круговая диаграмма.' },
  { id: 3, key: '3', title: 'Топ частых блюд', desc: 'Рейтинг блюд по количеству приёмов.' },
  { id: 4, key: '4', title: 'Топ калорийных блюд', desc: 'Средняя калорийность за приём.' },
  { id: 5, key: '5', title: 'Сравнение пользователей', desc: 'ИМТ, отклонение от цели, гистограмма.' },
  { id: 6, key: '6', title: 'Анализ приёмов по времени', desc: 'Калорийность завтрака/обеда/ужина/перекуса.' },
  { id: 7, key: '7', title: 'Календарь питания', desc: 'Калорийность по дням месяца с цветовой индикацией.' },
  { id: 8, key: '8', title: 'Прогресс к цели', desc: 'Дефицит/профицит калорий, прогноз веса.' },
  { id: 9, key: '9', title: 'Общая статистика', desc: 'Количество приёмов, уникальных блюд, распределение целей.' },
  { id: 10, key: '0', title: 'Отчёт по эффективности', desc: 'Дни с нормой, пропуски приёмов, гистограмма.' },
]

const users = ref<User[]>([])
const currentUser = ref<User | null>(null)
const activeId = ref(1)
const reportData = ref<any>(null)
const loading = ref(false)
const error = ref<string | null>(null)
const showUserModal = ref(false)
const apiOk = ref(true)
const isMenuOpen = ref(false)

const activeItem = computed(() => MENU_ITEMS.find(m => m.id === activeId.value) || MENU_ITEMS[0])
const activeName = computed(() => {
  const names: Record<number, string> = {
    1: 'personal_statistics',
    2: 'macro_analysis',
    3: 'top_frequent_dishes',
    4: 'top_caloric_dishes',
    5: 'compare_users',
    6: 'meal_time_analysis',
    7: 'nutrition_calendar',
    8: 'progress_to_goal',
    9: 'overall_statistics',
    10: 'efficiency_report',
  }
  return names[activeId.value] || 'personal_statistics'
})

const today = computed(() => {
  const d = new Date()
  return d.toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric' })
})

async function loadUsers() {
  try {
    const data = await getUsers()
    users.value = data
    if (data.length > 0 && !currentUser.value) {
      currentUser.value = data[0]
    }
    apiOk.value = true
  } catch (e: any) {
    apiOk.value = false
    console.error('Failed to load users:', e)
  }
}

async function loadReport() {
  if (!currentUser.value) return
  loading.value = true
  error.value = null
  reportData.value = null
  try {
    const data = await getReport(activeName.value, currentUser.value.id)
    reportData.value = data
  } catch (e: any) {
    error.value = e.message || 'Ошибка загрузки отчёта'
  } finally {
    loading.value = false
  }
}

function selectItem(id: number) {
  activeId.value = id
  closeMenu()
  loadReport()
}

function onUserSelect(user: User) {
  currentUser.value = user
  showUserModal.value = false
  if (reportData.value) loadReport()
}

function toggleMenu() {
  isMenuOpen.value = !isMenuOpen.value
}

function closeMenu() {
  isMenuOpen.value = false
}

function onKey(e: KeyboardEvent) {
  if (showUserModal.value) return
  if (e.key === 'u' || e.key === 'U' || e.key === 'г' || e.key === 'Г') {
    showUserModal.value = true
    return
  }
  if (e.key === 'ArrowUp') {
    e.preventDefault()
    const idx = MENU_ITEMS.findIndex(m => m.id === activeId.value)
    if (idx > 0) selectItem(MENU_ITEMS[idx - 1].id)
  }
  if (e.key === 'ArrowDown') {
    e.preventDefault()
    const idx = MENU_ITEMS.findIndex(m => m.id === activeId.value)
    if (idx < MENU_ITEMS.length - 1) selectItem(MENU_ITEMS[idx + 1].id)
  }
  if (e.key === 'Enter') {
    loadReport()
  }
  const num = parseInt(e.key)
  if (!isNaN(num)) {
    const id = num === 0 ? 10 : num
    const item = MENU_ITEMS.find(m => m.id === id)
    if (item) selectItem(item.id)
  }
}

onMounted(() => {
  loadUsers()
  window.addEventListener('keydown', onKey)
})

onUnmounted(() => {
  window.removeEventListener('keydown', onKey)
})
</script>

<style scoped>
.app {
  display: flex;
  flex-direction: column;
  width: 100vw;
  height: 100vh;
  background: #0c0a12;
  color: #d75fd7;
  font-family: 'Courier New', Consolas, monospace;
  font-size: 14px;
  overflow: hidden;
  user-select: none;
  outline: none;
}

/* TOP BAR */
.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 4px 12px;
  background: #1a0b2e;
  border-bottom: 1px solid #3d1f5e;
  min-height: 36px;
  flex-shrink: 0;
  gap: 8px;
}

/* HAMBURGER BUTTON */
.hamburger {
  display: none;
  flex-direction: column;
  justify-content: space-around;
  width: 28px;
  height: 28px;
  background: transparent;
  border: none;
  cursor: pointer;
  padding: 4px;
  z-index: 101;
  flex-shrink: 0;
}

.hamburger span {
  display: block;
  width: 100%;
  height: 2px;
  background: #d75fd7;
  border-radius: 2px;
  transition: all 0.3s ease;
}

.hamburger.active span:nth-child(1) {
  transform: translateY(8px) rotate(45deg);
}

.hamburger.active span:nth-child(2) {
  opacity: 0;
}

.hamburger.active span:nth-child(3) {
  transform: translateY(-8px) rotate(-45deg);
}

.brand {
  color: #d75fd7;
  letter-spacing: 0.06em;
  font-weight: bold;

}

.user-info {
  color: #e8d8f0;
  font-size: 12px;
}

.user-name {
  color: #875fd7;
  font-weight: bold;
}

.topbar-keys {
  color: #8b6fa8;
  font-size: 11px;
}

/* SPLIT */
.split {
  display: flex;
  flex: 1;
  overflow: hidden;
  position: relative;
}

/* MENU OVERLAY (mobile) */
.menu-overlay {
  display: none;
  position: fixed;
  inset: 0;
  background: rgba(12, 10, 18, 0.7);
  z-index: 49;
}

/* LEFT MENU */
.menu-panel {
  width: 240px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  background: #120d1e;
  border-right: 1px solid #3d1f5e;
  z-index: 50;
  transition: transform 0.3s ease;
}

.panel-hdr {
  background: #d75fd7;
  color: #0c0a12;
  text-align: center;
  padding: 4px 6px;
  font-weight: bold;
  font-size: 11px;
  letter-spacing: 0.08em;
  flex-shrink: 0;
}

.menu-list {
  flex: 1;
  overflow-y: auto;
  padding: 4px 0;
}

.menu-item {
  display: flex;
  align-items: center;
  padding: 5px 8px;
  cursor: pointer;
  border-left: 3px solid transparent;
  color: #d75fd7;
}

.menu-item:hover:not(.active) {
  background: #1e0d30;
}

.menu-item.active {
  background: #2a1040;
  color: #af87af;
  border-left-color: #af87af;
}

.cur {
  width: 14px;
  color: #af87af;
  flex-shrink: 0;
}

.hk {
  width: 26px;
  color: #8b6fa8;
  font-size: 11px;
  flex-shrink: 0;
}

.ti {
  font-size: 12px;
}

/* RIGHT PANEL */
.right-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: #0c0a12;
}

.desc-bar {
  flex-shrink: 0;
  background: #120d1e;
  border-bottom: 1px solid #3d1f5e;
  padding: 6px 14px;
  min-height: 56px;
}

.desc-lbl {
  color: #8b6fa8;
  font-size: 11px;
  margin-bottom: 3px;
}

.desc-txt {
  color: #e8d8f0;
  font-style: italic;
  font-size: 13px;
}

.report-body {
  flex: 1;
  overflow-y: auto;
  padding: 12px 14px;
}

.status {
  color: #8b6fa8;
  padding: 24px 0;
  text-align: center;
  font-style: italic;
}

.status.err {
  color: #ef4444;
}

.status.hint {
  color: #3d1f5e;
}

/* BOTTOM BAR */
.bottombar {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 3px 12px;
  background: #1a0b2e;
  border-top: 1px solid #3d1f5e;
  color: #d75fd7;
  font-size: 12px;
  flex-shrink: 0;
  min-height: 24px;
  flex-wrap: wrap;
}

.k {
  color: #8b6fa8;
}

.ku {
  color: #875fd7;
}

.sep {
  color: #3d1f5e;
}

.dim {
  color: #8b6fa8;
  font-size: 11px;
}

.ok {
  color: #af87af;
}

.err {
  color: #ef4444;
}

/* ──────────────────────────────────────────────────────────
   RESPONSIVE / MOBILE STYLES
   ────────────────────────────────────────────────────────── */
@media (max-width: 768px) {
  .app {
    font-size: 12px;
  }

  /* Show hamburger */
  .hamburger {
    display: flex;
  }

  /* Topbar adjustments */
  .topbar {
    padding: 4px 8px;
    min-height: 40px;
  }

  .brand {
    font-size: 11px;
    letter-spacing: 0.03em;
  }

  .user-info {
    font-size: 11px;
    flex: 1;
    text-align: center;
  }

  .topbar-keys {
    display: none;
  }

  /* Menu as overlay on mobile */
  .menu-overlay {
    display: block;
  }

  .menu-panel {
    position: fixed;
    top: 0;
    left: 0;
    bottom: 0;
    width: 260px;
    max-width: 80vw;
    transform: translateX(-100%);
    box-shadow: 4px 0 20px rgba(215, 95, 215, 0.2);
  }

  .menu-panel.open {
    transform: translateX(0);
  }

  /* Description bar */
  .desc-bar {
    padding: 6px 10px;
    min-height: 44px;
  }

  .desc-lbl {
    font-size: 10px;
  }

  .desc-txt {
    font-size: 12px;
  }

  /* Report body */
  .report-body {
    padding: 8px 10px;
  }

  /* Bottom bar */
  .bottombar {
    font-size: 10px;
    gap: 6px;
    padding: 3px 8px;
    min-height: 28px;
  }

  .hide-mobile {
    display: none;
  }
}

/* Extra small devices */
@media (max-width: 480px) {
  .brand {
    font-size: 10px;
  }

  .user-info {
    font-size: 10px;
  }

  .menu-panel {
    width: 100%;
    max-width: 100%;
  }

  .desc-txt {
    font-size: 11px;
  }

  .bottombar {
    font-size: 9px;
    gap: 4px;
  }
}
</style>