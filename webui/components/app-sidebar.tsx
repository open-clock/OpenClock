"use client"

import * as React from "react"
import {
  BookOpen,
  Bot,
  Clock,
  Settings2,
  SquareTerminal,
} from "lucide-react"

import { NavMain } from "@/components/nav-main"
import { ThemeSwitcher } from "@/components/theme-switcher"
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarRail,
} from "@/components/ui/sidebar"
import { ClockType } from "@/lib/clocktype"

// This is sample data.
const data = {
  navMain: [
    {
      title: "Dashboard",
      url: "#",
      icon: Clock,
      isActive: true,
      items: [
        {
          title: "Clockface",
          url: "#",
        },
        {
          title: "Widgets",
          url: "#",
        }
      ],
    },
    {
      title: "System",
      url: "#",
      icon: Bot,
      items: [
        {
          title: "Updates",
          url: "#",
        },
        {
          title: "Logs",
          url: "#",
        },
        {
          title: "Terminal",
          url: "#",
        }
      ],
    },
    {
      title: "Settings",
      url: "#",
      icon: Settings2,
      items: [
        {
          title: "General",
          url: "#",
        },
        {
          title: "Accounts",
          url: "#",
        },
        {
          title: "Intervals",
          url: "#",
        }
      ],
    },
  ],
}

export function AppSidebar({ ...props }: React.ComponentProps<typeof Sidebar>) {
  return (
    <Sidebar collapsible="icon" {...props}>
      <SidebarHeader>
        <ThemeSwitcher type={ClockType.Mini} />
      </SidebarHeader>
      <SidebarContent>
        <NavMain items={data.navMain} />
      </SidebarContent>
      <SidebarFooter>
        <p className="text-sm text-gray-600 dark:text-gray-400">
          OpenClock {ClockType.Mini}. AGPL V3 Licensed.
        </p>
      </SidebarFooter>
      <SidebarRail />
    </Sidebar>
  )
}
