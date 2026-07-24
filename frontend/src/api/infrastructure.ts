import api from '../composables/useApi'

export interface ServerRecord {
  id: number
  name: string
  host: string
  provider?: string | null
  region?: string | null
  operating_system?: string | null
  ssh_port: number
  username?: string | null
  notes?: string | null
  is_active: boolean
  service_count: number
}

export interface DeployedServiceRecord {
  id: number
  name: string
  domain: string
  server_id: number
  server_name: string
  protocol: 'http' | 'https' | 'tcp' | 'udp'
  internal_host: string
  internal_port: number
  container_name?: string | null
  notes?: string | null
  is_active: boolean
}

export function getInfrastructureOverview() {
  return api.get<{ servers: ServerRecord[]; services: DeployedServiceRecord[] }>('/infrastructure/overview')
}

export function createServer(data: Record<string, any>) {
  return api.post('/infrastructure/servers', data)
}

export function updateServer(id: number, data: Record<string, any>) {
  return api.put(`/infrastructure/servers/${id}`, data)
}

export function deleteServer(id: number) {
  return api.delete(`/infrastructure/servers/${id}`)
}

export function createDeployedService(data: Record<string, any>) {
  return api.post('/infrastructure/services', data)
}

export function updateDeployedService(id: number, data: Record<string, any>) {
  return api.put(`/infrastructure/services/${id}`, data)
}

export function deleteDeployedService(id: number) {
  return api.delete(`/infrastructure/services/${id}`)
}
