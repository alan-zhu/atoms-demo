import * as Dialog from '@radix-ui/react-dialog'
import {
  AlertCircle, ArrowUp, ArrowUpRight, Bell, Check, CheckCircle2, ChevronDown, Circle,
  Clock3, Copy, FolderPlus, Gift, Globe2, Home, LoaderCircle,
  MessageSquare, Mic, Monitor, PanelLeft, Plus,
  Settings, Share2, Sparkles, TerminalSquare, UserRound, Users, X
} from 'lucide-react'
import { FormEvent, useEffect, useMemo, useRef, useState } from 'react'
import { Navigate, Route, Routes, useNavigate, useParams } from 'react-router-dom'
import { api } from './lib/api'
import { cn, formatTime } from './lib/utils'
import type { AppEvent, Project } from './types'

type DiscoverItem = { id: string; title: string; author: string; category: string; desc: string; gradient: string; emoji: string; uses: number }

const discoverItems: DiscoverItem[] = [
  { id: 'd1', title: 'SaaS 产品落地页', author: 'Emily', category: '营销', desc: '高转化率的产品落地页，含套餐对比与预约演示', gradient: 'from-violet-500 to-fuchsia-400', emoji: '🚀', uses: 2840 },
  { id: 'd2', title: '项目管理看板', author: 'Marcus', category: '工具', desc: '看板式任务管理，支持拖拽与状态流转', gradient: 'from-sky-500 to-cyan-400', emoji: '📋', uses: 1920 },
  { id: 'd3', title: '活动报名页', author: 'Sofia', category: '活动', desc: '多场次报名系统，自动统计名额与提醒', gradient: 'from-orange-400 to-amber-300', emoji: '🎉', uses: 1560 },
  { id: 'd4', title: '个人作品集', author: 'Yuki', category: '展示', desc: '极简风格作品集，项目卡片与联系表单', gradient: 'from-emerald-500 to-teal-400', emoji: '🎨', uses: 3210 },
  { id: 'd5', title: '电商商品页', author: 'David', category: '电商', desc: '商品详情、规格选择与加购流程', gradient: 'from-rose-500 to-pink-400', emoji: '🛍️', uses: 2150 },
  { id: 'd6', title: '社区论坛', author: 'Linda', category: '社区', desc: '帖子列表、话题分类与实时互动', gradient: 'from-indigo-500 to-blue-400', emoji: '💬', uses: 980 },
  { id: 'd7', title: '知识库 Wiki', author: 'Tom', category: '工具', desc: '文档树形导航、全文搜索与版本管理', gradient: 'from-teal-500 to-green-400', emoji: '📚', uses: 1340 },
  { id: 'd8', title: '餐厅点餐系统', author: 'Anna', category: '生活', desc: '菜单分类、购物车与在线下单', gradient: 'from-amber-500 to-yellow-400', emoji: '🍜', uses: 760 },
  { id: 'd9', title: '数据看板', author: 'Kevin', category: '工具', desc: '实时数据可视化，多维度图表展示', gradient: 'from-purple-500 to-violet-400', emoji: '📊', uses: 1680 },
  { id: 'd10', title: '课程平台', author: 'Rachel', category: '教育', desc: '课程目录、视频播放与进度追踪', gradient: 'from-cyan-500 to-sky-400', emoji: '🎓', uses: 2050 },
  { id: 'd11', title: '招聘官网', author: 'James', category: '展示', desc: '职位列表、团队介绍与简历投递', gradient: 'from-slate-500 to-zinc-400', emoji: '💼', uses: 890 },
  { id: 'd12', title: '活动倒计时', author: 'Nora', category: '活动', desc: '倒计时组件、日程安排与嘉宾介绍', gradient: 'from-red-500 to-orange-400', emoji: '⏰', uses: 1120 },
]

const discoverCategories = ['全部', '营销', '工具', '活动', '展示', '电商', '社区', '生活', '教育']

const agentConfig: Record<string, { initial: string; gradient: string; ring: string; role: string; tagline: string }> = {
  Emma: { initial: 'E', gradient: 'from-violet-500 to-fuchsia-500', ring: '#c4b5fd', role: '产品经理', tagline: '将想法转化为清晰的规格和范围' },
  Iris: { initial: 'I', gradient: 'from-sky-500 to-cyan-400', ring: '#7dd3fc', role: '体验研究员', tagline: '提取清晰的信息层级与内容重点' },
  Bob: { initial: 'B', gradient: 'from-amber-500 to-orange-500', ring: '#fcd34d', role: '架构师', tagline: '设计可扩展的系统蓝图与数据模型' },
  Alex: { initial: 'A', gradient: 'from-emerald-500 to-teal-400', ring: '#6ee7b7', role: '工程师', tagline: '构建生产级可交互的应用界面' },
  Luna: { initial: 'L', gradient: 'from-rose-500 to-pink-500', ring: '#fda4af', role: '测试员', tagline: '验证主流程与边界状态' },
  系统: { initial: 'S', gradient: 'from-zinc-500 to-zinc-400', ring: '#a1a1aa', role: '系统', tagline: '' },
}

const teamMembers = ['Emma', 'Iris', 'Bob', 'Alex', 'Luna']

function agentAvatar(agent: string, size: number = 24) {
  const config = agentConfig[agent] ?? { initial: agent[0] ?? '?', gradient: 'from-zinc-500 to-zinc-400', ring: '#a1a1aa', role: '', tagline: '' }
  return (
    <div
      className={cn('grid shrink-0 place-items-center rounded-full bg-gradient-to-br font-semibold text-white shadow-sm', config.gradient)}
      style={{ width: size, height: size, fontSize: size * 0.4, boxShadow: `0 0 0 2px #fff, 0 0 0 4px ${config.ring}55` }}
    >
      {config.initial}
    </div>
  )
}

