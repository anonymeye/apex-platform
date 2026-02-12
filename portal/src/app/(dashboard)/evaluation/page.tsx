"use client"

import Link from "next/link"
import { useQuery } from "@tanstack/react-query"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { ClipboardList, Loader2, ChevronRight } from "lucide-react"
import { evaluationApi } from "@/lib/api/evaluation"
import type { RunListItem } from "@/lib/types/evaluation"
import { JudgeConfigSection } from "@/components/evaluation/JudgeConfigSection"
import { useState } from "react"

const STATUS_OPTIONS = [
  { value: "", label: "All statuses" },
  { value: "pending", label: "Pending" },
  { value: "running", label: "Running" },
  { value: "completed", label: "Completed" },
  { value: "failed", label: "Failed" },
]

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

export default function EvaluationPage() {
  const [statusFilter, setStatusFilter] = useState("")
  const [skip, setSkip] = useState(0)
  const limit = 20

  const { data, isLoading, error } = useQuery({
    queryKey: ["evaluation-runs", statusFilter, skip, limit],
    queryFn: async () => {
      const res = await evaluationApi.listRuns({
        status: statusFilter || undefined,
        skip,
        limit,
      })
      return res.data
    },
  })

  const runs = data?.items ?? []
  const total = data?.total ?? 0
  const hasMore = skip + runs.length < total
  const hasPrev = skip > 0

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Evaluation</h1>
        <p className="text-muted-foreground">
          View evaluation runs and scores
        </p>
      </div>

      <JudgeConfigSection />

      <div className="flex flex-wrap items-end gap-4">
        <div className="space-y-2">
          <Label htmlFor="status">Status</Label>
          <select
            id="status"
            value={statusFilter}
            onChange={(e) => {
              setStatusFilter(e.target.value)
              setSkip(0)
            }}
            className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
          >
            {STATUS_OPTIONS.map((opt) => (
              <option key={opt.value || "all"} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {isLoading && (
        <div className="flex justify-center py-12">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </div>
      )}

      {error && (
        <Card>
          <CardContent className="pt-6">
            <p className="text-destructive">
              Failed to load evaluation runs. Please try again.
            </p>
          </CardContent>
        </Card>
      )}

      {!isLoading && !error && runs.length === 0 && (
        <Card>
          <CardContent className="pt-6">
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <ClipboardList className="h-12 w-12 text-muted-foreground mb-4" />
              <h3 className="text-lg font-semibold mb-2">No evaluation runs yet</h3>
              <p className="text-muted-foreground max-w-sm">
                Create runs via the API (POST /api/v1/evaluation/runs) with scope and judge config.
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      {!isLoading && !error && runs.length > 0 && (
        <>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {runs.map((run: RunListItem) => (
              <Link key={run.id} href={`/evaluation/${run.id}`}>
                <Card className="h-full cursor-pointer transition-shadow hover:shadow-md">
                  <CardHeader className="flex flex-row items-start justify-between space-y-0 pb-2">
                    <div className="space-y-1">
                      <CardTitle className="text-base font-medium truncate max-w-[180px]">
                        {run.id.slice(0, 8)}…
                      </CardTitle>
                      <CardDescription>
                        {run.scope_type} • {run.score_count} score{run.score_count !== 1 ? "s" : ""}
                      </CardDescription>
                    </div>
                    <ChevronRight className="h-4 w-4 text-muted-foreground shrink-0" />
                  </CardHeader>
                  <CardContent>
                    <div className="flex items-center justify-between text-sm">
                      <StatusBadge status={run.status} />
                      <span className="text-muted-foreground">
                        {formatDate(run.created_at)}
                      </span>
                    </div>
                    {run.error_message && (
                      <p className="mt-2 text-xs text-destructive truncate" title={run.error_message}>
                        {run.error_message}
                      </p>
                    )}
                  </CardContent>
                </Card>
              </Link>
            ))}
          </div>

          <div className="flex items-center justify-between">
            <p className="text-sm text-muted-foreground">
              Showing {skip + 1}–{skip + runs.length} of {total}
            </p>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                disabled={!hasPrev}
                onClick={() => setSkip((s) => Math.max(0, s - limit))}
              >
                Previous
              </Button>
              <Button
                variant="outline"
                size="sm"
                disabled={!hasMore}
                onClick={() => setSkip((s) => s + limit)}
              >
                Next
              </Button>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
