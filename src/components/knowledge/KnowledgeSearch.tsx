"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Search, Loader2, FileText } from "lucide-react"
import { useSearchKnowledgeBase } from "@/lib/hooks/useKnowledge"
import type { KnowledgeSearchResult } from "@/lib/types/knowledge"

interface KnowledgeSearchProps {
  kbId: string
}

export function KnowledgeSearch({ kbId }: KnowledgeSearchProps) {
  const [query, setQuery] = useState("")
  const [k, setK] = useState(5)
  const [results, setResults] = useState<KnowledgeSearchResult[] | null>(null)
  const searchMutation = useSearchKnowledgeBase()

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!query.trim()) return
    setResults(null)
    try {
      const data = await searchMutation.mutateAsync({
        kbId,
        data: { query: query.trim(), k },
      })
      setResults(data.results)
    } catch (err: any) {
      console.error("Search failed:", err)
      const message = err?.response?.data?.detail ?? err?.message ?? "Search failed"
      alert(typeof message === "string" ? message : JSON.stringify(message))
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Search className="h-5 w-5" />
          Search this knowledge base
        </CardTitle>
        <CardDescription>
          Test semantic search to verify embeddings and retrieval. Enter a query and see which chunks match.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <form onSubmit={handleSearch} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="search-query">Query</Label>
            <div className="flex gap-2">
              <Input
                id="search-query"
                placeholder="e.g. puffer jacket or wool sweater"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                disabled={searchMutation.isPending}
                className="flex-1"
              />
              <Button type="submit" disabled={!query.trim() || searchMutation.isPending}>
                {searchMutation.isPending ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <>
                    <Search className="h-4 w-4 mr-2" />
                    Search
                  </>
                )}
              </Button>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Label htmlFor="search-k" className="text-sm text-muted-foreground whitespace-nowrap">
              Results:
            </Label>
            <Input
              id="search-k"
              type="number"
              min={1}
              max={20}
              value={k}
              onChange={(e) => setK(Math.min(20, Math.max(1, parseInt(e.target.value, 10) || 1)))}
              disabled={searchMutation.isPending}
              className="w-16"
            />
          </div>
        </form>

        {results !== null && (
          <div className="space-y-3 pt-2 border-t">
            <h4 className="text-sm font-medium text-muted-foreground">
              {results.length === 0 ? "No results" : `${results.length} result(s)`}
            </h4>
            {results.length > 0 && (
              <div className="space-y-3">
                {results.map((r, i) => (
                  <div
                    key={i}
                    className="p-3 rounded-lg border bg-muted/30 space-y-1"
                  >
                    <div className="flex items-center justify-between gap-2">
                      <span className="flex items-center gap-1.5 text-xs text-muted-foreground">
                        <FileText className="h-3.5 w-3.5" />
                        Score: {(r.score * 100).toFixed(1)}%
                      </span>
                      {r.metadata && Object.keys(r.metadata).length > 0 && (
                        <span className="text-xs text-muted-foreground truncate max-w-[200px]">
                          {JSON.stringify(r.metadata)}
                        </span>
                      )}
                    </div>
                    <p className="text-sm whitespace-pre-wrap break-words line-clamp-4">
                      {r.content}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