function App() {
  return (
    <Routes>
      <Route path="/share/:token" element={<SharedPage />} />
      <Route path="/" element={<BuilderPage />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

function BuilderPage() {
  const [user, setUser] = useState<{ id: string; email: string; name: string | null } | null>(null)
  const [projects, setProjects] = useState<Project[]>([])
  const [activeProject, setActiveProject] = useState<Project | null>(null)
  const [prompt, setPrompt] = useState('')
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)
  const [agentSteps, setAgentSteps] = useState<Project['timeline']>([])
  const [error, setError] = useState<string | null>(null)
  const [previewMode, setPreviewMode] = useState<'desktop' | 'mobile'>('desktop')
  const [shareOpen, setShareOpen] = useState(false)
  const [copied, setCopied] = useState(false)
  const [view, setView] = useState<'home' | 'discover' | 'projects'>('home')
  const [llmEnabled, setLlmEnabled] = useState(false)
  const [llmMode, setLlmMode] = useState(false)
  const [authOpen, setAuthOpen] = useState(false)
  const navigate = useNavigate()

  useEffect(() => {
    let mounted = true
    async function bootstrap() {
      try {
        // 1. 尝试恢复登录态
        const token = window.localStorage.getItem('atoms-demo-token')
        if (token) {
          try {
            const me = await api.me()
            if (!mounted) return
            setUser(me)
            const list = await api.projects()
            if (!mounted) return
            setProjects(list)
            setActiveProject(list[0] ?? null)
          } catch {
            window.localStorage.removeItem('atoms-demo-token')
          }
        }
        // 2. 未登录 → 强制打开登录弹窗（但已在"处理登录"的话不要干扰）
        if (!user && !window.localStorage.getItem('atoms-demo-token')) {
          setAuthOpen(true)
        }
        // 3. LLM 探测
        api.health().then((h) => mounted && setLlmEnabled(h.llm_enabled)).catch(() => {})
      } catch (cause) {
        if (mounted) setError(cause instanceof Error ? cause.message : '无法连接到 API 服务')
      } finally {
        if (mounted) setLoading(false)
      }
    }
    void bootstrap()
    return () => { mounted = false }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  function replaceProject(next: Project) {
    setActiveProject(next)
    setProjects((current) => [next, ...current.filter((item) => item.id !== next.id)])
  }

  async function playTimeline(project: Project) {
    setAgentSteps([])
    for (const step of project.timeline) {
      await new Promise((resolve) => window.setTimeout(resolve, 560))
      setAgentSteps((steps) => [...steps, step])
    }
    await new Promise((resolve) => window.setTimeout(resolve, 280))
    replaceProject(project)
    setAgentSteps([])
  }

  async function submitPrompt(event?: FormEvent) {
    event?.preventDefault()
    const content = prompt.trim()
    if (!content || generating) return
    // 登录用户走 JWT（request 自动带）；访客用 visitorId
    setPrompt('')
    setGenerating(true)
    setError(null)
    try {
      const project = activeProject
        ? await api.iterate(activeProject.id, content)
        : await api.create(content, llmMode)
      await playTimeline(project)
    } catch (cause) {
      setPrompt(content)
      setError(cause instanceof Error ? cause.message : '生成失败，请重试')
    } finally {
      setGenerating(false)
    }
  }

  async function selectProject(projectId: string) {
    if (generating) return
    setLoading(true)
    try {
      const project = await api.project(projectId)
      setActiveProject(project)
      navigate('/')
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : '无法打开项目')
    } finally {
      setLoading(false)
    }
  }

  async function restore(version: number) {
    if (!activeProject || generating) return
    setGenerating(true)
    try {
      replaceProject(await api.restore(activeProject.id, version))
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : '恢复版本失败')
    } finally {
      setGenerating(false)
    }
  }

  async function publish() {
    if (!activeProject) return
    try {
      const project = activeProject.is_published ? activeProject : await api.publish(activeProject.id)
      replaceProject(project)
      setShareOpen(true)
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : '发布失败')
    }
  }

  async function copyShareUrl() {
    if (!activeProject?.share_token) return
    await navigator.clipboard.writeText(`${window.location.origin}/share/${activeProject.share_token}`)
    setCopied(true)
    window.setTimeout(() => setCopied(false), 1600)
  }

  async function sendAppEvent(appEvent: AppEvent) {
    if (!activeProject) return
    try {
      replaceProject(await api.event(activeProject.id, appEvent))
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : '保存数据失败')
    }
  }

  const shareUrl = activeProject?.share_token ? `${window.location.origin}/share/${activeProject.share_token}` : ''
  const newestVersion = activeProject?.versions[activeProject.versions.length - 1]

  return (
    <main className="h-screen min-h-[680px] overflow-hidden bg-canvas text-ink selection:bg-atoms/25">
      <div className="grid h-full grid-cols-[270px_minmax(0,1fr)]">
        <aside className="flex min-h-0 flex-col bg-canvas px-3 py-3">
          {/* Workspace selector */}
          <button className="flex items-center gap-2.5 rounded-xl px-2 py-2 text-left transition hover:bg-black/[.04]">
            <div className="grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-atoms text-sm font-semibold text-white">A</div>
            <span className="min-w-0 flex-1 truncate text-sm font-medium text-ink/90">我的 Atoms</span>
            <ChevronDown size={15} className="text-ink/40" />
          </button>

          {/* Primary nav */}
          <nav className="mt-3 space-y-0.5">
            <button onClick={() => { setActiveProject(null); setView('home'); navigate('/') }} className={cn('flex h-9 w-full items-center gap-2.5 rounded-lg px-2.5 text-sm transition', !activeProject && view === 'home' ? 'bg-black/[.06] font-medium text-ink' : 'text-ink/60 hover:bg-black/[.04] hover:text-ink')}>
              <Home size={17} className="text-ink/55" />首页
            </button>
            <button onClick={() => { setActiveProject(null); setView('discover'); navigate('/') }} className={cn('flex h-9 w-full items-center gap-2.5 rounded-lg px-2.5 text-sm transition', !activeProject && view === 'discover' ? 'bg-black/[.06] font-medium text-ink' : 'text-ink/60 hover:bg-black/[.04] hover:text-ink')}>
              <Sparkles size={17} className="text-ink/55" />资源
            </button>
            <button onClick={() => { setActiveProject(null); setView('projects'); navigate('/') }} className={cn('flex h-9 w-full items-center gap-2.5 rounded-lg px-2.5 text-sm transition', !activeProject && view === 'projects' ? 'bg-black/[.06] font-medium text-ink' : 'text-ink/60 hover:bg-black/[.04] hover:text-ink')}>
              <FolderPlus size={17} className="text-ink/55" />我的项目
            </button>
          </nav>

          {/* Recent projects */}
          <div className="mt-5 px-2.5 text-xs font-medium text-ink/40">最近</div>
          <div className="mt-1 min-h-0 flex-1 space-y-0.5 overflow-y-auto pb-3">
            {loading && <div className="px-3 py-4 text-xs text-ink/40">正在加载项目…</div>}
            {!loading && projects.length === 0 && <div className="px-3 py-4 text-xs leading-5 text-ink/35">还没有项目。<br />从一个想法开始吧。</div>}
            {projects.map((project) => (
              <button key={project.id} onClick={() => void selectProject(project.id)} className={cn('group flex w-full items-center gap-2.5 rounded-lg px-2.5 py-2 text-left transition', activeProject?.id === project.id ? 'bg-atoms/[.08] text-ink' : 'text-ink/60 hover:bg-black/[.04] hover:text-ink')}>
                <FolderPlus size={15} className={cn('shrink-0', activeProject?.id === project.id ? 'text-atoms' : 'text-ink/35')} />
                <span className="min-w-0 flex-1 truncate text-[13px]">{project.name}</span>
                {project.is_published && <Globe2 size={12} className="text-emerald-600" />}
              </button>
            ))}
          </div>

          {/* Promo cards */}
          <div className="space-y-2 pb-2">
            <div className="rounded-xl bg-white p-3 shadow-card">
              <div className="flex items-center gap-2 text-[13px] font-medium text-ink/90"><Users size={15} className="text-ink/60" />加入我们的社区</div>
              <div className="mt-0.5 text-xs text-ink/45">最多可赚取 25 积分</div>
            </div>
            <div className="rounded-xl bg-white p-3 shadow-card">
              <div className="flex items-center gap-2 text-[13px] font-medium text-ink/90"><Gift size={15} className="text-ink/60" />获取免费积分</div>
              <div className="mt-0.5 text-xs text-ink/45">每人获得 10 积分</div>
            </div>
          </div>

          {/* Bottom user */}
          <div className="flex items-center gap-1 border-t border-black/[.06] pt-2">
            {user ? (
              <>
                <div className="grid h-8 w-8 place-items-center rounded-full bg-gradient-to-tr from-atoms to-violet-500 text-[13px] font-semibold text-white">
                  {(user.name ?? user.email).slice(0, 1).toUpperCase()}
                </div>
                <div className="min-w-0 flex-1 text-[12px] leading-tight">
                  <div className="truncate font-medium text-ink">{user.name ?? user.email}</div>
                  <div className="truncate text-[11px] text-ink/45">{user.email}</div>
                </div>
                <button onClick={() => { window.localStorage.removeItem('atoms-demo-token'); setUser(null); setProjects([]); setActiveProject(null); }} className="grid h-8 w-8 place-items-center rounded-lg text-ink/45 transition hover:bg-black/[.05] hover:text-ink/70" title="退出登录"><Settings size={17} /></button>
              </>
            ) : (
              <>
                <button onClick={() => setAuthOpen(true)} className="grid h-8 w-8 place-items-center rounded-full bg-gradient-to-tr from-zinc-600 to-zinc-400 text-white"><UserRound size={14} /></button>
                <button onClick={() => setAuthOpen(true)} className="ml-2 text-[12px] font-medium text-ink hover:text-atoms">登录</button>
              </>
            )}
            <button className="relative grid h-8 w-8 place-items-center rounded-lg text-ink/45 transition hover:bg-black/[.05] hover:text-ink/70"><Bell size={17} /><span className="absolute right-1.5 top-1.5 h-1.5 w-1.5 rounded-full bg-red-500" /></button>
          </div>
        </aside>

        <section className="flex min-h-0 min-w-0 flex-col">
          <header className="flex h-[60px] shrink-0 items-center justify-between px-6">
            <div className="flex min-w-0 items-center gap-3">
              <PanelLeft size={17} className="text-ink/40" />
              {activeProject ? <><span className="truncate text-sm font-medium text-ink/90">{activeProject.name}</span><span className="hidden h-1 w-1 rounded-full bg-ink/20 sm:block" /><span className="hidden text-xs text-ink/45 sm:block">v{activeProject.current_version}</span></> : <span className="text-sm text-ink/50">新的工作空间</span>}
            </div>
            {activeProject && <div className="flex items-center gap-2">
              {newestVersion && <VersionPicker versions={activeProject.versions} current={activeProject.current_version} disabled={generating} onRestore={restore} />}
              <button onClick={() => void publish()} className="hidden h-9 shrink-0 items-center gap-2 whitespace-nowrap rounded-full border border-black/[.12] bg-white px-3.5 text-xs font-medium text-ink/80 transition hover:bg-black/[.03] sm:flex">
                <Globe2 size={14} className={activeProject.is_published ? 'text-emerald-600' : 'text-ink/50'} />{activeProject.is_published ? '已发布' : '发布'}
              </button>
              <button onClick={() => void publish()} className="flex h-9 shrink-0 items-center gap-2 whitespace-nowrap rounded-full bg-atoms px-4 text-xs font-semibold text-white transition hover:bg-atoms-dark">
                <Share2 size={14} />分享
              </button>
            </div>}
          </header>

          {error && <div className="absolute right-6 top-[70px] z-50 flex max-w-md items-center gap-2 rounded-xl border border-red-200 bg-white px-3.5 py-2.5 text-xs text-red-600 shadow-pop"><AlertCircle size={15} />{error}<button onClick={() => setError(null)}><X size={14} /></button></div>}
          {loading ? <div className="grid flex-1 place-items-center text-sm text-ink/45"><LoaderCircle className="mr-2 animate-spin" size={18} />加载工作区…</div> : activeProject ? (
            <Workspace project={activeProject} prompt={prompt} onPromptChange={setPrompt} onSubmit={submitPrompt} generating={generating} agentSteps={agentSteps} previewMode={previewMode} onPreviewMode={setPreviewMode} onEvent={sendAppEvent} />
          ) : view === 'discover' ? (
            <DiscoverView onUsePrompt={(p) => { setPrompt(p); setView('home') }} />
          ) : view === 'projects' ? (
            <ProjectsView projects={projects} onSelect={selectProject} loading={loading} />
          ) : (
            <NewProject prompt={prompt} onPromptChange={setPrompt} onSubmit={submitPrompt} generating={generating} projects={projects} onSelectProject={selectProject} onGotoDiscover={() => setView('discover')} onGotoProjects={() => setView('projects')} llmEnabled={llmEnabled} llmMode={llmMode} onLlmModeChange={setLlmMode} />
          )}
        </section>
      </div>

      <Dialog.Root open={shareOpen} onOpenChange={setShareOpen}>
        <Dialog.Portal>
          <Dialog.Overlay className="fixed inset-0 z-50 bg-black/40 backdrop-blur-sm" />
          <Dialog.Content className="fixed left-1/2 top-1/2 z-50 w-[min(92vw,500px)] -translate-x-1/2 -translate-y-1/2 rounded-3xl border border-black/[.08] bg-white p-6 shadow-pop focus:outline-none">
            <Dialog.Close className="absolute right-4 top-4 grid h-8 w-8 place-items-center rounded-full text-ink/45 hover:bg-black/[.05] hover:text-ink"><X size={18} /></Dialog.Close>
            <div className="mb-4 grid h-11 w-11 place-items-center rounded-full bg-emerald-50 text-emerald-600"><CheckCircle2 size={22} /></div>
            <Dialog.Title className="text-xl font-semibold tracking-[-.02em] text-ink">你的应用已发布</Dialog.Title>
            <Dialog.Description className="mt-2 text-sm leading-6 text-ink/55">任何拿到此链接的人都能使用应用，但无法进入你的 AI 工作台。</Dialog.Description>
            <div className="mt-5 flex items-center gap-2 rounded-xl border border-black/[.1] bg-canvas p-2 pl-3.5">
              <span className="min-w-0 flex-1 truncate text-xs text-ink/60">{shareUrl}</span>
              <button onClick={() => void copyShareUrl()} className="flex shrink-0 items-center gap-1.5 rounded-lg bg-black/[.06] px-3 py-2 text-xs font-medium text-ink transition hover:bg-black/[.1]">{copied ? <Check size={14} className="text-emerald-600" /> : <Copy size={14} />}{copied ? '已复制' : '复制'}</button>
            </div>
            <a href={shareUrl} target="_blank" rel="noreferrer" className="mt-3 flex h-11 items-center justify-center gap-2 rounded-full bg-atoms text-sm font-semibold text-white transition hover:bg-atoms-dark"><ArrowUpRight size={15} />打开分享页</a>
          </Dialog.Content>
        </Dialog.Portal>
      </Dialog.Root>

      {/* Auth Dialog */}
      <Dialog.Root open={authOpen} onOpenChange={setAuthOpen}>
        <Dialog.Portal>
          <Dialog.Overlay className="fixed inset-0 z-50 bg-black/30 backdrop-blur-sm data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out data-[state=open]:fade-in" />
          <Dialog.Content className="fixed left-1/2 top-1/2 z-50 w-[380px] max-w-[92vw] -translate-x-1/2 -translate-y-1/2 rounded-3xl border border-black/[.07] bg-white p-7 shadow-[0_24px_80px_rgba(0,0,0,.15)] outline-none data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out data-[state=open]:fade-in">
            <AuthDialog onClose={() => setAuthOpen(false)} onAuth={async (result) => {
              setAuthOpen(false)
              setUser(result.user)
              setLoading(true)
              try {
                const list = await api.projects()
                setProjects(list)
                setActiveProject(list[0] ?? null)
              } catch {}
              setLoading(false)
            }} />
          </Dialog.Content>
        </Dialog.Portal>
      </Dialog.Root>
    </main>
  )
}

