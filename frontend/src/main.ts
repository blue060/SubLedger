import { createApp } from 'vue'
import { createPinia } from 'pinia'
import {
  ElAside,
  ElBadge,
  ElButton,
  ElCalendar,
  ElCard,
  ElCol,
  ElCollapse,
  ElCollapseItem,
  ElColorPicker,
  ElConfigProvider,
  ElContainer,
  ElDatePicker,
  ElDialog,
  ElDropdown,
  ElDropdownItem,
  ElDropdownMenu,
  ElEmpty,
  ElForm,
  ElFormItem,
  ElHeader,
  ElIcon,
  ElInput,
  ElInputNumber,
  ElLoading,
  ElMain,
  ElMenu,
  ElMenuItem,
  ElOption,
  ElPagination,
  ElProgress,
  ElRadio,
  ElRadioButton,
  ElRadioGroup,
  ElRow,
  ElSelect,
  ElSwitch,
  ElTable,
  ElTableColumn,
  ElTag,
  ElTimeline,
  ElTimelineItem,
  ElTooltip,
  ElUpload,
} from 'element-plus'
import 'element-plus/dist/index.css'
import 'element-plus/theme-chalk/dark/css-vars.css'
import './assets/global.css'

import App from './App.vue'
import router from './router'

const app = createApp(App)
app.use(createPinia())
app.use(router)
const elementComponents = [
  ElAside, ElBadge, ElButton, ElCalendar, ElCard, ElCol, ElCollapse,
  ElCollapseItem, ElColorPicker, ElConfigProvider, ElContainer, ElDatePicker,
  ElDialog, ElDropdown, ElDropdownItem, ElDropdownMenu, ElEmpty, ElForm,
  ElFormItem, ElHeader, ElIcon, ElInput, ElInputNumber, ElMain, ElMenu,
  ElMenuItem, ElOption, ElPagination, ElProgress, ElRadio, ElRadioButton,
  ElRadioGroup, ElRow, ElSelect, ElSwitch, ElTable, ElTableColumn, ElTag,
  ElTimeline, ElTimelineItem, ElTooltip, ElUpload,
]
elementComponents.forEach((component) => app.use(component))
app.use(ElLoading)
app.mount('#app')
