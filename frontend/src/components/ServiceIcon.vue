<template>
  <div
    class="service-icon"
    :style="containerStyle"
    :title="name"
  >
    <img
      v-if="currentSrc && !allFailed"
      :src="currentSrc"
      @error="handleError"
    />
    <span v-else class="letter-avatar" :style="letterStyle">
      {{ letter }}
    </span>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { getIconSources, getCategoryColor } from '../utils/serviceIcons'

const props = defineProps<{
  name: string
  url?: string
  categoryColor?: string
  size?: number
}>()

const size = computed(() => props.size || 40)

// Build ordered list of icon sources to try
const sources = computed(() => getIconSources(props.url || '', props.name))
const sourceIndex = ref(0)
const allFailed = ref(false)

const currentSrc = computed(() => {
  if (allFailed.value || sourceIndex.value >= sources.value.length) return null
  return sources.value[sourceIndex.value]
})

function handleError() {
  if (sourceIndex.value < sources.value.length - 1) {
    sourceIndex.value++
  } else {
    allFailed.value = true
  }
}

const letter = computed(() => {
  const n = props.name.trim()
  if (/[一-鿿]/.test(n)) return n[0]
  return n[0]?.toUpperCase() || '?'
})

const categoryColor = computed(() => props.categoryColor || '#6366f1')

const containerStyle = computed(() => ({
  width: `${size.value}px`,
  height: `${size.value}px`,
  borderRadius: `${Math.round(size.value * 0.3)}px`,
}))

const letterStyle = computed(() => {
  const bg = getCategoryColor(categoryColor.value)
  const fontSize = Math.round(size.value * 0.45)
  return {
    backgroundColor: bg,
    fontSize: `${fontSize}px`,
  }
})
</script>

<style scoped>
.service-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  overflow: hidden;
  background: var(--surface-secondary, #f1f5f9);
  transition: transform 0.2s ease;
}
.service-icon img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}
.letter-avatar {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  color: #fff;
  font-weight: 700;
  letter-spacing: 0;
}
html.dark .service-icon {
  background: var(--surface-secondary, #1e293b);
}
</style>
