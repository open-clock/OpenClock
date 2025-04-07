import { AppSidebar } from "./app-sidebar";
import { SidebarProvider, SidebarInset, SidebarTrigger } from "./ui/sidebar";
import { ClockType } from "@/lib/clocktype";

export default function Dashboard({ children, clocktype }: { children: React.ReactNode, clocktype: ClockType }) {
    return (
        <SidebarProvider>
            <AppSidebar clocktype={clocktype} />
            <SidebarInset>
                <header className="flex h-16 shrink-0 items-center gap-2 transition-[width,height] ease-linear group-has-[[data-collapsible=icon]]/sidebar-wrapper:h-12">
                    <div className="flex items-center gap-2 px-4">
                        <SidebarTrigger className="-ml-1" />
                    </div>
                </header>
                <div className="flex items-center justify-center p-4 h-full max-h-screen">
                    {children}
                </div>
            </SidebarInset>
        </SidebarProvider>
    );
}