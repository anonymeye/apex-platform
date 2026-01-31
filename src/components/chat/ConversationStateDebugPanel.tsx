"use client"

import * as React from "react"
import { chatApi, type ConversationStateResponse } from "@/lib/api/chat"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Bug, ChevronLeft, RefreshCw } from "lucide-react"
import { cn } from "@/lib/utils/cn"

const PANEL_WIDTH = 380

type Props = {
  agentId: string
  conversationId: string | null
  className?: string
}

export function ConversationStateDebugPanel({
  agentId,
  conversationId,
  className,
}: Props) {
  const [open, setOpen] = React.useState(false)
  const [state, setState] = React.useState<ConversationStateResponse | null>(null)
  const [loading, setLoading] = React.useState(false)
  const [error, setError] = React.useState<string | null>(null)
  const [showRawJson, setShowRawJson] = React.useState(false)

  const fetchState = React.useCallback(async () => {
    if (!conversationId) return
    setLoading(true)
    setError(null)
    try {
      const res = await chatApi.getConversationState(agentId, conversationId)
      setState(res.data)
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string }; status?: number } }
      const detail =
        err?.response?.data?.detail ??
        (err?.response?.status === 404
          ? "Not found or expired"
          : "Failed to load state")
      setError(String(detail))
      setState(null)
    } finally {
      setLoading(false)
    }
  }, [agentId, conversationId])

  React.useEffect(() => {
    if (open && conversationId) void fetchState()
  }, [open, conversationId, fetchState])

  const hasConversation = Boolean(conversationId)

  return (
    <div className={cn("relative", className)}>
      <Button
        variant="outline"
        size="sm"
        onClick={() => setOpen((o) => !o)}
        disabled={!hasConversation}
        title={hasConversation ? "Toggle Redis state debug panel" : "Start a conversation to see state"}
        className="gap-2"
      >
        <Bug className="h-4 w-4" />
        Debug state
      </Button>

      <div
        className={cn(
          "fixed top-0 right-0 z-50 h-full bg-background border-l shadow-lg transition-transform duration-200 ease-out flex flex-col",
          open ? "translate-x-0" : "translate-x-full"
        )}
        style={{ width: PANEL_WIDTH, maxWidth: "100vw" }}
      >
        <div className="flex items-center justify-between gap-2 border-b px-3 py-2">
          <span className="text-sm font-medium">Redis conversation state</span>
          <div className="flex items-center gap-1">
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8"
              onClick={() => open && conversationId && void fetchState()}
              disabled={!conversationId || loading}
              title="Refresh"
            >
              <RefreshCw className={cn("h-4 w-4", loading && "animate-spin")} />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8"
              onClick={() => setOpen(false)}
              title="Close"
            >
              <ChevronLeft className="h-4 w-4" />
            </Button>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-3 space-y-4">
          {!conversationId ? (
            <p className="text-sm text-muted-foreground">
              No active conversation. Send a message to see state.
            </p>
          ) : error ? (
            <p className="text-sm text-destructive">{error}</p>
          ) : state ? (
            <>
              <Card>
                <CardHeader className="py-2 px-3">
                  <CardTitle className="text-sm">Metadata</CardTitle>
                </CardHeader>
                <CardContent className="py-0 px-3 pb-3 text-xs space-y-1">
                  <Row label="conversation_id" value={state.metadata.conversation_id} />
                  <Row label="user_id" value={state.metadata.user_id} />
                  <Row label="agent_id" value={state.metadata.agent_id} />
                  <Row label="created_at" value={state.metadata.created_at} />
                  <Row label="last_activity_at" value={state.metadata.last_activity_at} />
                  <Row label="message_count" value={String(state.metadata.message_count)} />
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="py-2 px-3 flex flex-row items-center justify-between">
                  <CardTitle className="text-sm">Messages ({state.messages.length})</CardTitle>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="text-xs h-7"
                    onClick={() => setShowRawJson((v) => !v)}
                  >
                    {showRawJson ? "List" : "Raw JSON"}
                  </Button>
                </CardHeader>
                <CardContent className="py-0 px-3 pb-3">
                  {showRawJson ? (
                    <pre className="text-[11px] overflow-x-auto rounded border bg-muted/50 p-2 max-h-[40vh] overflow-y-auto">
                      {JSON.stringify(state.messages, null, 2)}
                    </pre>
                  ) : (
                    <ul className="space-y-2 text-xs max-h-[40vh] overflow-y-auto">
                      {state.messages.map((msg, i) => (
                        <MessageItem key={i} msg={msg} />
                      ))}
                    </ul>
                  )}
                </CardContent>
              </Card>
            </>
          ) : loading ? (
            <p className="text-sm text-muted-foreground">Loading…</p>
          ) : null}
        </div>
      </div>

      {open && (
        <button
          type="button"
          className="fixed inset-0 z-40 bg-black/20"
          aria-label="Close panel"
          onClick={() => setOpen(false)}
        />
      )}
    </div>
  )
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex gap-2 break-all">
      <span className="text-muted-foreground shrink-0">{label}:</span>
      <span className="min-w-0">{value}</span>
    </div>
  )
}

function MessageItem({ msg }: { msg: Record<string, unknown> }) {
  const role = String(msg.role ?? "?")
  const content = typeof msg.content === "string" ? msg.content : JSON.stringify(msg.content ?? "")
  const preview = content.length > 120 ? content.slice(0, 120) + "…" : content
  return (
    <li className="rounded border bg-muted/30 p-2">
      <div className="font-medium text-muted-foreground">{role}</div>
      <div className="mt-1 whitespace-pre-wrap break-words">{preview}</div>
    </li>
  )
}