function AuthDialog({ onClose, onAuth }: { onClose: () => void; onAuth: (result: { token: string; user: { id: string; email: string; name: string | null } }) => void }) {
  const [mode, setMode] = useState<'login' | 'register'>('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [name, setName] = useState('')
  const [loading, setLoading] = useState(false)
  const [err, setErr] = useState<string | null>(null)

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true); setErr(null)
    try {
      const r = mode === 'login'
        ? await api.login(email, password)
        : await api.register(email, password, name || undefined)
      window.localStorage.setItem('atoms-demo-token', r.token)
      onAuth(r)
    } catch (cause) {
      setErr(cause instanceof Error ? cause.message : '操作失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <Dialog.Title className="font-display text-xl leading-tight text-ink">
        {mode === 'login' ? '欢迎回来' : '创建账号'}
      </Dialog.Title>
      <Dialog.Description className="mt-1 text-[13px] text-ink/55">
        {mode === 'login' ? '登录后继续你未完成的项目。' : '注册后你现有的访客数据会自动关联到账号。'}
      </Dialog.Description>
      <form onSubmit={submit} className="mt-5 space-y-3">
        {mode === 'register' && (
          <div>
            <label className="mb-1 block text-[12px] font-medium text-ink/55">昵称（可选）</label>
            <input value={name} onChange={(e) => setName(e.target.value)} placeholder="你希望被怎么称呼" className="h-11 w-full rounded-xl border border-black/[.08] bg-white px-3 text-[13px] outline-none transition focus:border-atoms" />
          </div>
        )}
        <div>
          <label className="mb-1 block text-[12px] font-medium text-ink/55">邮箱</label>
          <input type="email" required value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@example.com" className="h-11 w-full rounded-xl border border-black/[.08] bg-white px-3 text-[13px] outline-none transition focus:border-atoms" />
        </div>
        <div>
          <label className="mb-1 block text-[12px] font-medium text-ink/55">密码</label>
          <input type="password" required minLength={6} value={password} onChange={(e) => setPassword(e.target.value)} placeholder={mode === 'register' ? '至少 6 位' : '请输入密码'} className="h-11 w-full rounded-xl border border-black/[.08] bg-white px-3 text-[13px] outline-none transition focus:border-atoms" />
        </div>
        {err && <div className="rounded-lg bg-red-50 px-3 py-2 text-[12px] text-red-600">{err}</div>}
        <button type="submit" disabled={loading} className="mt-2 h-11 w-full rounded-xl bg-atoms text-[13px] font-semibold text-white transition hover:bg-atoms-dark disabled:opacity-50">
          {loading ? '正在处理…' : mode === 'login' ? '登录' : '注册'}
        </button>
      </form>
      <div className="mt-4 text-center text-[12px] text-ink/55">
        {mode === 'login' ? '还没有账号？' : '已经有账号了？'}
        <button onClick={() => { setMode(mode === 'login' ? 'register' : 'login'); setErr(null) }} className="ml-1 font-medium text-atoms hover:text-atoms-dark">
          {mode === 'login' ? '注册' : '登录'}
        </button>
      </div>
    </div>
  )
}

function DiscoverCard({ item, onUse }: { item: DiscoverItem; onUse?: (item: DiscoverItem) => void }) {
  return (
    <button onClick={() => onUse?.(item)} className="group overflow-hidden rounded-2xl border border-black/[.07] bg-white text-left shadow-card transition hover:shadow-pop">
      <div className={cn('relative flex h-28 items-center justify-center bg-gradient-to-br text-4xl', item.gradient)}>
        <span className="drop-shadow-sm">{item.emoji}</span>
      </div>
      <div className="p-3">
        <div className="text-xs font-semibold text-ink">{item.title}</div>
        <p className="mt-1 text-[10px] leading-[1.5] text-ink/50">{item.desc}</p>
        <div className="mt-2 flex items-center gap-1.5 text-[10px] text-ink/40"><span className="h-3 w-3 rounded-full bg-gradient-to-br from-zinc-400 to-zinc-300" />{item.author}<span className="ml-auto flex items-center gap-0.5"><Sparkles size={9} />{item.uses > 999 ? `${(item.uses / 1000).toFixed(1)}k` : item.uses}</span></div>
      </div>
    </button>
  )
}

function NewProject({ prompt, onPromptChange, onSubmit, generating, projects, onSelectProject, onGotoDiscover, onGotoProjects, llmEnabled, llmMode, onLlmModeChange }: { prompt: string; onPromptChange: (value: string) => void; onSubmit: (event?: FormEvent) => void; generating: boolean; projects: Project[]; onSelectProject: (id: string) => void; onGotoDiscover: () => void; onGotoProjects: () => void; llmEnabled: boolean; llmMode: boolean; onLlmModeChange: (v: boolean) => void }) {
  const [tab, setTab] = useState<'discover' | 'projects'>('discover')
  return <div className="relative flex flex-1 flex-col overflow-auto">
    <div className="mx-auto flex w-full max-w-3xl flex-col items-center px-6 pt-14 pb-10 text-center">
      {/* Agent avatar row */}
      <div className="mb-7 flex items-center justify-center gap-3">
        {teamMembers.map((name, i) => (
          <div key={name} className="animate-bob" style={{ animationDelay: `${i * 0.25}s` }}>
            {agentAvatar(name, 50)}
          </div>
        ))}
      </div>
      <h1 className="max-w-2xl text-[26px] font-medium leading-[1.35] tracking-[-.02em] text-ink sm:text-[32px]">让我们将你的想法变为现实。</h1>
      <div className="mt-6 w-full max-w-xl">
        <PromptBox prompt={prompt} onPromptChange={onPromptChange} onSubmit={onSubmit} generating={generating} large showLlmToggle={llmEnabled} llmMode={llmMode} onLlmModeChange={onLlmModeChange} />
      </div>
    </div>

    {/* Tabbed content: 发现 / 我的项目 */}
    <div className="mx-auto w-full max-w-4xl px-6 pb-14">
      {/* Tab bar */}
      <div className="mb-4 flex items-center gap-1 border-b border-black/[.08]">
        <button onClick={() => setTab('discover')} className={cn('flex items-center gap-1.5 border-b-2 px-3 pb-2.5 pt-1 text-sm transition', tab === 'discover' ? 'border-atoms font-medium text-ink' : 'border-transparent text-ink/50 hover:text-ink/80')}><Sparkles size={14} />发现</button>
        <button onClick={() => setTab('projects')} className={cn('flex items-center gap-1.5 border-b-2 px-3 pb-2.5 pt-1 text-sm transition', tab === 'projects' ? 'border-atoms font-medium text-ink' : 'border-transparent text-ink/50 hover:text-ink/80')}><FolderPlus size={14} />我的项目</button>
        <div className="ml-auto pb-1.5">
          <button onClick={() => tab === 'discover' ? onGotoDiscover() : onGotoProjects()} className="text-[11px] text-atoms hover:underline">查看全部 →</button>
        </div>
      </div>

      {/* Tab: 发现 */}
      {tab === 'discover' && (
        <div className="grid grid-cols-2 gap-2.5 sm:grid-cols-3 lg:grid-cols-4">
          {discoverItems.slice(0, 8).map((item) => <DiscoverCard key={item.id} item={item} onUse={() => { onPromptChange(`做一个${item.title}：${item.desc}`) }} />)}
        </div>
      )}

      {/* Tab: 我的项目 */}
      {tab === 'projects' && (
        projects.length === 0 ? (
          <div className="rounded-xl border border-dashed border-black/[.1] px-4 py-12 text-center text-sm text-ink/40">还没有项目，从上方输入框开始吧。</div>
        ) : (
          <div className="grid grid-cols-2 gap-2.5 sm:grid-cols-3 lg:grid-cols-4">
            {projects.map((project) => (
              <button key={project.id} onClick={() => onSelectProject(project.id)} className="group overflow-hidden rounded-2xl border border-black/[.07] bg-white text-left shadow-card transition hover:shadow-pop">
                <div className="flex h-28 items-center justify-center bg-gradient-to-br from-atoms/15 to-atoms-soft">
                  <FolderPlus size={32} className="text-atoms/50" />
                </div>
                <div className="p-3">
                  <div className="truncate text-xs font-semibold text-ink">{project.name}</div>
                  <div className="mt-1.5 flex items-center gap-1.5 text-[10px] text-ink/40">
                    <span>v{project.current_version}</span>
                    {project.is_published && <><span className="h-1 w-1 rounded-full bg-ink/20" /><Globe2 size={9} className="text-emerald-600" />已发布</>}
                  </div>
                </div>
              </button>
            ))}
          </div>
        )
      )}
    </div>

    {/* AI team */}
    <div className="mx-auto w-full max-w-4xl px-6 pb-14">
      <div className="mb-4 flex items-center gap-3">
        <span className="text-[11px] font-medium uppercase tracking-[.16em] text-ink/40">你的 AI 团队</span>
        <div className="h-px flex-1 bg-black/[.08]" />
      </div>
      <div className="grid gap-2.5 sm:grid-cols-2 lg:grid-cols-5">
        {teamMembers.map((name) => {
          const config = agentConfig[name]
          return (
            <div key={name} className="group rounded-2xl border border-black/[.07] bg-white p-4 shadow-card transition hover:shadow-pop">
              <div className="flex items-center gap-2.5">
                {agentAvatar(name, 38)}
                <div className="min-w-0">
                  <div className="truncate text-xs font-semibold text-ink">{name}</div>
                  <div className="truncate text-[10px] text-atoms">{config.role}</div>
                </div>
              </div>
              <p className="mt-3 text-[10px] leading-[1.5] text-ink/50">{config.tagline}</p>
            </div>
          )
        })}
      </div>
    </div>
  </div>
}

function DiscoverView({ onUsePrompt }: { onUsePrompt: (prompt: string) => void }) {
  const [category, setCategory] = useState('全部')
  const filtered = category === '全部' ? discoverItems : discoverItems.filter((item) => item.category === category)
  return (
    <div className="flex flex-1 flex-col overflow-auto">
      <div className="mx-auto w-full max-w-5xl px-6 py-8">
        <h1 className="text-2xl font-semibold tracking-[-.02em] text-ink">发现</h1>
        <p className="mt-1 text-sm text-ink/50">探索社区构建的精选应用模板，一键开始你的项目。</p>
        {/* Category pills */}
        <div className="mt-5 flex flex-wrap gap-1.5">
          {discoverCategories.map((cat) => <button key={cat} onClick={() => setCategory(cat)} className={cn('rounded-full px-3 py-1.5 text-xs transition', category === cat ? 'bg-atoms text-white' : 'bg-white text-ink/60 hover:bg-black/[.05]')}>{cat}</button>)}
        </div>
        {/* Grid */}
        <div className="mt-5 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
          {filtered.map((item) => <DiscoverCard key={item.id} item={item} onUse={() => onUsePrompt(`做一个${item.title}：${item.desc}`)} />)}
        </div>
      </div>
    </div>
  )
}

function ProjectsView({ projects, onSelect, loading }: { projects: Project[]; onSelect: (id: string) => void; loading: boolean }) {
  return (
    <div className="flex flex-1 flex-col overflow-auto">
      <div className="mx-auto w-full max-w-5xl px-6 py-8">
        <h1 className="text-2xl font-semibold tracking-[-.02em] text-ink">我的项目</h1>
        <p className="mt-1 text-sm text-ink/50">所有由你创建的应用，点击即可继续迭代。</p>
        {loading ? (
          <div className="mt-8 flex items-center gap-2 text-sm text-ink/45"><LoaderCircle size={16} className="animate-spin" />加载中…</div>
        ) : projects.length === 0 ? (
          <div className="mt-8 rounded-xl border border-dashed border-black/[.1] px-4 py-16 text-center text-sm text-ink/40">还没有项目。<br />回到首页，从一个想法开始吧。</div>
        ) : (
          <div className="mt-5 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
            {projects.map((project) => (
              <button key={project.id} onClick={() => onSelect(project.id)} className="group overflow-hidden rounded-2xl border border-black/[.07] bg-white text-left shadow-card transition hover:shadow-pop">
                <div className="flex h-28 items-center justify-center bg-gradient-to-br from-atoms/15 to-atoms-soft">
                  <FolderPlus size={32} className="text-atoms/50" />
                </div>
                <div className="p-3">
                  <div className="truncate text-xs font-semibold text-ink">{project.name}</div>
                  <div className="mt-1.5 flex items-center gap-1.5 text-[10px] text-ink/40">
                    <span>v{project.current_version}</span>
                    {project.is_published && <><span className="h-1 w-1 rounded-full bg-ink/20" /><Globe2 size={9} className="text-emerald-600" />已发布</>}
                  </div>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

function Workspace({ project, prompt, onPromptChange, onSubmit, generating, agentSteps, previewMode, onPreviewMode, onEvent }: { project: Project; prompt: string; onPromptChange: (value: string) => void; onSubmit: (event?: FormEvent) => void; generating: boolean; agentSteps: Project['timeline']; previewMode: 'desktop' | 'mobile'; onPreviewMode: (mode: 'desktop' | 'mobile') => void; onEvent: (event: AppEvent) => void }) {
  const messages = useMemo(() => project.messages.slice(-14), [project.messages])
  const chatEndRef = useRef<HTMLDivElement>(null)
  useEffect(() => { chatEndRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' }) }, [messages, agentSteps])
  const [rightTab, setRightTab] = useState<'preview' | 'code'>('preview')
  const [codeHtml, setCodeHtml] = useState<string | null>(null)
  const [codeLoading, setCodeLoading] = useState(false)
  useEffect(() => { setCodeHtml(null) }, [project.id, project.current_version])
  useEffect(() => {
    if (rightTab !== 'code' || codeHtml !== null) return
    setCodeLoading(true)
    api.projectHtml(project.id).then(r => setCodeHtml(r.html)).catch(() => setCodeHtml(null)).finally(() => setCodeLoading(false))
  }, [rightTab, project.id, project.current_version, codeHtml])
  return <div className="grid min-h-0 flex-1 grid-cols-1 xl:grid-cols-[minmax(360px,.82fr)_minmax(520px,1.18fr)]">
    <section className="flex min-h-[360px] xl:min-h-0 min-w-0 flex-col border-b border-black/[.08] bg-white xl:border-b-0 xl:border-r">
      <div className="flex shrink-0 items-center justify-between border-b border-black/[.07] px-5 py-3"><div className="flex items-center gap-2.5 text-xs font-medium text-ink/70"><MessageSquare size={14} className="text-atoms" />与 Atoms 团队对话<div className="ml-1 flex -space-x-1.5">{teamMembers.map((name) => <div key={name} className="ring-2 ring-white">{agentAvatar(name, 20)}</div>)}</div></div><span className="flex items-center gap-1 rounded-full bg-emerald-50 px-2 py-1 text-[10px] text-emerald-600"><span className="h-1 w-1 rounded-full bg-emerald-500" />已保存</span></div>
      <div className="min-h-0 flex-1 space-y-4 overflow-y-auto bg-canvas/60 px-5 py-5">
        {messages.map((message) => <ChatBubble key={message.id} message={message} />)}
        {agentSteps.map((step, index) => <AgentProgress key={`${step.agent}-${index}`} step={step} active={index === agentSteps.length - 1} />)}
        {generating && agentSteps.length === 0 && <div className="flex items-center gap-2 text-xs text-ink/45"><LoaderCircle size={14} className="animate-spin text-atoms" />正在分配 Agent…</div>}
        <div ref={chatEndRef} />
      </div>
      <div className="shrink-0 border-t border-black/[.07] bg-white p-4"><PromptBox prompt={prompt} onPromptChange={onPromptChange} onSubmit={onSubmit} generating={generating} compact /><p className="mt-2 px-1 text-[10px] text-ink/35">试试："改成蓝色、增加更多留白、让文案更年轻"</p></div>
    </section>
    <section className="flex min-h-0 min-w-0 flex-col bg-canvas">
      <div className="flex h-[49px] shrink-0 items-center justify-between border-b border-black/[.07] px-4">
        <div className="flex items-center gap-1 rounded-lg bg-black/[.05] p-0.5">
          <button onClick={() => setRightTab('preview')} className={cn('grid h-6 place-items-center rounded-md px-3 text-[11px] font-medium transition', rightTab === 'preview' ? 'bg-white text-ink shadow-sm' : 'text-ink/40 hover:text-ink/70')}>Preview</button>
          <button onClick={() => setRightTab('code')} className={cn('grid h-6 place-items-center rounded-md px-3 text-[11px] font-medium transition', rightTab === 'code' ? 'bg-white text-ink shadow-sm' : 'text-ink/40 hover:text-ink/70')}>Code</button>
        </div>
        {rightTab === 'preview' ? (
          <div className="flex items-center gap-1 rounded-lg bg-black/[.05] p-0.5">
            <button onClick={() => onPreviewMode('desktop')} className={cn('grid h-6 w-7 place-items-center rounded-md transition', previewMode === 'desktop' ? 'bg-white text-ink shadow-sm' : 'text-ink/40 hover:text-ink/70')}><Monitor size={13} /></button>
            <button onClick={() => onPreviewMode('mobile')} className={cn('grid h-6 w-7 place-items-center rounded-md transition', previewMode === 'mobile' ? 'bg-white text-ink shadow-sm' : 'text-ink/40 hover:text-ink/70')}><PanelLeft size={13} className="rotate-90" /></button>
          </div>
        ) : <div />}
        <div className="flex items-center gap-2 text-[11px] text-ink/50"><span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />{rightTab === 'preview' ? '实时预览' : '源码'}</div>
        <div className="w-[74px]" />
      </div>
      <div className="min-h-0 flex-1 overflow-auto p-4 sm:p-6">
        {rightTab === 'preview' ? (
          <div className={cn('mx-auto min-h-full overflow-hidden rounded-2xl border border-black/[.1] bg-white shadow-pop transition-all', previewMode === 'mobile' ? 'w-[375px] max-w-full' : 'w-full')}><GeneratedApp project={project} onEvent={onEvent} /></div>
        ) : (
          <CodeViewer code={codeHtml} loading={codeLoading} />
        )}
      </div>
    </section>
  </div>
}

function PromptBox({ prompt, onPromptChange, onSubmit, generating, large = false, compact = false, llmMode = false, onLlmModeChange, showLlmToggle = false }: { prompt: string; onPromptChange: (value: string) => void; onSubmit: (event?: FormEvent) => void; generating: boolean; large?: boolean; compact?: boolean; llmMode?: boolean; onLlmModeChange?: (v: boolean) => void; showLlmToggle?: boolean }) {
  function handleKeyDown(event: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === 'Enter' && (event.metaKey || event.ctrlKey)) {
      event.preventDefault()
      if (prompt.trim() && !generating) onSubmit()
    }
  }
  const canSend = prompt.trim() && !generating
  return <form onSubmit={(e) => { e.preventDefault(); if (canSend) onSubmit() }} className={cn('rounded-3xl border border-black/[.12] bg-white p-3 shadow-card transition focus-within:border-atoms/50 focus-within:shadow-pop', compact && 'rounded-2xl p-2.5', large && 'w-full')}>
    <textarea value={prompt} onChange={(event) => onPromptChange(event.target.value)} onKeyDown={handleKeyDown} rows={large ? 3 : 2} placeholder={compact ? '描述下一步修改…（⌘/Ctrl+↵ 发送）' : '描述你想构建的产品，例如：为独立设计师做一个作品集与服务预约网站'} className={cn('w-full resize-none bg-transparent px-2 pb-2 text-sm leading-6 text-ink placeholder:text-ink/35 focus:outline-none', compact && 'text-[13px]')} />
    <div className="flex items-center justify-between px-1">
      <div className="flex items-center gap-1.5">
        <button type="button" className="grid h-8 w-8 place-items-center rounded-full text-ink/50 transition hover:bg-black/[.05]"><Plus size={18} /></button>
        <button type="button" className="flex h-8 items-center gap-1 rounded-full px-2.5 text-[13px] font-medium text-ink/70 transition hover:bg-black/[.05]">构建 <ChevronDown size={13} /></button>
      </div>
      <div className="flex items-center gap-1.5">
        {showLlmToggle && <button type="button" onClick={() => onLlmModeChange?.(!llmMode)} className={cn('flex h-8 items-center gap-1 rounded-full px-2 text-[12px] font-medium transition', llmMode ? 'bg-gradient-to-br from-atoms to-violet-500 text-white shadow-sm' : 'text-ink/55 hover:bg-black/[.05]')}><Sparkles size={12} />AI 生成</button>}
        <button type="button" className="grid h-8 w-8 place-items-center rounded-full text-ink/45 transition hover:bg-black/[.05]"><Mic size={17} /></button>
        <button type="submit" disabled={!canSend} className={cn('grid h-9 w-9 place-items-center rounded-full transition', canSend ? 'bg-atoms text-white hover:bg-atoms-dark' : 'bg-black/[.06] text-ink/30')}>
          {generating ? <LoaderCircle size={17} className="animate-spin" /> : <ArrowUp size={18} strokeWidth={2.5} />}
        </button>
      </div>
    </div>
  </form>
}

function ChatBubble({ message }: { message: Project['messages'][number] }) {
  const user = message.role === 'user'
  return <div className={cn('flex gap-2.5', user && 'justify-end')}>
    {!user && message.agent && agentAvatar(message.agent, 26)}
    <div className={cn('max-w-[86%] rounded-2xl px-3.5 py-2.5 text-[12px] leading-5 shadow-card', user ? 'rounded-tr-md bg-atoms text-white' : 'rounded-tl-md border border-black/[.07] bg-white text-ink/70')}>
      {!user && message.agent && <div className="mb-1 flex items-center gap-1.5 text-[10px] font-medium text-ink"><span>{message.agent}</span><span className="text-ink/25">·</span><span className="text-atoms">{agentConfig[message.agent]?.role ?? ''}</span></div>}
      {message.content}
      <div className={cn('mt-1.5 text-[9px]', user ? 'text-white/60' : 'text-ink/35')}>{formatTime(message.created_at)}</div>
    </div>
  </div>
}

function AgentProgress({ step, active }: { step: Project['timeline'][number]; active: boolean }) {
  return <div className="flex gap-2.5 animate-in fade-in slide-in-from-bottom-1 duration-300">
    <div className="relative shrink-0">
      {agentAvatar(step.agent, 26)}
      {active && <div className="absolute -right-0.5 -bottom-0.5 grid h-3.5 w-3.5 place-items-center rounded-full bg-white"><LoaderCircle size={10} className="animate-spin text-atoms" /></div>}
      {!active && <div className="absolute -right-0.5 -bottom-0.5 grid h-3.5 w-3.5 place-items-center rounded-full bg-white"><Check size={9} className="text-emerald-500" /></div>}
    </div>
    <div className="flex-1 rounded-2xl rounded-tl-md border border-black/[.07] bg-white px-3.5 py-2.5 shadow-card"><div className="flex items-center gap-1.5"><span className="text-[11px] font-medium text-ink">{step.agent}</span><span className="text-ink/25">·</span><span className="text-[10px] text-atoms">{step.role}</span></div><p className="mt-1 text-[11px] leading-5 text-ink/55">{step.content}</p></div>
  </div>
}

function VersionPicker({ versions, current, disabled, onRestore }: { versions: Project['versions']; current: number; disabled: boolean; onRestore: (version: number) => void }) {
  const [open, setOpen] = useState(false)
  return <div className="relative">
    <button onClick={() => setOpen(!open)} className="hidden h-9 shrink-0 items-center gap-1 whitespace-nowrap rounded-full px-2 text-xs text-ink/55 hover:bg-black/[.05] sm:flex">版本 <span className="font-medium text-ink/80">v{current}</span><ChevronDown size={13} /></button>
    {open && <><button onClick={() => setOpen(false)} className="fixed inset-0 z-20 cursor-default" aria-label="关闭版本菜单" /><div className="absolute right-0 top-10 z-30 w-64 rounded-2xl border border-black/[.08] bg-white p-1.5 shadow-pop"><div className="px-2.5 py-2 text-[10px] font-medium uppercase tracking-[.12em] text-ink/40">最近版本</div>{versions.slice().reverse().map((version) => <button key={version.number} disabled={disabled || version.number === current} onClick={() => { onRestore(version.number); setOpen(false) }} className="flex w-full items-start gap-2 rounded-xl px-2.5 py-2 text-left hover:bg-black/[.04] disabled:opacity-50"><Clock3 size={13} className="mt-0.5 text-ink/40" /><span><span className="block text-xs text-ink/85">v{version.number} {version.number === current && <span className="text-atoms">当前</span>}</span><span className="mt-0.5 block text-[10px] leading-4 text-ink/45">{version.summary}</span></span></button>)}</div></>}
  </div>
}

function CodeViewer({ code, loading }: { code: string | null; loading: boolean }) {
  const [copied, setCopied] = useState(false)
  async function copy() {
    if (!code) return
    await navigator.clipboard.writeText(code)
    setCopied(true)
    window.setTimeout(() => setCopied(false), 1600)
  }
  return (
    <div className="mx-auto flex h-full min-h-[480px] flex-col overflow-hidden rounded-2xl border border-black/[.1] bg-white shadow-pop">
      <div className="flex h-9 shrink-0 items-center justify-between border-b border-black/[.07] px-4">
        <span className="flex items-center gap-1.5 text-[11px] text-ink/55">
          <TerminalSquare size={13} /> index.html · {code ? code.length : 0} 字节
        </span>
        <button onClick={() => void copy()} disabled={!code}
          className="flex items-center gap-1.5 rounded-lg bg-black/[.06] px-2.5 py-1.5 text-[11px] font-medium text-ink/80 transition hover:bg-black/[.1] disabled:opacity-40">
          {copied ? <Check size={13} className="text-emerald-600" /> : <Copy size={13} />}
          {copied ? '已复制' : '复制'}
        </button>
      </div>
      <pre className="min-h-0 flex-1 overflow-auto bg-[#0d1117] p-4 text-[11px] leading-[1.55] text-zinc-200">
        <code>{loading ? '正在生成源码…' : code ?? '暂无源码'}</code>
      </pre>
    </div>
  )
}

function SharedPage() {
  const { token } = useParams()
  const [loaded, setLoaded] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const apiBase = import.meta.env.VITE_API_URL ?? `${window.location.protocol}//${window.location.hostname}:8000`
  useEffect(() => {
    if (!token) return
    api.shared(token).catch((cause: unknown) => setError(cause instanceof Error ? cause.message : '无法打开分享页'))
  }, [token])
  if (error) return <div className="grid min-h-screen place-items-center bg-canvas text-ink/60"><div className="text-center"><AlertCircle className="mx-auto mb-3 text-red-500" /><p>{error}</p></div></div>
  if (!token) return <Navigate to="/" replace />
  return (
    <main className="relative h-screen bg-canvas">
      {!loaded && <div className="absolute inset-0 grid place-items-center text-ink/45"><LoaderCircle className="animate-spin" /></div>}
      <iframe
        src={`${apiBase}/api/share/${token}/page`}
        title="Atoms shared app"
        onLoad={() => setLoaded(true)}
        className="h-screen w-screen border-0"
      />
    </main>
  )
}

function normalizeConfig(config: any): any {
  // 把 blocks schema 或 legacy schema 都映射到旧字段（brand/style/accent/sections），让老 Preview 组件兼容新数据
  if (!config || typeof config !== 'object') return {}
  if (config.blocks) {
    const meta = config.meta || {}
    return { ...config, brand: meta.brand ?? config.brand, accent: meta.accent ?? config.accent, style: meta.style ?? config.style, sections: config.blocks.find((b: any) => b.type === 'section-nav')?.props?.sections ?? undefined, eyebrow: '', headline: '', description: '', show_pricing: !!config.blocks.find((b: any) => b.type === 'pricing-grid') }
  }
  return config
}

function GeneratedApp({ project, onEvent, shared = false }: { project: Project; onEvent: (event: AppEvent) => void; shared?: boolean }) {
  const normalizedProject = { ...project, app_config: normalizeConfig(project.app_config) }
  if (project.template_type === 'project') return <ProjectPreview project={normalizedProject} onEvent={onEvent} shared={shared} />
  if (project.template_type === 'event') return <EventPreview project={normalizedProject} onEvent={onEvent} />
  return <LandingPreview project={normalizedProject} onEvent={onEvent} />
}

function accentStyles(accent: unknown) {
  return ({ blue: 'from-blue-400 to-cyan-300 text-blue-950', emerald: 'from-emerald-400 to-teal-300 text-emerald-950', orange: 'from-orange-300 to-amber-300 text-orange-950', violet: 'from-violet-400 to-fuchsia-300 text-violet-950' } as Record<string, string>)[String(accent)] ?? 'from-violet-400 to-fuchsia-300 text-violet-950'
}

function LandingPreview({ project, onEvent }: { project: Project; onEvent: (event: AppEvent) => void }) {
  const [formOpen, setFormOpen] = useState(false)
  const [submitted, setSubmitted] = useState(false)
  const config = project.app_config
  const plans = (config.plans as { name: string; price: string; detail: string }[] | undefined) ?? []
  const features = [
    { icon: '⚡', title: '极速启动', desc: '从想法到上线，只需几分钟' },
    { icon: '🎨', title: '精美设计', desc: '每个像素都经过精心打磨' },
    { icon: '🔄', title: '持续迭代', desc: '对话式修改，实时预览效果' },
    { icon: '📊', title: '数据驱动', desc: '内置分析，洞察每一个用户行为' },
  ]
  function submit(event: FormEvent<HTMLFormElement>) { event.preventDefault(); const data = new FormData(event.currentTarget); onEvent({ type: 'contact', payload: { name: String(data.get('name') ?? ''), email: String(data.get('email') ?? '') } }); setSubmitted(true) }
  return <div className="relative min-h-[680px] overflow-hidden bg-[#111117] px-5 py-5 text-zinc-100 sm:px-9 sm:py-7"><div className={cn('absolute -right-20 -top-20 h-80 w-80 rounded-full bg-gradient-to-br opacity-[.18] blur-3xl', accentStyles(config.accent))} /><nav className="relative flex items-center justify-between"><span className="font-display text-lg font-bold tracking-[-.055em]">{String(config.brand)}</span><div className="hidden gap-5 text-[11px] text-zinc-400 sm:flex"><span>产品</span><span>方案</span><span>客户</span></div><button onClick={() => setFormOpen(true)} className="rounded-lg border border-white/[.1] bg-white/[.05] px-3 py-1.5 text-[11px] text-zinc-200">预约演示</button></nav>
    <section className="relative flex min-h-[320px] max-w-xl flex-col justify-center py-14"><div className="mb-4 inline-flex w-fit rounded-full border border-white/[.1] bg-white/[.04] px-2.5 py-1 text-[9px] font-medium tracking-[.15em] text-zinc-300">{String(config.eyebrow)}</div><h1 className="font-display text-4xl font-semibold leading-[1.03] tracking-[-.065em] sm:text-5xl">{String(config.headline)}</h1><p className="mt-5 max-w-md text-sm leading-6 text-zinc-400">{String(config.description)}</p><div className="mt-7 flex gap-2.5"><button onClick={() => setFormOpen(true)} className={cn('rounded-lg bg-gradient-to-r px-4 py-2.5 text-xs font-bold', accentStyles(config.accent))}>开始体验 <ArrowUpRight size={14} className="ml-1 inline" /></button><button className="rounded-lg border border-white/[.1] px-4 py-2.5 text-xs text-zinc-300">了解更多</button></div></section>
    <section className="relative mt-6 grid gap-2.5 sm:grid-cols-2 lg:grid-cols-4">{features.map((feature) => <div key={feature.title} className="rounded-xl border border-white/[.08] bg-black/15 p-4"><div className="text-lg">{feature.icon}</div><div className="mt-2 text-xs font-semibold text-zinc-200">{feature.title}</div><p className="mt-1 text-[10px] leading-[1.5] text-zinc-500">{feature.desc}</p></div>)}</section>
    {config.show_pricing !== false && <section className="relative mt-6"><div className="mb-3 text-center text-[10px] font-medium tracking-[.15em] text-zinc-500">选择你的方案</div><div className="grid gap-2 sm:grid-cols-3">{plans.map((plan, index) => <div key={plan.name} className={cn('rounded-xl border p-4', index === 1 ? 'border-violet-300/30 bg-violet-400/[.08]' : 'border-white/[.08] bg-black/15')}><span className="text-[11px] text-zinc-400">{plan.name}</span><div className="mt-3 font-display text-2xl font-semibold tracking-[-.05em]">{plan.price}</div><p className="mt-2 text-[10px] text-zinc-500">{plan.detail}</p>{index === 1 && <span className="mt-3 inline-block rounded-full bg-violet-400/20 px-2 py-0.5 text-[9px] text-violet-200">推荐</span>}</div>)}</div></section>}
    <footer className="relative mt-10 border-t border-white/[.07] pt-5 text-center text-[10px] text-zinc-600">© 2026 {String(config.brand)}. 用 Atoms 构建。</footer>
    {formOpen && <div className="absolute inset-0 z-10 grid place-items-center bg-black/70 p-5 backdrop-blur-sm"><div className="w-full max-w-sm rounded-2xl border border-white/[.1] bg-[#1a1a22] p-5"><button onClick={() => setFormOpen(false)} className="float-right text-zinc-500"><X size={16} /></button>{submitted ? <div className="py-8 text-center"><CheckCircle2 className="mx-auto mb-3 text-emerald-300" /><h3 className="font-display text-xl">收到你的信息</h3><p className="mt-2 text-xs text-zinc-400">我们会尽快联系你。</p></div> : <form onSubmit={submit}><h3 className="font-display text-xl font-semibold tracking-[-.04em]">预约产品演示</h3><p className="mt-1 text-xs text-zinc-500">留下联系方式，我们会与您同步下一步。</p><input required name="name" placeholder="你的名字" className="mt-5 w-full rounded-lg border border-white/[.09] bg-black/20 px-3 py-2.5 text-xs outline-none placeholder:text-zinc-600 focus:border-violet-300/50" /><input required name="email" type="email" placeholder="工作邮箱" className="mt-2 w-full rounded-lg border border-white/[.09] bg-black/20 px-3 py-2.5 text-xs outline-none placeholder:text-zinc-600 focus:border-violet-300/50" /><button className={cn('mt-3 w-full rounded-lg bg-gradient-to-r py-2.5 text-xs font-bold', accentStyles(config.accent))}>提交预约</button></form>}</div></div>}
  </div>
}

function ProjectPreview({ project, onEvent, shared }: { project: Project; onEvent: (event: AppEvent) => void; shared: boolean }) {
  const [newTask, setNewTask] = useState('')
  const config = project.app_config
  const tasks = project.records.filter((record) => record.record_type === 'task')
  const doneCount = tasks.filter((t) => t.payload.status === 'done').length
  const progress = tasks.length > 0 ? doneCount / tasks.length * 100 : 0
  const isTodo = config.style === 'todo' || !((config.sections as string[])?.length)
  const states: Record<string, { label: string; color: string }> = { todo: { label: '待处理', color: 'text-zinc-400 bg-zinc-400/10' }, in_progress: { label: '进行中', color: 'text-violet-300 bg-violet-400/10' }, done: { label: '已完成', color: 'text-emerald-300 bg-emerald-400/10' } }
  function addTask(event: FormEvent) { event.preventDefault(); if (!newTask.trim()) return; onEvent({ type: 'task_create', payload: { title: newTask } }); setNewTask('') }

  const taskRows = tasks.map((task) => { const state = states[task.payload.status] ?? states.todo; return <div key={task.id} className="group flex items-center gap-3 rounded-xl border border-white/[.07] bg-white/[.025] px-3 py-3"><button onClick={() => onEvent({ type: 'task_update', payload: { record_id: task.id, status: task.payload.status === 'done' ? 'todo' : 'done' } })} className={cn('grid h-5 w-5 place-items-center rounded-full border', task.payload.status === 'done' ? 'border-emerald-400 bg-emerald-400 text-emerald-950' : 'border-zinc-600 text-transparent')}><Check size={12} /></button><span className={cn('min-w-0 flex-1 text-xs', task.payload.status === 'done' && 'text-zinc-600 line-through')}>{task.payload.title}</span><button onClick={() => onEvent({ type: 'task_update', payload: { record_id: task.id, status: task.payload.status === 'todo' ? 'in_progress' : 'todo' } })} className={cn('rounded-full px-2 py-1 text-[9px]', state.color)}>{state.label}</button>{!isTodo && <span className="hidden text-[10px] text-zinc-600 sm:block">{task.payload.due}</span>}{!shared && <button onClick={() => onEvent({ type: 'task_delete', payload: { record_id: task.id } })} className="text-zinc-700 opacity-0 transition group-hover:opacity-100 hover:text-red-300"><X size={13} /></button>}</div> })

  const header = <header className="flex items-center justify-between border-b border-white/[.07] px-5 py-4"><div className="flex items-center gap-2"><div className={cn('grid h-6 w-6 place-items-center rounded-md bg-gradient-to-br', accentStyles(config.accent))}><TerminalSquare size={13} /></div><span className="font-display text-sm font-semibold tracking-[-.04em]">{String(config.brand)}</span></div><span className="rounded-full bg-emerald-400/10 px-2 py-1 text-[9px] text-emerald-300">自动保存</span></header>

  if (isTodo) {
    return <div className="min-h-[650px] bg-[#111219] text-zinc-100">{header}<main className="mx-auto max-w-[560px] px-6 py-10 sm:px-10"><p className="text-[10px] font-medium tracking-[.15em] text-violet-300">{String(config.eyebrow)}</p><h1 className="mt-2 font-display text-4xl font-semibold leading-[1.1] tracking-[-.055em]">{String(config.headline)}</h1><p className="mt-3 text-[13px] text-zinc-500">{String(config.description)}</p><div className="mt-7 flex items-center gap-3 text-[11px] text-zinc-500"><span>完成 <span className="text-zinc-300">{doneCount}</span> / <span className="text-zinc-300">{tasks.length}</span></span><div className="h-1 flex-1 overflow-hidden rounded-sm bg-white/[.08]"><div className="h-full rounded-sm bg-gradient-to-br transition-all" style={{ width: `${progress}%`, backgroundImage: config.accent === 'blue' ? 'linear-gradient(135deg,#60a5fa,#67e8f9)' : config.accent === 'emerald' ? 'linear-gradient(135deg,#34d399,#5eead4)' : config.accent === 'orange' ? 'linear-gradient(135deg,#fdba74,#fcd34d)' : 'linear-gradient(135deg,#a78bfa,#e879f9)' }} /></div></div><form onSubmit={addTask} className="mt-7 flex gap-2"><input value={newTask} onChange={(event) => setNewTask(event.target.value)} placeholder="添加一个新任务…" className="min-w-0 flex-1 rounded-lg border border-white/[.08] bg-black/20 px-3 py-2.5 text-xs outline-none placeholder:text-zinc-600 focus:border-violet-300/50" /><button className="grid w-9 place-items-center rounded-lg bg-violet-400 text-violet-950"><Plus size={16} /></button></form><div className="mt-4 space-y-2">{taskRows}</div></main></div>
  }

  return <div className="min-h-[650px] bg-[#111219] text-zinc-100">{header}<div className="grid gap-0 lg:grid-cols-[150px_minmax(0,1fr)]"><aside className="border-b border-white/[.07] p-3 lg:min-h-[592px] lg:border-b-0 lg:border-r">{((config.sections as string[]) ?? []).map((section, index) => <button key={section} className={cn('mb-1 flex w-full items-center gap-2 rounded-md px-2.5 py-2 text-left text-[11px]', index === 1 ? 'bg-white/[.07] text-zinc-100' : 'text-zinc-500')}><Circle size={11} className={index === 1 ? 'text-violet-300' : ''} />{section}</button>)}</aside><main className="p-5 sm:p-7"><div className="flex flex-wrap items-end justify-between gap-3"><div><p className="text-[10px] font-medium tracking-[.15em] text-violet-300">{String(config.eyebrow)}</p><h2 className="mt-2 font-display text-2xl font-semibold tracking-[-.05em]">{String(config.headline)}</h2><p className="mt-2 text-xs text-zinc-500">{String(config.description)}</p></div><div className="rounded-lg border border-white/[.08] bg-white/[.025] px-3 py-2 text-right"><div className="text-lg font-semibold">{doneCount}/{tasks.length}</div><div className="text-[9px] text-zinc-500">本周已完成</div></div></div><form onSubmit={addTask} className="mt-6 flex gap-2"><input value={newTask} onChange={(event) => setNewTask(event.target.value)} placeholder="添加一个新任务…" className="min-w-0 flex-1 rounded-lg border border-white/[.08] bg-black/20 px-3 py-2.5 text-xs outline-none placeholder:text-zinc-600 focus:border-violet-300/50" /><button className="grid w-9 place-items-center rounded-lg bg-violet-400 text-violet-950"><Plus size={16} /></button></form><div className="mt-4 space-y-2">{taskRows}</div></main></div></div>
}

function EventPreview({ project, onEvent }: { project: Project; onEvent: (event: AppEvent) => void }) {
  const [submitted, setSubmitted] = useState(false)
  const config = project.app_config
  const registrations = project.records.filter((record) => record.record_type === 'registration')
  function submit(event: FormEvent<HTMLFormElement>) { event.preventDefault(); const data = new FormData(event.currentTarget); onEvent({ type: 'registration', payload: { name: String(data.get('name') ?? ''), session: String(data.get('session') ?? '') } }); setSubmitted(true) }
  return <div className="min-h-[680px] overflow-hidden bg-[#15100e] text-orange-50"><div className="relative border-b border-orange-100/[.1] px-5 py-5 sm:px-8"><div className="absolute -right-20 -top-16 h-52 w-52 rounded-full bg-orange-400/20 blur-3xl" /><nav className="relative flex items-center justify-between"><span className="font-display text-base font-semibold tracking-[-.04em]">{String(config.brand)}</span><span className="text-[10px] tracking-[.16em] text-orange-100/50">{String(config.eyebrow)}</span></nav><div className="relative max-w-xl py-14 sm:py-20"><p className="mb-4 text-[11px] text-orange-200/60">{String(config.date)}</p><h1 className="font-display text-4xl font-semibold leading-[1.02] tracking-[-.07em] sm:text-5xl">{String(config.headline)}</h1><p className="mt-5 max-w-md text-sm leading-6 text-orange-100/60">{String(config.description)}</p></div></div><div className="grid gap-5 p-5 sm:grid-cols-[1fr_.9fr] sm:p-8"><section><p className="text-[10px] tracking-[.14em] text-orange-200/50">CHOOSE YOUR PATH</p><div className="mt-3 space-y-2">{((config.sessions as string[]) ?? []).map((session, index) => <div key={session} className="flex items-center gap-3 rounded-xl border border-orange-100/[.1] bg-orange-100/[.035] p-3"><span className="grid h-6 w-6 place-items-center rounded-full bg-orange-200/10 text-[10px] text-orange-200">0{index + 1}</span><span className="text-xs text-orange-50/80">{session}</span></div>)}</div><p className="mt-5 text-[11px] text-orange-100/45"><span className="text-orange-200">{registrations.length}</span> / {String(config.capacity)} 人已报名</p></section><section className="rounded-2xl border border-orange-100/[.12] bg-black/20 p-5">{submitted ? <div className="py-9 text-center"><CheckCircle2 className="mx-auto mb-3 text-orange-200" /><h3 className="font-display text-xl">你已在名单中</h3><p className="mt-2 text-xs text-orange-100/50">期待在线下见到你。</p></div> : <form onSubmit={submit}><h3 className="font-display text-xl font-semibold tracking-[-.04em]">预留一个席位</h3><p className="mt-1 text-xs text-orange-100/50">名额有限，提交后即完成报名。</p><input required name="name" placeholder="你的名字" className="mt-5 w-full rounded-lg border border-orange-100/[.1] bg-black/20 px-3 py-2.5 text-xs outline-none placeholder:text-orange-100/30 focus:border-orange-200/40" /><select required name="session" defaultValue="" className="mt-2 w-full rounded-lg border border-orange-100/[.1] bg-[#1b1310] px-3 py-2.5 text-xs text-orange-50 outline-none"><option value="" disabled>选择参与场次</option>{((config.sessions as string[]) ?? []).map((session) => <option key={session}>{session}</option>)}</select><button className="mt-3 w-full rounded-lg bg-orange-200 py-2.5 text-xs font-bold text-orange-950">确认报名 <ArrowUpRight size={14} className="ml-1 inline" /></button></form>}</section></div></div>
}

export default App
