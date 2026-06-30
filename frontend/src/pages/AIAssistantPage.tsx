import React, { useEffect, useMemo, useRef, useState } from "react"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"
import { ChevronRight, FileText, PanelLeft, RotateCcw, Send, Sparkles, Trash2, Upload } from "lucide-react"
import {
  useDeleteRagDocument,
  useRagChat,
  useRagDocuments,
  useUploadRagDocument,
} from "../hooks"
import { useToastStore } from "../store"
import { Button } from "../components/common/Button"
import { formatRelativeTime } from "../lib/time"
import type { RagSourceReference } from "../types"

interface ChatMessage {
  id: string
  role: "user" | "assistant"
  content: string
  sources?: RagSourceReference[]
  timestamp: string
}

const STORAGE_KEY = "onboarding-assistant-chat"

const BASE_QUESTIONS = [
  "What onboarding tasks are pending?",
  "Explain the VPN setup process.",
  "Summarize the employee handbook.",
  "What documents are pending review?",
  "What is the provisioning checklist?",
]

export const AIAssistantPage: React.FC = () => {
  const [question, setQuestion] = useState("")
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [documentType, setDocumentType] = useState("onboarding_policy")
  const [isTyping, setIsTyping] = useState(false)
  const [showSourcesFor, setShowSourcesFor] = useState<string | null>(null)
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const chatBottomRef = useRef<HTMLDivElement | null>(null)

  const { data: documents = [], isLoading: documentsLoading } = useRagDocuments()
  const uploadMutation = useUploadRagDocument()
  const deleteMutation = useDeleteRagDocument()
  const chatMutation = useRagChat()
  const addToast = useToastStore((state) => state.addToast)

  const sortedDocuments = useMemo(
    () => [...documents].sort((a, b) => (b.ingested_at || "").localeCompare(a.ingested_at || "")),
    [documents],
  )

  const suggestedQuestions = useMemo(() => {
    const fromDocs = sortedDocuments.slice(0, 2).map((doc) => `Summarize ${doc.document_name}.`)
    return [...BASE_QUESTIONS, ...fromDocs].slice(0, 5)
  }, [sortedDocuments])

  const selectedSourceMessage = useMemo(
    () => messages.find((message) => message.id === showSourcesFor) ?? null,
    [messages, showSourcesFor],
  )
  const selectedSources = selectedSourceMessage?.sources ?? []
  const assistantResponses = messages.filter((message) => message.role === "assistant").length
  const totalCitations = messages.reduce((sum, message) => sum + (message.sources?.length ?? 0), 0)
  const conversationHistory = useMemo(
    () => messages
      .filter((message) => message.role === "user")
      .slice(-12)
      .reverse(),
    [messages],
  )

  useEffect(() => {
    try {
      const raw = globalThis.localStorage.getItem(STORAGE_KEY)
      if (!raw) return
      const parsed = JSON.parse(raw) as { sessionId: string | null; messages: ChatMessage[] }
      setSessionId(parsed.sessionId)
      setMessages(parsed.messages.slice(-30))
    } catch {
      // ignore malformed local cache
    }
  }, [])

  useEffect(() => {
    const payload = JSON.stringify({ sessionId, messages: messages.slice(-30) })
    globalThis.localStorage.setItem(STORAGE_KEY, payload)
  }, [messages, sessionId])

  const pushMessage = (message: ChatMessage) => {
    setMessages((prev) => [...prev, message])
    requestAnimationFrame(() => chatBottomRef.current?.scrollIntoView({ behavior: "smooth" }))
  }

  const updateStreamContent = (messageId: string, content: string, length: number) => {
    setMessages((prev) => prev.map((msg) => (msg.id === messageId ? { ...msg, content: content.slice(0, length) } : msg)))
  }

  const streamAssistantMessage = (content: string, sources: RagSourceReference[]) => {
    const messageId = crypto.randomUUID()
    const timestamp = new Date().toISOString()
    setIsTyping(true)
    setMessages((prev) => [...prev, { id: messageId, role: "assistant", content: "", sources, timestamp }])
    let index = 0
    const interval = globalThis.setInterval(() => {
      index += 8
      updateStreamContent(messageId, content, index)
      requestAnimationFrame(() => chatBottomRef.current?.scrollIntoView({ behavior: "smooth" }))
      if (index >= content.length) {
        globalThis.clearInterval(interval)
        setIsTyping(false)
      }
    }, 16)
  }

  const submitQuestion = async (value?: string) => {
    const text = (value ?? question).trim()
    if (!text) return
    pushMessage({ id: crypto.randomUUID(), role: "user", content: text, timestamp: new Date().toISOString() })
    setQuestion("")
    try {
      const response = await chatMutation.mutateAsync({ question: text, session_id: sessionId, top_k: 5 })
      setSessionId(response.session_id)
      streamAssistantMessage(response.answer, response.sources)
    } catch {
      setIsTyping(false)
      addToast({ title: "Assistant request failed", description: "Unable to generate a response. Please try again.", variant: "error" })
    }
  }

  const handleFileUpload = async (file: File | null) => {
    if (!file) return
    try {
      await uploadMutation.mutateAsync({ file, documentType })
      addToast({ title: "Document indexed", description: `${file.name} is ready for semantic search.`, variant: "success" })
    } catch {
      addToast({ title: "Upload failed", description: "Use a valid PDF under the configured size limit.", variant: "error" })
    }
  }

  const deleteDocument = async (documentId: string) => {
    try {
      await deleteMutation.mutateAsync(documentId)
      addToast({ title: "Document removed", description: "Indexed chunks were deleted from the assistant store.", variant: "success" })
    } catch {
      addToast({ title: "Delete failed", description: "Document could not be deleted.", variant: "error" })
    }
  }

  return (
    <section className="flex h-[calc(100vh-5.5rem)] flex-col overflow-hidden rounded-2xl border border-slate-200/70 bg-white/95 shadow-sm dark:border-slate-700 dark:bg-slate-900/90">
      {/* Top bar */}
      <div className="flex flex-shrink-0 items-center justify-between border-b border-slate-200 px-4 py-2.5 dark:border-slate-700">
        <div className="flex items-center gap-3">
          <button
            onClick={() => setSidebarOpen((v) => !v)}
            className="rounded-lg p-1.5 text-slate-500 hover:bg-slate-100 hover:text-slate-700 dark:hover:bg-slate-800 dark:hover:text-slate-100"
            aria-label="Toggle document sidebar"
            title="Toggle sidebar"
          >
            <PanelLeft className="h-4 w-4" />
          </button>
          <div className="flex items-center gap-2">
            <span className="flex h-7 w-7 items-center justify-center rounded-xl bg-slate-900 dark:bg-sky-500">
              <Sparkles className="h-3.5 w-3.5 text-white dark:text-slate-950" />
            </span>
            <p className="text-sm font-semibold text-slate-900 dark:text-slate-100">AI Onboarding Assistant</p>
            <span className="rounded-md bg-slate-100 px-1.5 py-0.5 text-xs font-semibold uppercase tracking-wide text-slate-500 dark:bg-slate-800 dark:text-slate-400">RAG | Grounded</span>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-400">{messages.length} msgs | {sortedDocuments.length} docs</span>
          <button
            onClick={() => { setMessages([]); setSessionId(null); globalThis.localStorage.removeItem(STORAGE_KEY) }}
            className="flex items-center gap-1 rounded-lg px-2 py-1.5 text-xs font-medium text-slate-500 hover:bg-slate-100 hover:text-slate-700 dark:hover:bg-slate-800 dark:hover:text-slate-100"
            title="Clear history"
          >
            <RotateCcw className="h-3 w-3" />
            Clear
          </button>
        </div>
      </div>

      <div className="flex min-h-0 flex-1">
        {/* Document sidebar */}
        {sidebarOpen && (
          <aside className="flex w-64 flex-shrink-0 flex-col border-r border-slate-200 dark:border-slate-700">
            <div className="flex-shrink-0 border-b border-slate-100 px-3 py-2.5 dark:border-slate-800">
              <p className="section-label">Knowledge Base</p>
            </div>
            <div className="flex-1 space-y-3 overflow-y-auto p-3">
              {/* Upload */}
              <div className="space-y-2">
                <select
                  className="surface-select text-xs"
                  value={documentType}
                  onChange={(e) => setDocumentType(e.target.value)}
                  aria-label="Document type"
                >
                  <option value="onboarding_policy">Onboarding Policy</option>
                  <option value="handbook">Employee Handbook</option>
                  <option value="it_setup">IT Setup Guide</option>
                  <option value="hr_compliance">HR Compliance</option>
                </select>
                <label className="flex cursor-pointer items-center justify-center gap-2 rounded-xl border-2 border-dashed border-slate-300 bg-slate-50 py-2.5 text-xs font-medium text-slate-600 transition-all hover:border-violet-400 hover:bg-violet-50 dark:border-slate-600 dark:bg-slate-800/50 dark:hover:border-violet-500">
                  <input type="file" accept="application/pdf" className="hidden" onChange={(e) => { void handleFileUpload(e.target.files?.[0] ?? null); e.currentTarget.value = "" }} />
                  <Upload className="h-3.5 w-3.5" />
                  {uploadMutation.isPending ? "Indexing..." : "Upload PDF"}
                </label>
              </div>

              {/* Doc list */}
              <div>
                <p className="section-label mb-1.5">Indexed ({sortedDocuments.length})</p>
                {documentsLoading && <p className="text-xs text-slate-400">Loading…</p>}
                {!documentsLoading && sortedDocuments.length === 0 && (
                  <p className="text-xs text-slate-400">No documents yet. Upload a PDF above.</p>
                )}
                {!documentsLoading && sortedDocuments.length > 0 && (
                  <div className="space-y-1">
                    {sortedDocuments.map((doc) => (
                      <div key={doc.document_id} className="group flex items-center gap-2 rounded-lg px-2 py-1.5 hover:bg-slate-100 dark:hover:bg-slate-800">
                        <FileText className="h-3.5 w-3.5 flex-shrink-0 text-slate-400" />
                        <div className="min-w-0 flex-1">
                          <p className="truncate text-xs font-medium text-slate-800 dark:text-slate-200">{doc.document_name}</p>
                          <p className="text-xs text-slate-400">{doc.chunks_indexed ?? "?"} chunks</p>
                        </div>
                        <button
                          onClick={() => void deleteDocument(doc.document_id)}
                          disabled={deleteMutation.isPending}
                          className="hidden rounded p-0.5 text-slate-400 hover:text-rose-500 group-hover:flex"
                          aria-label="Delete document"
                        >
                          <Trash2 className="h-3 w-3" />
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <div>
                <p className="section-label mb-1.5">Conversation History</p>
                {conversationHistory.length === 0 ? (
                  <p className="text-xs text-slate-400">No conversation history yet.</p>
                ) : (
                  <div className="space-y-1.5">
                    {conversationHistory.map((entry) => (
                      <button
                        key={`history-${entry.id}`}
                        type="button"
                        onClick={() => {
                          setQuestion(entry.content)
                        }}
                        className="w-full rounded-lg border border-slate-200 bg-white px-2 py-1.5 text-left text-xs text-slate-600 hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300 dark:hover:bg-slate-800"
                        title="Reuse question"
                      >
                        <p className="line-clamp-2">{entry.content}</p>
                        <p className="mt-0.5 text-xs text-slate-400">{formatRelativeTime(entry.timestamp)}</p>
                      </button>
                    ))}
                  </div>
                )}
              </div>

              <div>
                <p className="section-label mb-1.5">Suggested Prompts</p>
                <div className="space-y-1.5">
                  {suggestedQuestions.map((prompt) => (
                    <button
                      key={`sidebar-prompt-${prompt}`}
                      type="button"
                      onClick={() => void submitQuestion(prompt)}
                      className="w-full rounded-lg border border-slate-200 bg-white px-2 py-1.5 text-left text-xs font-medium text-slate-600 hover:border-blue-300 hover:bg-violet-50 hover:text-violet-700 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300 dark:hover:border-violet-500 dark:hover:bg-blue-900/20"
                    >
                      {prompt}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </aside>
        )}

        {/* Chat pane */}
        <div className="flex min-w-0 flex-1 flex-col">
          <div className="grid grid-cols-3 gap-2 border-b border-slate-100 px-4 py-2 dark:border-slate-800">
            {[
              { label: "Responses", value: assistantResponses },
              { label: "Citations", value: totalCitations },
              { label: "Indexed Docs", value: sortedDocuments.length },
            ].map((metric) => (
              <div key={metric.label} className="rounded-lg border border-slate-200 bg-slate-50/80 px-2.5 py-1.5 dark:border-slate-700 dark:bg-slate-900/70">
                <p className="section-label">{metric.label}</p>
                <p className="text-lg font-bold tabular-nums text-slate-900 dark:text-slate-100">{metric.value}</p>
              </div>
            ))}
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto px-4 py-4">
            {messages.length === 0 ? (
              <div className="flex h-full flex-col items-center justify-center gap-6">
                <div className="text-center">
                  <span className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-slate-900 dark:bg-sky-500">
                    <Sparkles className="h-7 w-7 text-white dark:text-slate-950" />
                  </span>
                  <p className="mt-3 text-base font-semibold text-slate-900 dark:text-slate-100">Onboarding AI Assistant</p>
                  <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">Ask about policies, tasks, provisioning, or any onboarding topic.</p>
                </div>
                <div className="flex flex-wrap justify-center gap-2">
                  {suggestedQuestions.map((q) => (
                    <button key={q} type="button" onClick={() => void submitQuestion(q)}
                      className="rounded-full border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-700 shadow-sm hover:border-blue-300 hover:bg-violet-50 hover:text-violet-800 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200 dark:hover:border-violet-500 dark:hover:bg-blue-900/20"
                    >
                      <ChevronRight className="mr-0.5 inline h-3 w-3 text-slate-400" />{q}
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              <div className="mx-auto max-w-4xl space-y-3.5">
                {messages.map((message) => {
                  const isUser = message.role === "user"
                  return (
                    <article key={message.id} className={`flex gap-3 ${isUser ? "flex-row-reverse" : ""}`}>
                      {/* Avatar */}
                      {isUser ? (
                        <span className="mt-1 flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-full bg-violet-600 text-xs font-bold text-white">
                          U
                        </span>
                      ) : (
                        <span className="mt-1 flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-lg bg-violet-600 text-white">
                          <Sparkles className="h-3.5 w-3.5" />
                        </span>
                      )}

                      <div className={`max-w-[85%] ${isUser ? "items-end" : "items-start"} flex flex-col gap-1`}>
                        {/* Bubble */}
                        <div className={`rounded-xl px-4 py-2.5 text-sm ${
                          isUser
                            ? "bg-violet-600 text-white"
                            : "border bg-white shadow-sm dark:bg-slate-800 dark:text-slate-100"
                        }`} style={{ borderColor: isUser ? "transparent" : "var(--surface-border)" }}>
                          {isUser ? (
                            <p className="whitespace-pre-wrap leading-relaxed">{message.content}</p>
                          ) : (
                            <div className="prose prose-sm max-w-none dark:prose-invert prose-pre:rounded-lg prose-pre:bg-slate-900 prose-pre:text-slate-100 prose-code:rounded prose-code:bg-slate-100 prose-code:px-1 prose-code:text-slate-800 dark:prose-code:bg-slate-800 dark:prose-code:text-slate-100">
                              <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content}</ReactMarkdown>
                            </div>
                          )}
                        </div>
                        <p className="px-1 text-xs text-slate-400">{formatRelativeTime(message.timestamp)}</p>

                        {/* Citations */}
                        {message.sources && message.sources.length > 0 && (
                          <div>
                            <button
                              type="button"
                              onClick={() => setShowSourcesFor((prev) => (prev === message.id ? null : message.id))}
                              className="flex items-center gap-1.5 rounded-md border px-2 py-1 text-xs font-medium text-slate-500 transition-colors hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200"
                              style={{ borderColor: "var(--surface-border)" }}
                            >
                              <FileText className="h-3 w-3" />
                              {showSourcesFor === message.id ? "Hide sources" : `${message.sources.length} source${message.sources.length > 1 ? "s" : ""}`}
                            </button>
                            {showSourcesFor === message.id && (
                              <div className="mt-2 grid gap-1.5 sm:grid-cols-2">
                                {message.sources.map((source) => (
                                  <div key={`${message.id}-${source.index}`} className="rounded-lg border p-2.5 text-xs" style={{ borderColor: "var(--surface-border)", backgroundColor: "var(--surface-muted)" }}>
                                    <p className="font-semibold text-slate-800 dark:text-slate-200">
                                      [{source.index}] {source.document_name}
                                    </p>
                                    <div className="mt-1 flex items-center gap-2">
                                      <span className="text-slate-400">Relevance:</span>
                                      <div className="h-1 flex-1 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-700">
                                        <div
                                          className="h-full rounded-full bg-violet-500"
                                          style={{ width: `${Math.round(source.score * 100)}%` }}
                                        />
                                      </div>
                                      <span className="text-slate-500">{Math.round(source.score * 100)}%</span>
                                    </div>
                                    <p className="mt-1.5 line-clamp-3 text-slate-600 dark:text-slate-300">{source.excerpt}</p>
                                  </div>
                                ))}
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    </article>
                  )
                })}

                {(chatMutation.isPending || isTyping) && (
                  <div className="flex gap-3">
                    <span className="mt-1 flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-lg bg-violet-600 text-white">
                      <Sparkles className="h-3.5 w-3.5" />
                    </span>
                    <div className="rounded-2xl border border-slate-200 bg-white px-4 py-3 shadow-sm dark:border-slate-700 dark:bg-slate-800">
                      <div className="flex items-center gap-1.5">
                        <span className="h-2 w-2 animate-bounce rounded-full bg-slate-400" style={{ animationDelay: "0ms" }} />
                        <span className="h-2 w-2 animate-bounce rounded-full bg-slate-400" style={{ animationDelay: "120ms" }} />
                        <span className="h-2 w-2 animate-bounce rounded-full bg-slate-400" style={{ animationDelay: "240ms" }} />
                      </div>
                    </div>
                  </div>
                )}
                <div ref={chatBottomRef} />
              </div>
            )}
          </div>

          {/* Suggested prompts strip (visible after first message) */}
          {messages.length > 0 && (
            <div className="flex flex-shrink-0 gap-2 overflow-x-auto border-t border-slate-100 px-4 py-2 dark:border-slate-800">
              {suggestedQuestions.map((q) => (
                <button key={q} type="button" onClick={() => void submitQuestion(q)}
                  className="flex-shrink-0 rounded-full border border-slate-200 bg-white px-3 py-1 text-xs font-medium text-slate-600 hover:border-blue-300 hover:text-violet-700 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300 dark:hover:text-sky-400"
                >
                  {q}
                </button>
              ))}
            </div>
          )}

          {/* Composer */}
          <div className="flex-shrink-0 border-t border-slate-200 bg-white px-4 py-3 dark:border-slate-700 dark:bg-slate-900">
            <form className="flex items-end gap-2" onSubmit={(e) => { e.preventDefault(); void submitQuestion() }}>
              <textarea
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); void submitQuestion() } }}
                placeholder="Ask about policies, workflow blockers, provisioning status..."
                rows={1}
                className="surface-input flex-1 resize-none py-2.5"
                style={{ minHeight: 40, maxHeight: 120 }}
                aria-label="Chat input"
              />
              <Button
                type="submit"
                disabled={chatMutation.isPending || isTyping || question.trim().length === 0}
                size="sm"
              >
                <Send className="h-4 w-4" />
              </Button>
            </form>
            <p className="mt-1.5 text-center text-xs text-slate-400">AI responses are grounded in indexed documents. Verify critical decisions independently.</p>
          </div>
        </div>

        <aside className="hidden w-80 flex-shrink-0 border-l border-slate-200 p-3 xl:flex xl:flex-col dark:border-slate-700">
          <p className="section-label">Citation Inspector</p>
          {selectedSourceMessage ? (
            <>
              <p className="mt-1 text-xs font-semibold text-slate-700 dark:text-slate-200">
                Message: {formatRelativeTime(selectedSourceMessage.timestamp)}
              </p>
              <div className="mt-2 space-y-2 overflow-y-auto">
                {selectedSources.map((source) => (
                  <article
                    key={`inspector-${selectedSourceMessage.id}-${source.index}`}
                    className="rounded-xl border border-slate-200 bg-slate-50 p-2.5 text-xs dark:border-slate-700 dark:bg-slate-900"
                  >
                    <p className="font-semibold text-slate-800 dark:text-slate-200">
                      [{source.index}] {source.document_name}
                    </p>
                    <div className="mt-1.5 flex items-center gap-2">
                      <span className="text-xs text-slate-400">Relevance:</span>
                      <div className="h-1 flex-1 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-700">
                        <div className="h-full rounded-full bg-violet-500" style={{ width: `${Math.round(source.score * 100)}%` }} />
                      </div>
                      <span className="text-xs text-slate-500">{Math.round(source.score * 100)}%</span>
                    </div>
                    <p className="mt-1.5 text-xs text-slate-600 dark:text-slate-300">{source.excerpt}</p>
                  </article>
                ))}
              </div>
            </>
          ) : (
            <div className="mt-2 rounded-xl border border-dashed border-slate-300 bg-slate-50 p-3 text-xs text-slate-500 dark:border-slate-700 dark:bg-slate-900/70 dark:text-slate-300">
              Select a message citation to inspect grounded excerpts and relevance scores.
            </div>
          )}
        </aside>
      </div>
    </section>
  )
}

