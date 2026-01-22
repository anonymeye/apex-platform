"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import {
  LayoutDashboard,
  Bot,
  MessageCircle,
  Book,
  GraduationCap,
  FlaskConical,
  BarChart3,
} from "lucide-react"
import { AgentSelector } from "@/components/agents/AgentSelector"
import { cn } from "@/lib/utils/cn"

const navigation = [
  {
    name: "Home",
    href: "/home",
    icon: LayoutDashboard,
  },
  {
    name: "Agents",
    href: "/agents",
    icon: Bot,
  },
  {
    name: "Test Agent",
    href: "/test-agent",
    icon: MessageCircle,
  },
  {
    name: "Knowledge",
    href: "/knowledge",
    icon: Book,
  },
  {
    name: "Training",
    href: "/training",
    icon: GraduationCap,
  },
  {
    name: "Experiments",
    href: "/experiments",
    icon: FlaskConical,
  },
  {
    name: "Monitoring",
    href: "/monitoring",
    icon: BarChart3,
  },
]

export function Sidebar() {
  const pathname = usePathname()

  return (
    <div className="flex h-full w-64 flex-col border-r bg-background">
      {/* Logo */}
      <div className="flex h-16 items-center border-b px-6">
        <Link href="/home" className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
            <Bot className="h-5 w-5" />
          </div>
          <span className="text-lg font-semibold">Apex</span>
        </Link>
      </div>

      {/* Agent Selector */}
      <div className="border-b p-4">
        <AgentSelector />
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1 p-4">
        {navigation.map((item) => {
          const Icon = item.icon
          const isActive = pathname === item.href || pathname?.startsWith(item.href + "/")

          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                isActive
                  ? "bg-accent text-accent-foreground"
                  : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
              )}
            >
              <Icon className="h-5 w-5" />
              {item.name}
            </Link>
          )
        })}
      </nav>
    </div>
  )
}
