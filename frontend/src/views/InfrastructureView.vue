<template>
  <div v-loading="loading" class="infrastructure-page">
    <div class="page-header">
      <div>
        <h2>{{ zhCN.infrastructure.title }}</h2>
        <p class="page-subtitle">{{ zhCN.infrastructure.subtitle }}</p>
      </div>
      <div class="header-actions">
        <el-button @click="openServerDialog()">{{ zhCN.infrastructure.addServer }}</el-button>
        <el-button type="primary" :disabled="!servers.length" @click="openServiceDialog()">
          {{ zhCN.infrastructure.addService }}
        </el-button>
      </div>
    </div>

    <div class="stat-grid">
      <div class="stat-box stat-server">
        <span class="stat-label">{{ zhCN.infrastructure.serverCount }}</span>
        <strong>{{ servers.length }}</strong>
      </div>
      <div class="stat-box stat-service">
        <span class="stat-label">{{ zhCN.infrastructure.serviceCount }}</span>
        <strong>{{ services.length }}</strong>
      </div>
      <div class="stat-box stat-active">
        <span class="stat-label">{{ zhCN.infrastructure.activeServiceCount }}</span>
        <strong>{{ activeServiceCount }}</strong>
      </div>
    </div>

    <div class="section-heading">
      <h3>{{ zhCN.infrastructure.servers }}</h3>
    </div>
    <el-empty v-if="!servers.length" :description="zhCN.infrastructure.noServerTip" />
    <div v-else class="server-grid">
      <el-card v-for="server in servers" :key="server.id" class="server-card" shadow="hover">
        <div class="server-card-header">
          <div class="server-title-wrap">
            <span class="status-dot" :class="{ off: !server.is_active }" />
            <div>
              <div class="server-name">{{ server.name }}</div>
              <div class="server-host">{{ server.host }}:{{ server.ssh_port }}</div>
            </div>
          </div>
          <div class="card-actions">
            <el-button link type="primary" @click="openServiceDialog(undefined, server.id)">{{ zhCN.infrastructure.addService }}</el-button>
            <el-button link @click="openServerDialog(server)">{{ zhCN.common.edit }}</el-button>
            <el-button link type="danger" @click="handleDeleteServer(server)">{{ zhCN.common.delete }}</el-button>
          </div>
        </div>
        <div class="server-meta">
          <span v-if="server.provider">{{ server.provider }}</span>
          <span v-if="server.region">{{ server.region }}</span>
          <span v-if="server.operating_system">{{ server.operating_system }}</span>
          <span v-if="server.username">{{ server.username }}</span>
        </div>
        <div class="server-footer">
          <el-tag size="small" :type="server.is_active ? 'success' : 'info'">
            {{ server.is_active ? zhCN.infrastructure.active : zhCN.infrastructure.inactive }}
          </el-tag>
          <span class="service-count">{{ zhCN.infrastructure.serviceUnit.replace('{count}', String(server.service_count)) }}</span>
        </div>
      </el-card>
    </div>

    <div class="section-heading service-heading">
      <h3>{{ zhCN.infrastructure.services }}</h3>
      <div class="service-filters">
        <el-input v-model="searchText" clearable :placeholder="zhCN.infrastructure.searchPlaceholder" />
        <el-select v-model="serverFilter" clearable :placeholder="zhCN.infrastructure.filterAllServers">
          <el-option v-for="server in servers" :key="server.id" :label="server.name" :value="server.id" />
        </el-select>
      </div>
    </div>

    <el-table :data="filteredServices" stripe>
      <el-table-column prop="name" :label="zhCN.infrastructure.serviceName" min-width="150">
        <template #default="{ row }">
          <div class="service-name-cell">
            <span class="status-dot" :class="{ off: !row.is_active }" />
            <div>
              <strong>{{ row.name }}</strong>
              <small v-if="row.container_name">{{ row.container_name }}</small>
            </div>
          </div>
        </template>
      </el-table-column>
      <el-table-column prop="domain" :label="zhCN.infrastructure.domain" min-width="220">
        <template #default="{ row }">
          <a v-if="row.protocol === 'http' || row.protocol === 'https'" class="domain-link" :href="publicUrl(row)" target="_blank" rel="noopener noreferrer">
            {{ row.domain }}
          </a>
          <span v-else>{{ row.domain }}</span>
          <el-tag class="protocol-tag" size="small" type="info">{{ row.protocol.toUpperCase() }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="server_name" :label="zhCN.infrastructure.server" min-width="150" />
      <el-table-column :label="zhCN.infrastructure.mapping" min-width="210">
        <template #default="{ row }">
          <code class="mapping-code">{{ row.internal_host }}:{{ row.internal_port }}</code>
          <el-button link type="primary" @click="copyMapping(row)">{{ zhCN.infrastructure.copyMapping }}</el-button>
        </template>
      </el-table-column>
      <el-table-column prop="notes" :label="zhCN.infrastructure.notes" min-width="140" show-overflow-tooltip />
      <el-table-column width="130" fixed="right">
        <template #default="{ row }">
          <el-button link @click="openServiceDialog(row)">{{ zhCN.common.edit }}</el-button>
          <el-button link type="danger" @click="handleDeleteService(row)">{{ zhCN.common.delete }}</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="serverDialogVisible" :title="editingServerId ? zhCN.infrastructure.editServer : zhCN.infrastructure.addServer" width="520px">
      <el-form label-width="120px">
        <el-form-item :label="zhCN.infrastructure.serverName" required>
          <el-input v-model="serverForm.name" :placeholder="zhCN.infrastructure.serverNamePlaceholder" />
        </el-form-item>
        <el-form-item :label="zhCN.infrastructure.host" required>
          <el-input v-model="serverForm.host" :placeholder="zhCN.infrastructure.hostPlaceholder" />
        </el-form-item>
        <el-form-item :label="zhCN.infrastructure.provider">
          <el-input v-model="serverForm.provider" :placeholder="zhCN.infrastructure.providerPlaceholder" />
        </el-form-item>
        <el-form-item :label="zhCN.infrastructure.region">
          <el-input v-model="serverForm.region" :placeholder="zhCN.infrastructure.regionPlaceholder" />
        </el-form-item>
        <el-form-item :label="zhCN.infrastructure.operatingSystem">
          <el-input v-model="serverForm.operating_system" :placeholder="zhCN.infrastructure.operatingSystemPlaceholder" />
        </el-form-item>
        <el-form-item :label="zhCN.infrastructure.sshPort">
          <el-input-number v-model="serverForm.ssh_port" :min="1" :max="65535" />
        </el-form-item>
        <el-form-item :label="zhCN.infrastructure.username">
          <el-input v-model="serverForm.username" :placeholder="zhCN.infrastructure.usernamePlaceholder" />
        </el-form-item>
        <el-form-item :label="zhCN.infrastructure.notes">
          <el-input v-model="serverForm.notes" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item :label="zhCN.infrastructure.active">
          <el-switch v-model="serverForm.is_active" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="serverDialogVisible = false">{{ zhCN.common.cancel }}</el-button>
        <el-button type="primary" :loading="saving" @click="saveServer">{{ zhCN.common.save }}</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="serviceDialogVisible" :title="editingServiceId ? zhCN.infrastructure.editService : zhCN.infrastructure.addService" width="540px">
      <el-form label-width="110px">
        <el-form-item :label="zhCN.infrastructure.serviceName" required>
          <el-input v-model="serviceForm.name" :placeholder="zhCN.infrastructure.serviceNamePlaceholder" />
        </el-form-item>
        <el-form-item :label="zhCN.infrastructure.domain" required>
          <el-input v-model="serviceForm.domain" :placeholder="zhCN.infrastructure.domainPlaceholder">
            <template #prepend>{{ serviceForm.protocol }}://</template>
          </el-input>
        </el-form-item>
        <el-form-item :label="zhCN.infrastructure.server" required>
          <el-select v-model="serviceForm.server_id" style="width: 100%">
            <el-option v-for="server in servers" :key="server.id" :label="`${server.name} · ${server.host}`" :value="server.id" />
          </el-select>
        </el-form-item>
        <el-form-item :label="zhCN.infrastructure.protocol">
          <el-select v-model="serviceForm.protocol" style="width: 140px">
            <el-option label="HTTPS" value="https" />
            <el-option label="HTTP" value="http" />
            <el-option label="TCP" value="tcp" />
            <el-option label="UDP" value="udp" />
          </el-select>
        </el-form-item>
        <el-form-item :label="zhCN.infrastructure.internalHost" required>
          <el-input v-model="serviceForm.internal_host" :placeholder="zhCN.infrastructure.internalHostPlaceholder" />
        </el-form-item>
        <el-form-item :label="zhCN.infrastructure.internalPort" required>
          <el-input-number v-model="serviceForm.internal_port" :min="1" :max="65535" style="width: 180px" />
        </el-form-item>
        <el-form-item :label="zhCN.infrastructure.containerName">
          <el-input v-model="serviceForm.container_name" :placeholder="zhCN.infrastructure.containerNamePlaceholder" />
        </el-form-item>
        <el-form-item :label="zhCN.infrastructure.notes">
          <el-input v-model="serviceForm.notes" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item :label="zhCN.infrastructure.active">
          <el-switch v-model="serviceForm.is_active" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="serviceDialogVisible = false">{{ zhCN.common.cancel }}</el-button>
        <el-button type="primary" :loading="saving" @click="saveService">{{ zhCN.common.save }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  createDeployedService,
  createServer,
  deleteDeployedService,
  deleteServer,
  getInfrastructureOverview,
  updateDeployedService,
  updateServer,
  type DeployedServiceRecord,
  type ServerRecord,
} from '../api/infrastructure'
import { zhCN } from '../locales/zh-CN'

const servers = ref<ServerRecord[]>([])
const services = ref<DeployedServiceRecord[]>([])
const loading = ref(false)
const saving = ref(false)
const searchText = ref('')
const serverFilter = ref<number | null>(null)
const serverDialogVisible = ref(false)
const serviceDialogVisible = ref(false)
const editingServerId = ref<number | null>(null)
const editingServiceId = ref<number | null>(null)

const defaultServerForm = {
  name: '', host: '', provider: '', region: '', operating_system: '', ssh_port: 22,
  username: '', notes: '', is_active: true,
}
const serverForm = reactive({ ...defaultServerForm })

const defaultServiceForm = {
  name: '', domain: '', server_id: null as number | null, protocol: 'https' as 'http' | 'https' | 'tcp' | 'udp',
  internal_host: '127.0.0.1', internal_port: 8080, container_name: '', notes: '', is_active: true,
}
const serviceForm = reactive({ ...defaultServiceForm })

const activeServiceCount = computed(() => services.value.filter(service => service.is_active).length)
const filteredServices = computed(() => {
  const keyword = searchText.value.trim().toLowerCase()
  return services.value.filter((service) => {
    if (serverFilter.value && service.server_id !== serverFilter.value) return false
    if (!keyword) return true
    return [service.name, service.domain, service.server_name, service.internal_host, String(service.internal_port), service.container_name]
      .some(value => value?.toLowerCase().includes(keyword))
  })
})

async function fetchOverview() {
  loading.value = true
  try {
    const response = await getInfrastructureOverview()
    servers.value = response.data.servers
    services.value = response.data.services
  } finally {
    loading.value = false
  }
}

function openServerDialog(server?: ServerRecord) {
  editingServerId.value = server?.id ?? null
  Object.assign(serverForm, defaultServerForm)
  if (server) {
    Object.assign(serverForm, {
      name: server.name,
      host: server.host,
      provider: server.provider || '',
      region: server.region || '',
      operating_system: server.operating_system || '',
      ssh_port: server.ssh_port,
      username: server.username || '',
      notes: server.notes || '',
      is_active: server.is_active,
    })
  }
  serverDialogVisible.value = true
}

function openServiceDialog(service?: DeployedServiceRecord, serverId?: number) {
  if (!servers.value.length) {
    ElMessage.warning(zhCN.infrastructure.noServerTip)
    return
  }
  editingServiceId.value = service?.id ?? null
  Object.assign(serviceForm, defaultServiceForm)
  serviceForm.server_id = serverId ?? servers.value[0].id
  if (service) {
    Object.assign(serviceForm, {
      name: service.name,
      domain: service.domain,
      server_id: service.server_id,
      protocol: service.protocol,
      internal_host: service.internal_host,
      internal_port: service.internal_port,
      container_name: service.container_name || '',
      notes: service.notes || '',
      is_active: service.is_active,
    })
  }
  serviceDialogVisible.value = true
}

async function saveServer() {
  if (!serverForm.name.trim() || !serverForm.host.trim()) {
    ElMessage.warning(zhCN.infrastructure.requiredTip)
    return
  }
  saving.value = true
  try {
    if (editingServerId.value) await updateServer(editingServerId.value, serverForm)
    else await createServer(serverForm)
    ElMessage.success(zhCN.common.success)
    serverDialogVisible.value = false
    await fetchOverview()
  } finally {
    saving.value = false
  }
}

async function saveService() {
  if (!serviceForm.name.trim() || !serviceForm.domain.trim() || !serviceForm.server_id || !serviceForm.internal_host.trim() || !serviceForm.internal_port) {
    ElMessage.warning(zhCN.infrastructure.requiredTip)
    return
  }
  saving.value = true
  try {
    if (editingServiceId.value) await updateDeployedService(editingServiceId.value, serviceForm)
    else await createDeployedService(serviceForm)
    ElMessage.success(zhCN.common.success)
    serviceDialogVisible.value = false
    await fetchOverview()
  } finally {
    saving.value = false
  }
}

async function handleDeleteServer(server: ServerRecord) {
  try {
    await ElMessageBox.confirm(
      zhCN.infrastructure.deleteServerConfirm.replace('{name}', server.name),
      zhCN.common.confirm,
      { type: 'warning' },
    )
    await deleteServer(server.id)
    ElMessage.success(zhCN.common.success)
    await fetchOverview()
  } catch {}
}

async function handleDeleteService(service: DeployedServiceRecord) {
  try {
    await ElMessageBox.confirm(
      zhCN.infrastructure.deleteServiceConfirm.replace('{name}', service.name),
      zhCN.common.confirm,
      { type: 'warning' },
    )
    await deleteDeployedService(service.id)
    ElMessage.success(zhCN.common.success)
    await fetchOverview()
  } catch {}
}

function publicUrl(service: DeployedServiceRecord) {
  return `${service.protocol}://${service.domain}`
}

async function copyMapping(service: DeployedServiceRecord) {
  const mapping = `${service.internal_host}:${service.internal_port}`
  if (navigator.clipboard) {
    await navigator.clipboard.writeText(mapping)
  } else {
    const input = document.createElement('textarea')
    input.value = mapping
    input.style.position = 'fixed'
    input.style.opacity = '0'
    document.body.appendChild(input)
    input.select()
    document.execCommand('copy')
    input.remove()
  }
  ElMessage.success(zhCN.infrastructure.copied)
}

onMounted(fetchOverview)
</script>

<style scoped>
.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 20px;
}
.page-header h2 { margin-bottom: 4px; }
.page-subtitle { color: var(--text-muted); font-size: 14px; }
.header-actions { display: flex; gap: 8px; }
.stat-grid { display: grid; grid-template-columns: repeat(3, minmax(150px, 1fr)); gap: 14px; margin-bottom: 26px; }
.stat-box {
  display: flex;
  flex-direction: column;
  gap: 5px;
  padding: 18px 20px;
  border-radius: 14px;
  background: var(--surface);
  box-shadow: var(--card-shadow);
  border-left: 4px solid #6366f1;
}
.stat-box strong { font-size: 27px; color: var(--text-primary); }
.stat-label { color: var(--text-muted); font-size: 13px; }
.stat-service { border-left-color: #06b6d4; }
.stat-active { border-left-color: #10b981; }
.section-heading { display: flex; align-items: center; justify-content: space-between; margin: 0 0 12px; }
.section-heading h3 { margin: 0; color: var(--text-primary); }
.server-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 14px; }
.server-card { background: var(--surface); }
.server-card-header { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; }
.server-title-wrap { display: flex; align-items: flex-start; gap: 10px; min-width: 0; }
.status-dot { width: 9px; height: 9px; margin-top: 7px; border-radius: 50%; background: #10b981; box-shadow: 0 0 0 4px rgba(16,185,129,.12); flex: 0 0 auto; }
.status-dot.off { background: #94a3b8; box-shadow: 0 0 0 4px rgba(148,163,184,.12); }
.server-name { font-size: 16px; font-weight: 700; color: var(--text-primary); }
.server-host { margin-top: 3px; color: var(--text-muted); font-size: 13px; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }
.card-actions { display: flex; flex-wrap: wrap; justify-content: flex-end; }
.server-meta { min-height: 24px; display: flex; flex-wrap: wrap; gap: 7px; margin: 16px 0; }
.server-meta span { padding: 4px 8px; border-radius: 6px; background: var(--surface-secondary); color: var(--text-secondary); font-size: 12px; }
.server-footer { display: flex; align-items: center; justify-content: space-between; padding-top: 12px; border-top: 1px solid rgba(148,163,184,.14); }
.service-count { color: var(--text-muted); font-size: 13px; }
.service-heading { margin-top: 28px; }
.service-filters { display: flex; gap: 10px; width: min(560px, 60%); }
.service-filters .el-input { flex: 1; }
.service-filters .el-select { width: 190px; }
.service-name-cell { display: flex; align-items: flex-start; gap: 10px; }
.service-name-cell strong { display: block; color: var(--text-primary); }
.service-name-cell small { display: block; margin-top: 3px; color: var(--text-muted); }
.domain-link { color: var(--primary); text-decoration: none; font-weight: 600; }
.domain-link:hover { text-decoration: underline; }
.protocol-tag { margin-left: 8px; }
.mapping-code { display: inline-block; margin-right: 8px; padding: 4px 7px; border-radius: 6px; background: var(--surface-secondary); color: var(--text-secondary); }

@media (max-width: 767px) {
  .page-header, .section-heading { flex-direction: column; align-items: stretch; }
  .header-actions .el-button { flex: 1; }
  .stat-grid { grid-template-columns: 1fr; }
  .server-grid { grid-template-columns: 1fr; }
  .service-filters { width: 100%; flex-direction: column; }
  .service-filters .el-select { width: 100%; }
}
</style>
