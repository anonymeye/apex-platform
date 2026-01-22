"use client"

import { useAgentStore } from "@/lib/store/agentStore"
import { Button } from "@/components/ui/button"
import { Book } from "lucide-react"
import Link from "next/link"

export default function KnowledgePage() {
  const { selectedAgent } = useAgentStore()

  if (!selectedAgent) {
    return (
      <div className="flex h-full flex-col items-center justify-center space-y-4">
        <Book className="h-12 w-12 text-muted-foreground" />
        <div className="text-center space-y-2">
          <h2 className="text-2xl font-semibold">No Agent Selected</h2>
          <p className="text-muted-foreground">
            Please select an agent to manage its knowledge base
          </p>
          <Button asChild className="mt-4">
            <Link href="/agents">Go to Agents</Link>
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Knowledge</h1>
        <p className="text-muted-foreground">
          Agent: <span className="font-medium">{selectedAgent.name}</span>
        </p>
      </div>
      {/* Knowledge management UI will be added here */}
    </div>
  )
}
