import { Separator } from "@radix-ui/react-separator";
import { AppSidebar } from "./app-sidebar";
import { Breadcrumb, BreadcrumbList, BreadcrumbItem, BreadcrumbLink, BreadcrumbSeparator, BreadcrumbPage } from "./ui/breadcrumb";
import { SidebarProvider, SidebarInset, SidebarTrigger } from "./ui/sidebar";
import { ClockType } from "@/lib/clocktype";
import Watchface from "./watchface";

export default function Dashboard({ clocktype } : { clocktype: ClockType }) {
    return (
        <SidebarProvider>
            <AppSidebar clocktype={clocktype}/>
            <SidebarInset>
                <header className="flex h-16 shrink-0 items-center gap-2 transition-[width,height] ease-linear group-has-[[data-collapsible=icon]]/sidebar-wrapper:h-12">
                    <div className="flex items-center gap-2 px-4">
                        <SidebarTrigger className="-ml-1" />
                    </div>
                </header>
                <div className="flex items-center justify-center p-4 h-full max-h-screen">
                    <Watchface/>
                </div>
            </SidebarInset>
        </SidebarProvider>
    );
}