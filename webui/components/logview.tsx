import { API_ENDPOINT } from "@/lib/constants";
import { DialogContent, DialogTitle } from "./ui/dialog";
import { ScrollArea } from "./ui/scroll-area";
import { useQuery } from "@tanstack/react-query";
import { LucideLoaderCircle } from "lucide-react";
import { useState } from "react";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select"

export default function LogViewDialogContent() {
    enum LogType {
        ALL = "all",
        SYSLOG = "syslog",
        JOURNAL = "journal",
    }

    const [logType, setLogType] = useState<LogType>(LogType.ALL);
    const [logLines, setLogLines] = useState<Number>(100);
    const [logSince, setLogSince] = useState<string>();
    const [logUntil, setLogUntil] = useState<string>();
    const [logServices, setLogServices] = useState<string>();
    const [logPriority, setLogPriority] = useState<Number>();

    const { isPending, error, data, isFetching } = useQuery<String, Error>({
        queryKey: ['system/logs', logType, logLines, logSince, logUntil, logServices, logPriority],
        queryFn: async (): Promise<String> => {
            const params = new URLSearchParams();
            params.append('source', logType);
            params.append('lines', logLines.toString());

            if (logSince) params.append('since', logSince.toString());
            if (logUntil) params.append('until', logUntil.toString());
            if (logServices) params.append('services', logServices.toString());
            if (logPriority) params.append('priority', logPriority.toString());

            const response = await fetch(`${API_ENDPOINT}/system/logs?${params.toString()}`);
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
            <DialogTitle>
                <div className="flex items-center justify-between">
                    <p>Logs</p>
                    <div className="flex gap-2 mr-8">
                        <Select onValueChange={(value) => { setLogType(value as LogType) }} defaultValue={logType}>
                            <SelectTrigger>
                                <SelectValue placeholder="Log type" defaultValue="all" />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="all">All</SelectItem>
                                <SelectItem value="syslog">Syslog</SelectItem>
                                <SelectItem value="journal">Journal</SelectItem>
                            </SelectContent>
                        </Select>
                        <Select onValueChange={(value) => { setLogLines(Number.parseInt(value)) }} defaultValue={logLines.toString()} >
                            <SelectTrigger>
                                <SelectValue placeholder="Lines" />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="100">100</SelectItem>
                                <SelectItem value="200">200</SelectItem>
                                <SelectItem value="500">500</SelectItem>
                            </SelectContent>
                        </Select>
                        <Select onValueChange={(value) => { setLogSince(value === "all" ? undefined : value) }} defaultValue={logSince ? logSince : ""}>
                            <SelectTrigger>
                                <SelectValue placeholder="Since" />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="30m">30m</SelectItem>
                                <SelectItem value="1h">1h</SelectItem>
                                <SelectItem value="2d">2d</SelectItem>
                                <SelectItem value="all">All</SelectItem>
                            </SelectContent>
                        </Select>
                        <Select onValueChange={(value) => { setLogUntil(value === "all" ? undefined : value) }} defaultValue={logUntil ? logUntil : ""}>
                            <SelectTrigger>
                                <SelectValue placeholder="Until" />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="30m">30m</SelectItem>
                                <SelectItem value="1h">1h</SelectItem>
                                <SelectItem value="2d">2d</SelectItem>
                                <SelectItem value="all">All</SelectItem>
                            </SelectContent>
                        </Select>
                        <Select onValueChange={(value) => { setLogPriority(value === "all" ? undefined : Number.parseInt(value)); }} defaultValue={logPriority ? logPriority.toString() : "all"}>
                            <SelectTrigger>
                                <SelectValue placeholder="Priority" />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="0">0</SelectItem>
                                <SelectItem value="1">1</SelectItem>
                                <SelectItem value="2">2</SelectItem>
                                <SelectItem value="3">3</SelectItem>
                                <SelectItem value="4">4</SelectItem>
                                <SelectItem value="5">5</SelectItem>
                                <SelectItem value="6">6</SelectItem>
                                <SelectItem value="all">All</SelectItem>
                            </SelectContent>
                        </Select>
                        <Select onValueChange={(value) => { setLogServices(value === "all" ? undefined : value) }} defaultValue={logServices ? logServices : "all"}>
                            <SelectTrigger>
                                <SelectValue placeholder="Service" />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="nginx">Webserver</SelectItem>
                                <SelectItem value="api">API</SelectItem>
                                <SelectItem value="displaydriver">Displaydriver</SelectItem>
                                <SelectItem value="splash-boot">Bootsplash</SelectItem>
                                <SelectItem value="splash-shutdown">Shutdownsplash</SelectItem>
                                <SelectItem value="all">All</SelectItem>
                            </SelectContent>
                        </Select>
                    </div>
                </div>
            </DialogTitle>
            <ScrollArea className="h-[70vh] p-4 font-mono">
                <pre>{data}</pre>
            </ScrollArea>
        </DialogContent>
    );
}