import { defineStore } from 'pinia'
import { ref } from 'vue'
import { listCategories, createCategory, updateCategory, deleteCategory } from '../api/categories'
import type { Category, CategoryCreate, CategoryUpdate } from '../types/subscription'

export const useCategoryStore = defineStore('category', () => {
  const categories = ref<Category[]>([])

  async function fetchList() {
    const res = await listCategories()
    categories.value = res.data
  }

  async function create(data: CategoryCreate) {
    const res = await createCategory(data)
    categories.value.push(res.data)
    return res.data
  }

  async function update(id: number, data: CategoryUpdate) {
    const res = await updateCategory(id, data)
    const idx = categories.value.findIndex((c) => c.id === id)
    if (idx !== -1) categories.value[idx] = res.data
    return res.data
  }

  async function remove(id: number) {
    await deleteCategory(id)
    categories.value = categories.value.filter((c) => c.id !== id)
  }

  return { categories, fetchList, create, update, remove }
})