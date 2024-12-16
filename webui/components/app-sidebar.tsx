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
import Copyright from "./copyright"

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

export function AppSidebar({ 
  clocktype,
  ...props 
}: React.ComponentProps<typeof Sidebar> & {
  clocktype: ClockType
}) {
  return (
    <Sidebar collapsible="icon" {...props}>
      <SidebarHeader>
        <ThemeSwitcher type={clocktype} />
      </SidebarHeader>
      <SidebarContent>
        <NavMain items={data.navMain} />
      </SidebarContent>
      <SidebarFooter>
        <Copyright clocktype={clocktype} />
      </SidebarFooter>
      <SidebarRail />
    </Sidebar>
  )
}
