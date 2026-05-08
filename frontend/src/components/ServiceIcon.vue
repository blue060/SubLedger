<template>
  <div
    class="service-icon"
    :style="containerStyle"
    :title="name"
  >
    <img
      v-if="iconSrc"
      :src="iconSrc"
    />
    <img
      v-else-if="!iconFailed && resolvedUrl"
      :src="resolvedUrl"
      @error="handleGoogleError"
    />
    <span v-else class="letter-avatar" :style="letterStyle">
      {{ letter }}
    </span>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { getServiceIconKey, getCategoryColor } from '../utils/serviceIcons'

// Import all built-in SVGs as URLs via Vite's ?url import
const iconModules = import.meta.glob('../assets/icons/*.svg', { eager: true, query: '?url', import: 'default' })

// Build a map: iconKey → resolved URL
const iconUrlMap: Record<string, string> = {}
for (const path in iconModules) {
  const key = path.replace('../assets/icons/', '').replace('.svg', '')
  iconUrlMap[key] = (iconModules[path] as string) || ''
}

const props = defineProps<{
  name: string
  url?: string
  categoryColor?: string
  size?: number
}>()

const size = computed(() => props.size || 40)
const iconKey = computed(() => getServiceIconKey(props.url || ''))
const iconSrc = computed(() => iconKey.value ? iconUrlMap[iconKey.value] : null)

// Google Favicon API fallback
const resolvedUrl = computed(() => {
  if (!props.url) return null
  try {
    const domain = new URL(props.url.startsWith('http') ? props.url : `https://${props.url}`).hostname
    return `https://www.google.com/s2/favicons?domain=${domain}&sz=64`
  } catch {
    return null
  }
})

const iconFailed = ref(false)
function handleGoogleError() {
  iconFailed.value = true
}

const letter = computed(() => {
  const n = props.name.trim()
  // For Chinese names, use first character
  if (/[一-鿿]/.test(n)) return n[0]
  // For English names, use first letter uppercase
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