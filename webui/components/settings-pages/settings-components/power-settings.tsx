import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { API_ENDPOINT } from "@/lib/constants";
import { useMutation } from "@tanstack/react-query";
import { PowerIcon, RotateCwIcon } from "lucide-react";

export default function PowerSettings() {
    const powerMutation = useMutation({
        mutationFn: async () => {
            const response = await fetch(`${API_ENDPOINT}/system/shutdown`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                },
            });
            return response.json();
        },
        onSuccess: () => {
            window.location.reload();
        }
    });

    const rebootMutation = useMutation({
        mutationFn: async () => {
            const response = await fetch(`${API_ENDPOINT}/system/reboot`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                },
            });
            return response.json();
        },
        onSuccess: () => {
            window.location.reload();
        }
    });

    return (
        <div className="flex items-center space-x-2 my-2">
            <p className="">Power:</p>
            <div className="w-5"></div>
            <TooltipProvider>
                <Tooltip>
                    <TooltipTrigger asChild>
                        <PowerIcon className="h-8 w-8 cursor-pointer" onClick={() => powerMutation.mutate()} />
                    </TooltipTrigger>
                    <TooltipContent>
                        <p>Power off the device</p>
                    </TooltipContent>
                </Tooltip>
            </TooltipProvider>
            <div className="w-5"></div>
            <TooltipProvider>
                <Tooltip>
                    <TooltipTrigger asChild>
                        <RotateCwIcon className="h-8 w-8 cursor-pointer" onClick={() => rebootMutation.mutate()} />
                    </TooltipTrigger>
                    <TooltipContent>
                        <p>Reboot the device</p>
                    </TooltipContent>
                </Tooltip>
            </TooltipProvider>
        </div>
    );
}