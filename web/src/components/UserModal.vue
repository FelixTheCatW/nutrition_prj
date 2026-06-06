<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal-box">
      <div class="modal-title">╔══ ВЫБЕРИТЕ ПОЛЬЗОВАТЕЛЯ ══╗</div>
      <div class="modal-list" ref="listRef">
        <div
          v-for="(u, i) in users"
          :key="u.id"
          class="modal-item"
          :class="{ selected: i === cursor }"
          @mouseenter="cursor = i"
          @click="$emit('select', u)"
        >
          <span class="star">{{ i === cursor ? '★' : ' ' }}</span>
          <span class="uname">{{ u.name }}</span>
          <span class="uinfo">{{ u.city }} · {{ u.gender[0].toUpperCase() }} · {{ u.age }} лет</span>
        </div>
      </div>
      <div class="modal-footer">
        [↑↓] навигация  [Enter] выбрать  [Esc] отмена
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
import type { User } from '../api'

const props = defineProps<{ users: User[]; currentId?: number }>()
const emit  = defineEmits<{ select: [u: User]; close: [] }>()

const listRef = ref<HTMLElement | null>(null)
const cursor  = ref(props.users.findIndex(u => u.id === props.currentId) ?? 0)
if (cursor.value < 0) cursor.value = 0

watch(cursor, () => {
  const el = listRef.value?.children[cursor.value] as HTMLElement
  el?.scrollIntoView({ block: 'nearest' })
})

function onKey(e: KeyboardEvent) {
  if (e.key === 'ArrowUp')   { e.preventDefault(); cursor.value = Math.max(0, cursor.value - 1) }
  if (e.key === 'ArrowDown') { e.preventDefault(); cursor.value = Math.min(props.users.length - 1, cursor.value + 1) }
  if (e.key === 'Enter')     { emit('select', props.users[cursor.value]) }
  if (e.key === 'Escape')    { emit('close') }
}

onMounted(()   => window.addEventListener('keydown', onKey))
onUnmounted(() => window.removeEventListener('keydown', onKey))
</script>

<style scoped>
.modal-overlay {
  position: fixed; inset: 0; z-index: 100;
  display: flex; align-items: center; justify-content: center;
  background: rgba(12, 10, 18, 0.88);
}
.modal-box {
  display: flex; flex-direction: column;
  min-width: 480px; max-width: 560px;
  background: #120d1e;
  border: 2px solid #d75fd7;
  box-shadow: 0 0 50px #d75fd755;
  font-family: 'Courier New', Consolas, monospace;
}
.modal-title {
  background: #d75fd7; color: #0c0a12;
  text-align: center; padding: 5px 12px;
  font-weight: bold; font-size: 13px; letter-spacing: 0.05em;
}
.modal-list {
  overflow-y: auto; max-height: 360px;
  background: #120d1e;
}
.modal-item {
  display: flex; align-items: baseline; gap: 8px;
  padding: 5px 14px; cursor: pointer;
  color: #d75fd7; font-size: 13px;
}
.modal-item:hover, .modal-item.selected {
  background: #d75fd7; color: #0c0a12;
}
.star { width: 16px; flex-shrink: 0; }
.uname { flex: 1; font-weight: bold; }
.uinfo { font-size: 11px; opacity: 0.7; }
.modal-item.selected .uinfo { opacity: 0.6; }
.modal-footer {
  text-align: center; padding: 5px 12px;
  background: #1a0b2e; color: #8b6fa8;
  font-size: 11px; border-top: 1px solid #3d1f5e;
}
</style>
