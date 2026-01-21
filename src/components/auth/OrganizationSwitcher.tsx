"use client"

import { useState } from "react"
import { useAuth } from "@/lib/hooks/useAuth"
import { Button } from "@/components/ui/button"
import { Building2, Check, ChevronDown } from "lucide-react"

/**
 * Organization switcher component for multi-org support.
 * Allows users to switch between organizations they belong to.
 */
export function OrganizationSwitcher() {
  const { user, switchOrg } = useAuth()
  const [isSwitching, setIsSwitching] = useState(false)
  const [isOpen, setIsOpen] = useState(false)

  // Only show if user has multiple organizations
  if (!user || user.organizations.length <= 1) {
    return null
  }

  const currentOrg = user.organizations.find((org) => org.id === user.currentOrgId)

  const handleSwitch = async (orgId: string) => {
    if (orgId === user.currentOrgId) return

    setIsSwitching(true)
    try {
      await switchOrg(orgId)
    } catch (error) {
      console.error("Failed to switch organization:", error)
      // TODO: Show error toast
    } finally {
      setIsSwitching(false)
    }
  }

  return (
    <div className="relative">
      <Button
        variant="outline"
        className="w-full justify-between"
        disabled={isSwitching}
        onClick={() => setIsOpen(!isOpen)}
      >
        <div className="flex items-center">
          <Building2 className="mr-2 h-4 w-4" />
          <span className="truncate">{currentOrg?.name || "Select Organization"}</span>
        </div>
        <ChevronDown className="ml-2 h-4 w-4" />
      </Button>
      {isOpen && (
        <>
          <div
            className="fixed inset-0 z-10"
            onClick={() => setIsOpen(false)}
          />
          <div className="absolute top-full left-0 right-0 z-20 mt-1 rounded-md border bg-popover shadow-md">
            <div className="p-2">
              <div className="px-2 py-1.5 text-sm font-semibold">Organizations</div>
              <div className="border-t my-1" />
              {user.organizations.map((org) => (
                <button
                  key={org.id}
                  onClick={() => {
                    handleSwitch(org.id)
                    setIsOpen(false)
                  }}
                  disabled={isSwitching}
                  className="w-full px-2 py-2 text-left rounded-sm hover:bg-accent flex items-center justify-between"
                >
                  <div className="flex flex-col">
                    <span className="text-sm font-medium">{org.name}</span>
                    <span className="text-xs text-muted-foreground capitalize">{org.role}</span>
                  </div>
                  {org.id === user.currentOrgId && <Check className="h-4 w-4" />}
                </button>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  )
}
