import { API_ENDPOINT } from "@/lib/constants";
import { DialogContent, DialogTitle } from "./ui/dialog";
import { ScrollArea } from "./ui/scroll-area";
import { SystemGetLogsResponse } from "@/lib/apitypes";
import { useQuery } from "@tanstack/react-query";
import { LucideLoaderCircle } from "lucide-react";

export default function LogViewDialogContent() {
    const { isPending, error, data, isFetching } = useQuery<SystemGetLogsResponse, Error>({
        queryKey: ['system/get_logs'],
        queryFn: async (): Promise<SystemGetLogsResponse> => {
            const response = await fetch(
                `${API_ENDPOINT}/system/get_logs`,
            );
            return await response.json();
        },
    });

    if (isPending) {
        return (
            <DialogContent>
                <DialogTitle>Logs</DialogTitle>
                <div className="flex-1 flex justify-center items-center h-[70vh]">
                    <LucideLoaderCircle className="animate-spin h-8 w-8" />
                </div>
            </DialogContent>
        );
    }

    if (error) {
        return (
            <DialogContent>
                <DialogTitle>Logs</DialogTitle>
                <ScrollArea className="h-[70vh] p-4 font-mono">
                    <p>Error: {error.message}</p>
                </ScrollArea>
            </DialogContent>
        );
    }

    return (
        <DialogContent className="min-w-[80vw]">
            <DialogTitle>Logs</DialogTitle>
            <ScrollArea className="h-[70vh] p-4 font-mono">
                <p>Logs</p>
            </ScrollArea>
        </DialogContent>
    );
}