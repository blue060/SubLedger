export interface Subscription {
  id: number
  name: string
  amount: number
  currency: string
  billing_cycle: string
  billing_cycle_num: number
  billing_cycle_unit: string
  first_payment_date: string
  next_payment_date: string | null
  category_id: number | null
  category_name: string | null
  category_color: string | null
  notes: string | null
  url: string | null
  expiry_date: string | null
  payment_method: string | null
  intro_amount: number | null
  intro_months: number | null
  remaining_days: number | null
  notify: boolean
  is_active: boolean
}

export interface SubscriptionCreate {
  name: string
  amount: number
  currency: string
  billing_cycle: string
  billing_cycle_num: number
  billing_cycle_unit: string
  first_payment_date: string
  category_id: number | null
  notes: string | null
  url: string | null
  expiry_date: string | null
  payment_method: string | null
  intro_amount: number | null
  intro_months: number | null
  notify: boolean
}

export interface SubscriptionUpdate {
  name?: string
  amount?: number
  currency?: string
  billing_cycle?: string
  billing_cycle_num?: number
  billing_cycle_unit?: string
  first_payment_date?: string
  category_id?: number | null
  notes?: string | null
  url?: string | null
  expiry_date?: string | null
  payment_method?: string | null
  intro_amount?: number | null
  intro_months?: number | null
  notify?: boolean
  is_active?: boolean
}

export interface Category {
  id: number
  name: string
  icon: string | null
  color: string | null
  sort_order: number
}

export interface CategoryCreate {
  name: string
  icon?: string | null
  color?: string | null
  sort_order?: number
}

export interface CategoryUpdate {
  name?: string
  icon?: string | null
  color?: string | null
  sort_order?: number
}