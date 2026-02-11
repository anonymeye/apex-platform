"use client"

import { useState, useEffect } from "react"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { X, Loader2, MessageSquare } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { evaluationApi } from "@/lib/api/evaluation"
import type { ScoreResponse } from "@/lib/types/evaluation"

function formatDate(iso: string | null) {
  if (!iso) return null
  try {
    return new Date(iso).toLocaleString(undefined, {
      dateStyle: "short",
      timeStyle: "short",
    })
  } catch {
    return iso
  }
}

interface HumanReviewSidePanelProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  runId: string
  score: ScoreResponse | null
}

export function HumanReviewSidePanel({
  open,
  onOpenChange,
  runId,
  score,
}: HumanReviewSidePanelProps) {
  const queryClient = useQueryClient()
  const [scoreValue, setScoreValue] = useState("")
  const [comment, setComment] = useState("")

  useEffect(() => {
    if (score) {
      setScoreValue(score.human_score != null ? String(score.human_score) : "")
      setComment(score.human_comment ?? "")
    }
  }, [score])

  const submitHumanScore = useMutation({
    mutationFn: async () => {
      const num = parseFloat(scoreValue)
      if (Number.isNaN(num)) throw new Error("Enter a valid number for score")
      const res = await evaluationApi.submitHumanScore(runId, score!.id, {
        score: num,
        comment: comment.trim() || undefined,
      })
      return res.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["evaluation-scores", runId] })
      onOpenChange(false)
    },
  })

  if (!open) return null

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    submitHumanScore.mutate()
  }

  return (
    <>
      <div
        className="fixed inset-0 z-50 bg-black/50"
        aria-hidden
        onClick={() => onOpenChange(false)}
      />
      <div
        className="fixed right-0 top-0 z-50 h-full w-full max-w-md border-l bg-background shadow-lg flex flex-col"
        role="dialog"
        aria-label="Human review"
      >
        <div className="flex items-center justify-between border-b px-4 py-3">
          <h2 className="text-lg font-semibold flex items-center gap-2">
            <MessageSquare className="h-5 w-5 text-muted-foreground" />
            Human review
          </h2>
          <Button
            variant="ghost"
            size="icon"
            onClick={() => onOpenChange(false)}
            aria-label="Close"
          >
            <X className="h-4 w-4" />
          </Button>
        </div>

        <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
          {score ? (
            <>
              <div className="rounded-lg bg-muted/50 p-3 text-sm space-y-1">
                <p className="text-muted-foreground">
                  Conversation <span className="font-mono">{score.conversation_id.slice(0, 8)}…</span>
                  {" · "}Turn {score.turn_index}
                </p>
              </div>

              <div>
                <h3 className="text-sm font-medium mb-2">LLM score</h3>
                <div className="flex flex-wrap gap-2">
                  {Object.entries(score.scores).map(([dim, val]) => (
                    <span
                      key={dim}
                      className="inline-flex items-center rounded-md bg-primary/10 px-2 py-1 text-xs font-medium text-primary"
                    >
                      {dim}: {val}
                    </span>
                  ))}
                </div>
              </div>

              {score.raw_judge_output && (
                <details className="rounded-md border bg-muted/30">
                  <summary className="cursor-pointer px-3 py-2 text-sm text-muted-foreground hover:text-foreground">
                    Raw judge output
                  </summary>
                  <pre className="p-3 text-xs overflow-auto max-h-32 whitespace-pre-wrap border-t">
                    {score.raw_judge_output}
                  </pre>
                </details>
              )}

              {score.human_reviewed_at && (
                <p className="text-sm text-muted-foreground">
                  Last reviewed {formatDate(score.human_reviewed_at)}
                </p>
              )}

              <form onSubmit={handleSubmit} className="space-y-4 pt-2">
                <div className="space-y-2">
                  <Label htmlFor="human-score">Your score</Label>
                  <Input
                    id="human-score"
                    type="number"
                    step="any"
                    min={0}
                    placeholder="e.g. 4.5"
                    value={scoreValue}
                    onChange={(e) => setScoreValue(e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="human-comment">Comment (optional)</Label>
                  <Textarea
                    id="human-comment"
                    placeholder="Notes for this turn..."
                    value={comment}
                    onChange={(e) => setComment(e.target.value)}
                    rows={3}
                  />
                </div>
                <Button
                  type="submit"
                  disabled={submitHumanScore.isPending}
                  className="w-full"
                >
                  {submitHumanScore.isPending ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin mr-2" />
                      Saving…
                    </>
                  ) : (
                    "Save human score"
                  )}
                </Button>
                {submitHumanScore.isError && (
                  <p className="text-sm text-destructive">
                    {submitHumanScore.error instanceof Error
                      ? submitHumanScore.error.message
                      : "Failed to save. Try again."}
                  </p>
                )}
              </form>
            </>
          ) : (
            <p className="text-muted-foreground text-sm">Select a score to review.</p>
          )}
        </div>
      </div>
    </>
  )
}
