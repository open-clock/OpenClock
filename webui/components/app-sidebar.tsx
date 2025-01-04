"use client"

import * as React from "react"

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
        <NavMain />
      </SidebarContent>
      <SidebarFooter>
        <Copyright clocktype={clocktype} />
      </SidebarFooter>
      <SidebarRail />
    </Sidebar>
  )
}
