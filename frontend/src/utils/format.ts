export function formatCurrency(amount: number, currency: string): string {
  const symbols: Record<string, string> = { CNY: '¥', USD: '$', EUR: '€', GBP: '£', JPY: '¥', HKD: '$' }
  return `${symbols[currency] || ''}${amount.toFixed(2)}`
}

export function getFavicon(url: string): string {
  try {
    const domain = new URL(url).hostname
    return `https://favicon.im/${domain}`
  } catch {
    return ''
  }
}

export function cycleLabel(cycle: string, num?: number, unit?: string, zhCN?: any): string {
  if (zhCN) {
    if (cycle === 'permanent') return zhCN.subscription.permanent
    if (cycle === 'once') return zhCN.subscription.once
    if (cycle === 'custom' && num && unit) {
      const unitLabel = unit === 'year' ? zhCN.subscription.unitYear : zhCN.subscription.unitMonth
      return `每${num}${unitLabel}`
    }
    const labels: Record<string, string> = { monthly: zhCN.subscription.monthly, quarterly: zhCN.subscription.quarterly, yearly: zhCN.subscription.yearly }
    return labels[cycle] || cycle
  }
  if (cycle === 'permanent') return '永久'
  if (cycle === 'once') return '一次性'
  if (cycle === 'custom' && num && unit) {
    const unitLabel = unit === 'year' ? '年' : '月'
    return `每${num}${unitLabel}`
  }
  const labels: Record<string, string> = { monthly: '月付', quarterly: '季付', yearly: '年付' }
  return labels[cycle] || cycle
}
