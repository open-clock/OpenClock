"use client"

import { Bot, ChevronRight, Clock, Settings2 } from "lucide-react"

import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible"
import {
  SidebarGroup,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarMenuSub,
  SidebarMenuSubButton,
  SidebarMenuSubItem,
} from "@/components/ui/sidebar"

import { Dialog, DialogTrigger } from "./ui/dialog"
import SettingsDialogContent from "./settings-dialog-content"
import TerminalDialogContent from "./terminal"

export function NavMain() {
  return (
    <SidebarGroup>
      <SidebarMenu>
        <Collapsible
          key="Dashboard"
          asChild
          defaultOpen={true}
          className="group/collapsible"
        >
          <SidebarMenuItem>
            <CollapsibleTrigger asChild>
              <SidebarMenuButton tooltip="Dashboard">
                <Clock />
                <span>Dashboard</span>
                <ChevronRight className="ml-auto transition-transform duration-200 group-data-[state=open]/collapsible:rotate-90" />
              </SidebarMenuButton>
            </CollapsibleTrigger>
            <CollapsibleContent>
              <SidebarMenuSub>
                <SidebarMenuSubItem key="Clockface">
                  <SidebarMenuSubButton asChild>
                    <a href="#">
                      <span>Clockface</span>
                    </a>
                  </SidebarMenuSubButton>
                </SidebarMenuSubItem>
                <SidebarMenuSubItem key="Widgets">
                  <SidebarMenuSubButton asChild>
                    <a href="#">
                      <span>Widgets</span>
                    </a>
                  </SidebarMenuSubButton>
                </SidebarMenuSubItem>
              </SidebarMenuSub>
            </CollapsibleContent>
          </SidebarMenuItem>
        </Collapsible>

        <Collapsible
          key="System"
          asChild
          defaultOpen={false}
          className="group/collapsible"
        >
          <SidebarMenuItem>
            <CollapsibleTrigger asChild>
              <SidebarMenuButton tooltip="System">
                <Bot />
                <span>System</span>
                <ChevronRight className="ml-auto transition-transform duration-200 group-data-[state=open]/collapsible:rotate-90" />
              </SidebarMenuButton>
            </CollapsibleTrigger>
            <CollapsibleContent>
              <SidebarMenuSub>
                <SidebarMenuSubItem key="Updates">
                  <SidebarMenuSubButton asChild>
                    <a href="#">
                      <span>Updates</span>
                    </a>
                  </SidebarMenuSubButton>
                </SidebarMenuSubItem>
                <SidebarMenuSubItem key="Logs">
                  <SidebarMenuSubButton asChild>
                    <a href="#">
                      <span>Logs</span>
                    </a>
                  </SidebarMenuSubButton>
                </SidebarMenuSubItem>
                <SidebarMenuSubItem key="Terminal">
                  <Dialog>
                    <DialogTrigger asChild>
                      <SidebarMenuSubButton asChild>
                        <a>
                          <span>Terminal</span>
                        </a>
                      </SidebarMenuSubButton>
                    </DialogTrigger>
                    <TerminalDialogContent/>
                  </Dialog>
                </SidebarMenuSubItem>
              </SidebarMenuSub>
            </CollapsibleContent>
          </SidebarMenuItem>
        </Collapsible>

        <Collapsible
          key="Settings"
          asChild
          defaultOpen={false}
          className="group/collapsible"
        >
          <SidebarMenuItem>
            <CollapsibleTrigger asChild>
              <SidebarMenuButton tooltip="Settings">
                <Settings2 />
                <span>Settings</span>
                <ChevronRight className="ml-auto transition-transform duration-200 group-data-[state=open]/collapsible:rotate-90" />
              </SidebarMenuButton>
            </CollapsibleTrigger>
            <CollapsibleContent>
              <SidebarMenuSub>
                <SidebarMenuSubItem key="General">
                  <Dialog>
                    <DialogTrigger asChild>
                      <SidebarMenuSubButton asChild>
                        <a>
                          <span>General</span>
                        </a>
                      </SidebarMenuSubButton>
                    </DialogTrigger>
                    <SettingsDialogContent defaultTab="general" />
                  </Dialog>
                </SidebarMenuSubItem>
                <SidebarMenuSubItem key="Accounts">
                  <Dialog>
                    <DialogTrigger asChild>
                      <SidebarMenuSubButton asChild>
                        <a>
                          <span>Accounts</span>
                        </a>
                      </SidebarMenuSubButton>
                    </DialogTrigger>
                    <SettingsDialogContent defaultTab="accounts" />
                  </Dialog>
                </SidebarMenuSubItem>
                <SidebarMenuSubItem key="Intervals">
                  <Dialog>
                    <DialogTrigger asChild>
                      <SidebarMenuSubButton asChild>
                        <a>
                          <span>Intervals</span>
                        </a>
                      </SidebarMenuSubButton>
                    </DialogTrigger>
                    <SettingsDialogContent defaultTab="intervals" />
                  </Dialog>
                </SidebarMenuSubItem>
              </SidebarMenuSub>
            </CollapsibleContent>
          </SidebarMenuItem>
        </Collapsible>
      </SidebarMenu>
    </SidebarGroup>
  )
}
