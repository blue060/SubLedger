import api from './useApi'

const STORAGE_KEY = 'subledger_notified'

function getNotified(): Set<string> {
  try {
    return new Set(JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]'))
  } catch {
    return new Set()
  }
}

function markNotified(key: string) {
  const set = getNotified()
  set.add(key)
  // Keep only last 200 entries
  const arr = Array.from(set)
  if (arr.length > 200) arr.splice(0, arr.length - 200)
  localStorage.setItem(STORAGE_KEY, JSON.stringify(arr))
}

export async function initBrowserNotifications() {
  if (!('Notification' in window)) return
  if (Notification.permission === 'denied') return

  // Request permission if not yet decided
  if (Notification.permission === 'default') {
    await Notification.requestPermission()
  }

  if (Notification.permission !== 'granted') return

  try {
    const [subsRes, settingsRes] = await Promise.all([
      api.get('/subscriptions', { params: { is_active: true, is_expired: false } }),
      api.get('/settings'),
    ])
    const subs = subsRes.data || []
    const reminderDays = settingsRes.data?.reminder_days || 7
    const today = new Date()
    today.setHours(0, 0, 0, 0)
    const cutoff = new Date(today)
    cutoff.setDate(cutoff.getDate() + reminderDays)

    const notified = getNotified()

    for (const sub of subs) {
      const key = `${sub.id}_${sub.next_payment_date || sub.expiry_date}`
      if (notified.has(key)) continue

      let title = ''
      let body = ''
      const nextDate = sub.next_payment_date ? new Date(sub.next_payment_date) : null
      const expiryDate = sub.expiry_date ? new Date(sub.expiry_date) : null

      if (sub.auto_renew && nextDate && nextDate >= today && nextDate <= cutoff) {
        const days = Math.ceil((nextDate.getTime() - today.getTime()) / 86400000)
        title = 'SubLedger 订阅提醒'
        body = `${sub.name} 将在 ${days} 天后扣款`
      } else if (!sub.auto_renew && expiryDate && expiryDate >= today && expiryDate <= cutoff) {
        const days = Math.ceil((expiryDate.getTime() - today.getTime()) / 86400000)
        title = 'SubLedger 到期提醒'
        body = `${sub.name} 将在 ${days} 天后到期`
      }

      if (title) {
        new Notification(title, { body, icon: '/favicon.svg', tag: key })
        markNotified(key)
      }
    }
  } catch {
    // Silently fail
  }
}
