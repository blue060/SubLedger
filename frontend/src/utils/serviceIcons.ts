/**
 * Icon resolution for subscriptions.
 *
 * Priority: Simple Icons CDN → Google Favicon API → letter avatar
 *
 * Simple Icons has 2000+ brand SVGs: https://simpleicons.org
 */

// Service name/URL keyword → Simple Icons slug
const SIMPLE_ICONS_MAP: Record<string, string> = {
  // Chinese services
  'bilibili': 'bilibili',
  'B站': 'bilibili',
  '哔哩哔哩': 'bilibili',
  'iqiyi': 'iqiyi',
  '爱奇艺': 'iqiyi',
  'v.qq.com': 'tencentqq',
  'qq.com': 'tencentqq',
  '腾讯视频': 'tencentqq',
  'youku': 'youku',
  '优酷': 'youku',
  'mgtv': 'weibo',
  '芒果': 'mango',
  'music.163.com': 'netease',
  '网易云': 'netease',
  'y.qq.com': 'tencentqq',
  'qq音乐': 'tencentqq',
  'kugou': 'kugou',
  '酷狗': 'kugou',
  'pan.baidu.com': 'baidu',
  '百度网盘': 'baidu',
  'aliyun': 'alibabacloud',
  '阿里云': 'alibabacloud',
  'huaweicloud': 'huawei',
  '华为云': 'huawei',
  'greencloud': 'greenhouse',
  'greencloudvps': 'greenhouse',
  'weixin.qq.com': 'wechat',
  '微信': 'wechat',
  'weibo': 'sinaweibo',
  '微博': 'sinaweibo',
  'wps': 'wpsoffice',
  'meituan': 'meituan',
  '美团': 'meituan',
  // International services
  'netflix': 'netflix',
  'spotify': 'spotify',
  'youtube': 'youtube',
  'music.apple.com': 'applemusic',
  'apple-music': 'applemusic',
  'icloud': 'icloud',
  'chatgpt': 'openai',
  'chat.openai': 'openai',
  'claude': 'anthropic',
  'github': 'github',
  'copilot': 'githubcopilot',
  'notion': 'notion',
  '1password': '1password',
  'microsoft': 'microsoft',
  'discord': 'discord',
  'steam': 'steam',
  'weiyun': 'icloud',
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

/**
 * Get an ordered list of icon URLs to try.
 * Falls through on error in the component.
 */
export function getIconSources(url: string, name: string): string[] {
  const sources: string[] = []

  // 1. Simple Icons CDN (match by URL or name)
  const slug = resolveSlug(url, name)
  if (slug) {
    sources.push(`https://cdn.simpleicons.org/${slug}`)
  }

  // 2. Google Favicon API
  if (url) {
    try {
      const domain = new URL(url.startsWith('http') ? url : `https://${url}`).hostname
      sources.push(`https://www.google.com/s2/favicons?domain=${domain}&sz=64`)
    } catch {}
  }

  return sources
}

function resolveSlug(url: string, name: string): string | null {
  // Try URL match first (longer keys = more specific)
  if (url) {
    const lower = url.toLowerCase()
    const sorted = Object.keys(SIMPLE_ICONS_MAP).sort((a, b) => b.length - a.length)
    for (const key of sorted) {
      if (lower.includes(key.toLowerCase())) {
        return SIMPLE_ICONS_MAP[key]
      }
    }
  }
  // Try name match
  if (name) {
    const nameLower = name.toLowerCase()
    const sorted = Object.keys(SIMPLE_ICONS_MAP).sort((a, b) => b.length - a.length)
    for (const key of sorted) {
      if (nameLower.includes(key.toLowerCase())) {
        return SIMPLE_ICONS_MAP[key]
      }
    }
  }
  return null
}

export function getCategoryColor(categoryNameOrIcon: string): string {
  if (CATEGORY_COLORS[categoryNameOrIcon]) return CATEGORY_COLORS[categoryNameOrIcon]
  return '#6366f1'
}
