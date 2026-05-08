// Domain keyword → built-in icon mapping
// Keys are lowercase domain substrings used for matching
const BUILTIN_ICONS: Record<string, string> = {
  // Chinese services
  'iqiyi': 'iqiyi',
  'bilibili': 'bilibili',
  'v.qq.com': 'tencent-video',
  'qq.com': 'qq',
  'youku': 'youku',
  'mgtv': 'mgtv',
  'music.163.com': 'netease-music',
  'y.qq.com': 'qq-music',
  'kugou': 'kugou',
  'pan.baidu.com': 'baidu-pan',
  'aliyun': 'aliyun',
  'weiyun': 'icloud',
  'weixin.qq.com': 'wechat',
  'weibo': 'weibo',
  'wps': 'wps',
  'meituan': 'meituan',
  // International services
  'netflix': 'netflix',
  'spotify': 'spotify',
  'youtube': 'youtube',
  'music.apple.com': 'apple-music',
  'icloud': 'icloud',
  'chatgpt': 'chatgpt',
  'chat.openai': 'chatgpt',
  'claude': 'claude',
  'github': 'github',
  'copilot': 'github-copilot',
  'notion': 'notion',
  '1password': '1password',
  'microsoft': 'microsoft-365',
  'discord': 'discord',
  'steam': 'steam',
}

// Category color fallback for letter avatars
const CATEGORY_COLORS: Record<string, string> = {
  '视频': '#E50914',
  '音乐': '#1DB954',
  '云存储': '#3693F5',
  '会员': '#FF6A00',
  '工具': '#6366f1',
  '游戏': '#5865F2',
  '其他': '#94a3b8',
  'AI工具': '#10A37F',
  '开发工具': '#24292F',
  '云服务': '#0572EC',
}

// Category icon name mapping (for templates that don't have URLs)
const CATEGORY_ICON_MAP: Record<string, string> = {
  'VideoPlay': '视频',
  'Headset': '音乐',
  'Cloudy': '云存储',
  'User': '会员',
  'Setting': '工具',
  'GamePad': '游戏',
  'More': '其他',
  'MagicStick': 'AI工具',
  'Cpu': '开发工具',
}

/**
 * Try to match a URL to a built-in icon key
 */
export function getServiceIconKey(url: string | null | undefined): string | null {
  if (!url) return null
  const lower = url.toLowerCase()
  // Check longer domain matches first (more specific)
  const sortedKeys = Object.keys(BUILTIN_ICONS).sort((a, b) => b.length - a.length)
  for (const key of sortedKeys) {
    if (lower.includes(key)) {
      return BUILTIN_ICONS[key]
    }
  }
  return null
}

/**
 * Resolve icon for a template by its URL or name
 */
export function getTemplateIconKey(tpl: { url?: string; name: string }): string | null {
  // Try URL match first
  const fromUrl = getServiceIconKey(tpl.url)
  if (fromUrl) return fromUrl
  // Try name match
  const nameLower = tpl.name.toLowerCase()
  const sortedKeys = Object.keys(BUILTIN_ICONS).sort((a, b) => b.length - a.length)
  for (const key of sortedKeys) {
    if (nameLower.includes(key)) {
      return BUILTIN_ICONS[key]
    }
  }
  return null
}

/**
 * Get a category color for letter avatar fallback
 */
export function getCategoryColor(categoryNameOrIcon: string): string {
  // Try direct category name
  if (CATEGORY_COLORS[categoryNameOrIcon]) return CATEGORY_COLORS[categoryNameOrIcon]
  // Try icon→name mapping
  const name = CATEGORY_ICON_MAP[categoryNameOrIcon]
  if (name && CATEGORY_COLORS[name]) return CATEGORY_COLORS[name]
  return '#6366f1'
}

/**
 * Get all built-in icon keys
 */
export function getAllIconKeys(): string[] {
  return Object.values(BUILTIN_ICONS)
}

export { BUILTIN_ICONS, CATEGORY_COLORS }