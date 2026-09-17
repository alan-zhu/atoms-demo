export type TemplateType = 'landing' | 'project' | 'event'

export interface AgentStep {
  agent: string
  role: string
  content: string
}

export interface ChatMessage {
  id: string
  role: 'user' | 'agent'
  agent: string | null
  content: string
  created_at: string
}

export interface Version {
  number: number
  summary: string
  created_at: string
}

export interface AppRecord {
  id: string
  record_type: 'task' | 'contact' | 'registration'
  payload: Record<string, string>
  created_at: string
}

export interface Project {
  id: string
  owner_id: string | null
  name: string
  template_type: TemplateType
  prompt: string
  app_config: Record<string, unknown>
  is_published: boolean
  share_token: string | null
  current_version: number
  created_at: string
  updated_at: string
  messages: ChatMessage[]
  versions: Version[]
  records: AppRecord[]
  timeline: AgentStep[]
}

export type AppEvent = {
  type: 'contact' | 'task_create' | 'task_update' | 'task_delete' | 'registration'
  payload: Record<string, string>
}
