"use client"

import { useParams } from "next/navigation"
import Link from "next/link"
import { useQuery } from "@tanstack/react-query"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { ArrowLeft, Loader2, ClipboardList, MessageSquare } from "lucide-react"
import { evaluationApi } from "@/lib/api/evaluation"
import type { ScoreResponse } from "@/lib/types/evaluation"
import { HumanReviewSidePanel } from "@/components/evaluation/HumanReviewSidePanel"
import { useState } from "react"

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

function StatusBadge({ status }: { status: string }) {
  const variant =
    status === "completed"
      ? "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400"
      : status === "failed"
        ? "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400"
        : status === "running"
          ? "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400"
          : "bg-muted text-muted-foreground"
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${variant}`}
    >
      {status}
    </span>
  )
}

export default function EvaluationRunDetailPage() {
  const params = useParams()
  const runId = params.runId as string
  const [scoresSkip, setScoresSkip] = useState(0)
  const scoresLimit = 50
  const [reviewPanelOpen, setReviewPanelOpen] = useState(false)
  const [selectedScore, setSelectedScore] = useState<ScoreResponse | null>(null)

  const { data: run, isLoading: runLoading, error: runError } = useQuery({
    queryKey: ["evaluation-run", runId],
    queryFn: async () => {
      const res = await evaluationApi.getRun(runId)
      return res.data
    },
    enabled: !!runId,
  })

  const { data: scoresData, isLoading: scoresLoading } = useQuery({
    queryKey: ["evaluation-scores", runId, scoresSkip, scoresLimit],
    queryFn: async () => {
      const res = await evaluationApi.listScores(runId, {
        skip: scoresSkip,
        limit: scoresLimit,
      })
      return res.data
    },
    enabled: !!runId && !!run,
  })

  const scores = scoresData?.items ?? []
  const scoresTotal = scoresData?.total ?? 0
  const hasMoreScores = scoresSkip + scores.length < scoresTotal
  const hasPrevScores = scoresSkip > 0

  if (runLoading) {
    return (
      <div className="flex justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  if (runError || !run) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Link href="/evaluation">
            <Button variant="ghost" size="icon">
              <ArrowLeft className="h-4 w-4" />
            </Button>
          </Link>
          <div>
            <h1 className="text-3xl font-bold">Evaluation Run</h1>
          </div>
        </div>
        <Card>
          <CardContent className="pt-6">
            <p className="text-destructive">
              Run not found or failed to load. It may have been deleted.
            </p>
            <Button variant="outline" className="mt-4" asChild>
              <Link href="/evaluation">Back to Evaluation</Link>
            </Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Link href="/evaluation">
          <Button variant="ghost" size="icon">
            <ArrowLeft className="h-4 w-4" />
          </Button>
        </Link>
        <div>
          <h1 className="text-3xl font-bold">Evaluation Run</h1>
          <p className="text-muted-foreground font-mono text-sm mt-1">
            {run.id}
          </p>
        </div>
      </div>

      <Card>
        <CardHeader>
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="flex flex-wrap items-center gap-3">
              <StatusBadge status={run.status} />
              <span className="text-sm text-muted-foreground">
                {run.scope_type} • {run.score_count} score{run.score_count !== 1 ? "s" : ""}
              </span>
            </div>
            <div className="text-sm text-muted-foreground">
              Created {formatDate(run.created_at)}
            </div>
          </div>
          {run.error_message && (
            <CardDescription className="text-destructive mt-2">
              {run.error_message}
            </CardDescription>
          )}
        </CardHeader>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Scores</CardTitle>
          <CardDescription>
            LLM judge scores for each conversation turn in this run
          </CardDescription>
        </CardHeader>
        <CardContent>
          {scoresLoading && (
            <div className="flex justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          )}

          {!scoresLoading && scores.length === 0 && (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <ClipboardList className="h-10 w-10 text-muted-foreground mb-2" />
              <p className="text-muted-foreground">
                No scores yet. The run may still be pending or running.
              </p>
            </div>
          )}

          {!scoresLoading && scores.length > 0 && (
            <>
              <div className="space-y-4">
                {scores.map((score: ScoreResponse) => (
                  <Card key={score.id} className="bg-muted/30">
                    <CardContent className="pt-4">
                      <div className="flex flex-wrap items-start justify-between gap-2 mb-2">
                        <div className="flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
                          <span className="font-mono">
                            conversation: {score.conversation_id.slice(0, 8)}…
                          </span>
                          <span>•</span>
                          <span>turn {score.turn_index}</span>
                        </div>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => {
                            setSelectedScore(score)
                            setReviewPanelOpen(true)
                          }}
                          className="shrink-0"
                        >
                          <MessageSquare className="h-3.5 w-3.5 mr-1.5" />
                          {score.human_score != null ? "Edit review" : "Add review"}
                        </Button>
                      </div>
                      <div className="flex flex-wrap gap-2 mb-2">
                        {Object.entries(score.scores).map(([dim, val]) => (
                          <span
                            key={dim}
                            className="inline-flex items-center rounded-md bg-primary/10 px-2 py-1 text-xs font-medium text-primary"
                          >
                            {dim}: {val}
                          </span>
                        ))}
                      </div>
                      {score.human_score != null && (
                        <p className="text-sm text-muted-foreground mb-1">
                          Human score: {score.human_score}
                          {score.human_comment && ` — ${score.human_comment}`}
                          {score.human_reviewed_at != null && (
                            <span className="ml-1 text-xs">
                              (reviewed {formatDate(score.human_reviewed_at)})
                            </span>
                          )}
                        </p>
                      )}
                      {score.raw_judge_output && (
                        <details className="mt-2">
                          <summary className="cursor-pointer text-sm text-muted-foreground hover:text-foreground">
                            Raw judge output
                          </summary>
                          <pre className="mt-2 p-3 rounded-md bg-muted text-xs overflow-auto max-h-40 whitespace-pre-wrap">
                            {score.raw_judge_output}
                          </pre>
                        </details>
                      )}
                    </CardContent>
                  </Card>
                ))}
              </div>

              {scoresTotal > scoresLimit && (
                <div className="flex items-center justify-between mt-6 pt-4 border-t">
                  <p className="text-sm text-muted-foreground">
                    Showing {scoresSkip + 1}–{scoresSkip + scores.length} of {scoresTotal}
                  </p>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      disabled={!hasPrevScores}
                      onClick={() =>
                        setScoresSkip((s) => Math.max(0, s - scoresLimit))
                      }
                    >
                      Previous
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      disabled={!hasMoreScores}
                      onClick={() => setScoresSkip((s) => s + scoresLimit)}
                    >
                      Next
                    </Button>
                  </div>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>

      <HumanReviewSidePanel
        open={reviewPanelOpen}
        onOpenChange={setReviewPanelOpen}
        runId={runId}
        score={selectedScore}
      />
    </div>
  )
}
