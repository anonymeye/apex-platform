"use client"

import * as React from "react"
import { useQuery, useQueryClient } from "@tanstack/react-query"
import { useRouter } from "next/navigation"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { evaluationApi } from "@/lib/api/evaluation"
import type { SavedConversation, JudgeConfig } from "@/lib/types/evaluation"

function formatDate(iso: string) {
  try {
    return new Date(iso).toLocaleString(undefined, {
      dateStyle: "short",
      timeStyle: "short",
    })
  } catch {
    return iso
  }
}

interface CreateRunFormProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onSuccess?: (runId: string) => void
}

export function CreateRunForm({
  open,
  onOpenChange,
  onSuccess,
}: CreateRunFormProps) {
  const router = useRouter()
  const queryClient = useQueryClient()
  const [savedConversationId, setSavedConversationId] = React.useState("")
  const [turnIndex, setTurnIndex] = React.useState(0)
  const [judgeConfigId, setJudgeConfigId] = React.useState("")
  const [submitting, setSubmitting] = React.useState(false)
  const [error, setError] = React.useState<string | null>(null)

  const { data: savedData, isLoading: loadingSaved } = useQuery({
    queryKey: ["saved-conversations", open],
    queryFn: async () => {
      const res = await evaluationApi.listSavedConversations({ limit: 100 })
      return res.data
    },
    enabled: open,
  })

  const { data: judgeData, isLoading: loadingJudges } = useQuery({
    queryKey: ["judge-configs", open],
    queryFn: async () => {
      const res = await evaluationApi.listJudgeConfigs({ limit: 100 })
      return res.data
    },
    enabled: open,
  })

  const savedConversations = savedData?.items ?? []
  const judgeConfigs = judgeData?.items ?? []

  const selectedConversation = savedConversations.find(
    (c: SavedConversation) => c.id === savedConversationId
  )
  const canSubmit =
    selectedConversation &&
    judgeConfigId &&
    !submitting

  const handleSubmit = async () => {
    if (!selectedConversation || !judgeConfigId) return
    setSubmitting(true)
    setError(null)
    try {
      const res = await evaluationApi.createRun({
        scope_type: "single",
        scope_payload: {
          conversation_id: selectedConversation.conversation_id,
          user_id: selectedConversation.user_id,
          turn_index: turnIndex,
        },
        judge_config_id: judgeConfigId,
      })
      onOpenChange(false)
      const runId = res.data.run_id
      queryClient.invalidateQueries({ queryKey: ["evaluation-runs"] })
      if (onSuccess) {
        onSuccess(runId)
      } else {
        router.push(`/evaluation/${runId}`)
      }
    } catch (e: unknown) {
      const detail =
        (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        (e as Error)?.message ||
        "Failed to create run"
      setError(String(detail))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Create evaluation run</DialogTitle>
          <DialogDescription>
            Run the judge on a saved conversation. Pick a conversation and a judge config.
          </DialogDescription>
        </DialogHeader>
        <div className="grid gap-4 py-2">
          <div className="grid gap-2">
            <Label htmlFor="create-run-conversation">Conversation</Label>
            <select
              id="create-run-conversation"
              value={savedConversationId}
              onChange={(e) => setSavedConversationId(e.target.value)}
              disabled={loadingSaved}
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
            >
              <option value="">Select a saved conversation…</option>
              {savedConversations.map((c: SavedConversation) => (
                <option key={c.id} value={c.id}>
                  {c.label} ({c.conversation_id.slice(0, 8)}…) · {formatDate(c.created_at)}
                </option>
              ))}
            </select>
            {savedConversations.length === 0 && !loadingSaved && (
              <p className="text-xs text-muted-foreground">
                No saved conversations. Save one from the Test Agent page first.
              </p>
            )}
          </div>

          <div className="grid gap-2">
            <Label htmlFor="create-run-turn">Turn index</Label>
            <Input
              id="create-run-turn"
              type="number"
              min={0}
              value={turnIndex}
              onChange={(e) => setTurnIndex(parseInt(e.target.value, 10) || 0)}
              disabled={submitting}
            />
            <p className="text-xs text-muted-foreground">
              Which turn to evaluate (0 = first user/assistant pair).
            </p>
          </div>

          <div className="grid gap-2">
            <Label htmlFor="create-run-judge">Judge config</Label>
            <select
              id="create-run-judge"
              value={judgeConfigId}
              onChange={(e) => setJudgeConfigId(e.target.value)}
              disabled={loadingJudges}
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
            >
              <option value="">Select a judge…</option>
              {judgeConfigs.map((j: JudgeConfig) => (
                <option key={j.id} value={j.id}>
                  {j.name}
                </option>
              ))}
            </select>
            {judgeConfigs.length === 0 && !loadingJudges && (
              <p className="text-xs text-muted-foreground">
                No judge configs. Add one in the Judge configs section above.
              </p>
            )}
          </div>

          {error && (
            <p className="text-sm text-destructive">{error}</p>
          )}
        </div>
        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}
            disabled={submitting}
          >
            Cancel
          </Button>
          <Button
            onClick={() => void handleSubmit()}
            disabled={!canSubmit}
          >
            {submitting ? "Creating…" : "Create run"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
