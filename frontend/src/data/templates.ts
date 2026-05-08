export interface SubscriptionTemplate {
  name: string
  amount: number
  currency: string
  billing_cycle: string
  category_name: string
  url: string
}

export const TEMPLATES: SubscriptionTemplate[] = [
  { name: 'Netflix', amount: 15.99, currency: 'USD', billing_cycle: 'monthly', category_name: '视频', url: 'https://netflix.com' },
  { name: 'Spotify', amount: 9.99, currency: 'USD', billing_cycle: 'monthly', category_name: '音乐', url: 'https://spotify.com' },
  { name: 'YouTube Premium', amount: 13.99, currency: 'USD', billing_cycle: 'monthly', category_name: '视频', url: 'https://youtube.com' },
  { name: 'Apple Music', amount: 10.99, currency: 'USD', billing_cycle: 'monthly', category_name: '音乐', url: 'https://music.apple.com' },
  { name: 'iCloud+ 50GB', amount: 0.99, currency: 'USD', billing_cycle: 'monthly', category_name: '云存储', url: 'https://icloud.com' },
  { name: 'iCloud+ 200GB', amount: 2.99, currency: 'USD', billing_cycle: 'monthly', category_name: '云存储', url: 'https://icloud.com' },
  { name: 'ChatGPT Plus', amount: 20.00, currency: 'USD', billing_cycle: 'monthly', category_name: 'AI工具', url: 'https://chat.openai.com' },
  { name: 'Claude Pro', amount: 20.00, currency: 'USD', billing_cycle: 'monthly', category_name: 'AI工具', url: 'https://claude.ai' },
  { name: 'GitHub Copilot', amount: 10.00, currency: 'USD', billing_cycle: 'monthly', category_name: '开发工具', url: 'https://github.com' },
  { name: 'Microsoft 365', amount: 6.99, currency: 'USD', billing_cycle: 'monthly', category_name: '工具', url: 'https://microsoft.com' },
  { name: '百度网盘超级会员', amount: 30.00, currency: 'CNY', billing_cycle: 'monthly', category_name: '云存储', url: 'https://pan.baidu.com' },
  { name: '腾讯视频VIP', amount: 30.00, currency: 'CNY', billing_cycle: 'monthly', category_name: '视频', url: 'https://v.qq.com' },
  { name: '爱奇艺VIP', amount: 25.00, currency: 'CNY', billing_cycle: 'monthly', category_name: '视频', url: 'https://iqiyi.com' },
  { name: 'B站大会员', amount: 25.00, currency: 'CNY', billing_cycle: 'monthly', category_name: '视频', url: 'https://bilibili.com' },
  { name: '网易云音乐黑胶VIP', amount: 18.00, currency: 'CNY', billing_cycle: 'monthly', category_name: '音乐', url: 'https://music.163.com' },
  { name: 'QQ会员', amount: 10.00, currency: 'CNY', billing_cycle: 'monthly', category_name: '会员', url: 'https://vip.qq.com' },
  { name: '阿里云服务器ECS', amount: 50.00, currency: 'CNY', billing_cycle: 'monthly', category_name: '云服务', url: 'https://aliyun.com' },
  { name: 'Notion Plus', amount: 10.00, currency: 'USD', billing_cycle: 'monthly', category_name: '工具', url: 'https://notion.so' },
  { name: '1Password', amount: 2.99, currency: 'USD', billing_cycle: 'monthly', category_name: '工具', url: 'https://1password.com' },
  { name: '优酷VIP', amount: 25.00, currency: 'CNY', billing_cycle: 'monthly', category_name: '视频', url: 'https://youku.com' },
  { name: '芒果TV会员', amount: 22.00, currency: 'CNY', billing_cycle: 'monthly', category_name: '视频', url: 'https://mgtv.com' },
  { name: 'QQ音乐绿钻', amount: 15.00, currency: 'CNY', billing_cycle: 'monthly', category_name: '音乐', url: 'https://y.qq.com' },
  { name: 'WPS会员', amount: 18.00, currency: 'CNY', billing_cycle: 'monthly', category_name: '工具', url: 'https://wps.cn' },
  { name: 'Discord Nitro', amount: 9.99, currency: 'USD', billing_cycle: 'monthly', category_name: '社交', url: 'https://discord.com' },
]