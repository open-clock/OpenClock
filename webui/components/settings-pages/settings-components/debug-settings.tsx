import { API_ENDPOINT } from "@/lib/constants";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Config } from "@/lib/apitypes";
import { Switch } from "../../ui/switch";
import { Label } from "../../ui/label";
import { useEffect, useState } from "react";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "../../ui/tooltip";
import { HelpCircle, Loader2Icon } from "lucide-react";

export default function DebugSettings() {
    const [debug, setDebug] = useState(false);
    const queryClient = useQueryClient();

    const { isPending, error, data, isFetching } = useQuery<Config, Error>({
        queryKey: ['config/get'],
        queryFn: async (): Promise<Config> => {
            const response = await fetch(
                `${API_ENDPOINT}/config/get`,
            );
            return await response.json();
        },
    });

    useEffect(() => {
        if (data) {
            setDebug(data.debug);
        }
    }, [data]);

    const debugMutation = useMutation({
        mutationFn: async (isDebug: boolean) => {
            const response = await fetch(`${API_ENDPOINT}/config/setDebug?debug=${isDebug}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
            });
            return response.json();
        },
        onSuccess: () => {
            // invalidate the query
            queryClient.invalidateQueries({ queryKey: ['config/get'] });
        }
    });

    if (isPending) return (
        <div className="flex items-center justify-center">
            <Loader2Icon className="animate-spin h-6 w-6 mr-2" />
            Loading...
        </div>
    );

    if (error) return (
        <div className="min-h-screen flex items-center justify-center">
            <h1 className="text-center text-2xl">An error has occurred: {error.message}</h1>
        </div>
    );

    return (

        <div className="flex items-center space-x-2 my-2">
            <TooltipProvider>
                <Tooltip>
                    <TooltipTrigger asChild>
                        <div className="flex items-center space-x-2">
                            <Label htmlFor="debug" className="text-md">Debug</Label>
                            <HelpCircle className="w-5 h-5 text-light-secondary dark:text-dark-secondary" />
                        </div>
                    </TooltipTrigger>
                    <TooltipContent>
                        <p className="text-center">Save more verbose logs and display debug information.</p>
                    </TooltipContent>
                </Tooltip>
            </TooltipProvider>
            <Switch id="debug" checked={debug} onCheckedChange={(checked) => {
                setDebug(checked);
                debugMutation.mutate(checked);
            }} />
        </div>
    )
}