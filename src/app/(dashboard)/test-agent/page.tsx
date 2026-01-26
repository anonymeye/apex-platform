"use client"

import * as React from "react"
import { useAgentStore } from "@/lib/store/agentStore"
import { agentsApi } from "@/lib/api/agents"
import { chatApi } from "@/lib/api/chat"
import type { Agent } from "@/lib/types/agent"
import type { Message as ChatMessageBase, ToolCall } from "@/lib/types/chat"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Textarea } from "@/components/ui/textarea"
import { Bot } from "lucide-react"
import Link from "next/link"
import { cn } from "@/lib/utils/cn"

type Usage = {
  input_tokens: number
  output_tokens: number
  total_tokens?: number | null
  cache_read_tokens?: number | null
  cache_creation_tokens?: number | null
}

type ChatMessage = ChatMessageBase & {
  iterations?: number
  usage?: Usage | null
  tool_calls?: ToolCall[]
  error?: boolean
}

function makeId() {
  // crypto.randomUUID is supported in modern browsers; fallback for safety
  return typeof crypto !== "undefined" && "randomUUID" in crypto
    ? crypto.randomUUID()
    : `${Date.now()}-${Math.random().toString(16).slice(2)}`
}

export default function TestAgentPage() {
  const { selectedAgentId, selectedAgent, setSelectedAgent } = useAgentStore()
  const [resolvedAgent, setResolvedAgent] = React.useState<Agent | null>(selectedAgent)
  const [messages, setMessages] = React.useState<ChatMessage[]>([])
  const [input, setInput] = React.useState("")
  const [isSending, setIsSending] = React.useState(false)
  const [loadError, setLoadError] = React.useState<string | null>(null)
  const bottomRef = React.useRef<HTMLDivElement | null>(null)

  React.useEffect(() => {
    setResolvedAgent(selectedAgent)
  }, [selectedAgent])

  React.useEffect(() => {
    let cancelled = false

    async function resolveAgent() {
      if (selectedAgent) return
      if (!selectedAgentId) return

      try {
        setLoadError(null)
        const res = await agentsApi.get(selectedAgentId)
        if (cancelled) return
        setSelectedAgent(res.data)
        setResolvedAgent(res.data)
      } catch (e: any) {
        if (cancelled) return
        setLoadError(e?.response?.data?.detail || e?.message || "Failed to load agent")
      }
    }

    void resolveAgent()
    return () => {
      cancelled = true
    }
  }, [selectedAgent, selectedAgentId, setSelectedAgent])

  React.useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages.length])

  const agent = resolvedAgent

  if (!agent) {
    return (
      <div className="flex h-full flex-col items-center justify-center space-y-4">
        <Bot className="h-12 w-12 text-muted-foreground" />
        <div className="text-center space-y-2">
          <h2 className="text-2xl font-semibold">No Agent Selected</h2>
          <p className="text-muted-foreground">
            Please select an agent from the sidebar to start testing
          </p>
          {loadError && (
            <p className="text-sm text-destructive">{loadError}</p>
          )}
          <Button asChild className="mt-4">
            <Link href="/agents">Go to Agents</Link>
          </Button>
        </div>
      </div>
    )
  }

  const handleClear = () => {
    setMessages([])
    setInput("")
    setIsSending(false)
  }

  const handleSend = async () => {
    const content = input.trim()
    if (!content) return
    if (isSending) return

    const userMsg: ChatMessage = {
      id: makeId(),
      role: "user",
      content,
      timestamp: new Date().toISOString(),
    }

    setMessages((prev) => [...prev, userMsg])
    setInput("")
    setIsSending(true)

    try {
      const res = await chatApi.sendMessage(agent.id, content)
      const data = res.data as {
        id: string
        role: "assistant"
        content: string
        timestamp: string
        tool_calls?: ToolCall[] | null
        iterations?: number
        usage?: Usage | null
      }

      const assistantMsg: ChatMessage = {
        id: data.id || makeId(),
        role: "assistant",
        content: data.content ?? "",
        timestamp: data.timestamp || new Date().toISOString(),
        tool_calls: data.tool_calls ?? undefined,
        iterations: data.iterations,
        usage: data.usage ?? null,
      }
      setMessages((prev) => [...prev, assistantMsg])
    } catch (e: any) {
      const detail =
        e?.response?.data?.detail || e?.message || "Failed to send message"
      const errorMsg: ChatMessage = {
        id: makeId(),
        role: "assistant",
        content: `Error: ${detail}`,
        timestamp: new Date().toISOString(),
        error: true,
      }
      setMessages((prev) => [...prev, errorMsg])
    } finally {
      setIsSending(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold">Test Agent</h1>
          <p className="text-muted-foreground">
            Testing: <span className="font-medium">{agent.name}</span>
            {agent.model_ref?.connection?.name && agent.model_ref?.name && (
              <span className="text-muted-foreground">
                {" "}
                ({agent.model_ref.connection.name}/{agent.model_ref.name})
              </span>
            )}
          </p>
          <p className="text-sm text-muted-foreground">
            Tools: <span className="font-medium">{agent.tools?.length ?? 0}</span>
          </p>
        </div>
        <Button variant="outline" onClick={handleClear} disabled={isSending && messages.length === 0}>
          Clear chat
        </Button>
      </div>

      <Card className="flex flex-col">
        <CardHeader className="pb-3">
          <CardTitle className="text-lg">Conversation</CardTitle>
        </CardHeader>
        <CardContent className="flex-1 space-y-4 overflow-y-auto max-h-[65vh] pr-2">
          {messages.length === 0 ? (
            <div className="text-sm text-muted-foreground">
              Send a message to start chatting with this agent.
            </div>
          ) : (
            <div className="space-y-4">
              {messages.map((m) => (
                <div
                  key={m.id}
                  className={cn(
                    "flex w-full",
                    m.role === "user" ? "justify-end" : "justify-start"
                  )}
                >
                  <div
                    className={cn(
                      "max-w-[80%] rounded-lg px-3 py-2 text-sm whitespace-pre-wrap break-words",
                      m.role === "user"
                        ? "bg-primary text-primary-foreground"
                        : m.error
                          ? "bg-destructive text-destructive-foreground"
                          : "bg-muted text-foreground"
                    )}
                  >
                    <div>{m.content}</div>
                    <div className="mt-2 text-[11px] opacity-70">
                      {new Date(m.timestamp).toLocaleTimeString()}
                      {m.role === "assistant" && typeof m.iterations === "number" && (
                        <span> · iters {m.iterations}</span>
                      )}
                      {m.role === "assistant" && m.usage && (
                        <span>
                          {" "}
                          · tokens {m.usage.input_tokens}/{m.usage.output_tokens}
                        </span>
                      )}
                    </div>

                    {m.role === "assistant" && m.tool_calls && m.tool_calls.length > 0 && (
                      <details className="mt-2">
                        <summary className="cursor-pointer text-[11px] opacity-80">
                          Tool calls ({m.tool_calls.length})
                        </summary>
                        <div className="mt-2 space-y-2 text-[12px]">
                          {m.tool_calls.map((tc) => (
                            <div key={tc.id} className="rounded-md border bg-background/60 p-2">
                              <div className="font-medium">{tc.name}</div>
                              <pre className="mt-1 overflow-x-auto text-[11px] opacity-90">
                                {JSON.stringify(tc.arguments ?? {}, null, 2)}
                              </pre>
                            </div>
                          ))}
                        </div>
                      </details>
                    )}
                  </div>
                </div>
              ))}
              <div ref={bottomRef} />
            </div>
          )}
        </CardContent>
        <CardFooter className="flex flex-col gap-2">
          <Textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type a message… (Enter to send, Shift+Enter for newline)"
            disabled={isSending}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault()
                void handleSend()
              }
            }}
            className="min-h-[90px]"
          />
          <div className="flex w-full items-center justify-end gap-2">
            <Button onClick={handleSend} disabled={isSending || input.trim().length === 0}>
              {isSending ? "Sending…" : "Send"}
            </Button>
          </div>
        </CardFooter>
      </Card>
    </div>
  )
}
