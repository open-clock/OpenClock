import { API_ENDPOINT } from "@/lib/constants";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Skeleton } from "../ui/skeleton";
import { Config } from "@/lib/apitypes";
import { Switch } from "../ui/switch";
import { Label } from "../ui/label";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import * as z from "zod"
import {
    Accordion,
    AccordionContent,
    AccordionItem,
    AccordionTrigger,
} from "@/components/ui/accordion"
import { Input } from "../ui/input";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "../ui/tooltip";
import { HelpCircle } from "lucide-react";

const hostnameSchema = z.object({
    hostname: z
        .string()
        .min(1)
        .max(63)
        .regex(/^[a-z0-9]([a-z0-9-]*[a-z0-9])?$/, {
            message: "Hostname must contain only lowercase letters, numbers, and hyphens",
        }),
});

type FormValues = z.infer<typeof hostnameSchema>;

export default function DeviceSettingsPage() {
    const [wallMounted, setWallMounted] = useState(false);
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
            setWallMounted(data.wallmounted);
            setDebug(data.debug);
        }
    }, [data]);

    const wallmountMutation = useMutation({
        mutationFn: async (isWallmounted: boolean) => {
            const response = await fetch(`${API_ENDPOINT}/config/setWallmount?wallmount=${isWallmounted}`, {
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

    const hostnameMutation = useMutation({
        mutationFn: async (newHostname: string) => {
            const response = await fetch(`${API_ENDPOINT}/config/setHostname?hostname=${newHostname}`, {
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

    const form = useForm<FormValues>({
        resolver: zodResolver(hostnameSchema),
        defaultValues: {
            hostname: "openclock",
        },
        mode: "onChange",
    });

    useEffect(() => {
        if (data?.hostname) {
            form.reset({ hostname: data.hostname });
        }
    }, [data, form]);

    useEffect(() => {
        const subscription = form.watch((value, { name }) => {
            if (name === 'hostname' && form.formState.isValid) {
                hostnameMutation.mutate(value.hostname!);
            }
        });

        return () => subscription.unsubscribe();
    }, [form.watch]);

    if (isPending) return (
        <div>
            <h1 className="text-2xl font-semibold mb-4">Configure your device</h1>

            <p className="mb-5">
                Configure how your device should behave.
            </p>
            <Skeleton className="h-10 space-x-2" />
            <h1 className="text-xl font-semibold mt-5">Name your device</h1>
            <Skeleton className="h-10 m-1 mt-2" />
            <div className="mr-2 mt-10">
                <Accordion type="single" collapsible>
                    <AccordionItem value="advanced" >
                        <AccordionTrigger>Advanced</AccordionTrigger>
                        <AccordionContent>
                            <Skeleton className="h-10 flex items-center space-x-2" />
                        </AccordionContent>
                    </AccordionItem>
                </Accordion>
            </div>
        </div>
    );

    if (error) return (
        <div className="min-h-screen flex items-center justify-center">
            <h1 className="text-center text-2xl">An error has occurred: {error.message}</h1>
        </div>
    );

    return (
        <div>
            <h1 className="text-2xl font-semibold mb-4">Configure your device</h1>

            <p className="mb-5">
                Configure how your device should behave.
            </p>
            <div className="flex items-center space-x-2">
                <TooltipProvider>
                    <Tooltip>
                        <TooltipTrigger asChild>
                            <div className="flex items-center space-x-2">
                                <Label htmlFor="wallmounted" className="text-md">Wall mounted</Label>
                                <HelpCircle className="w-5 h-5 text-light-secondary dark:text-dark-secondary" />
                            </div>
                        </TooltipTrigger>
                        <TooltipContent>
                            <p className="text-center">Enable this option if you want to mount your device on a wall.</p>
                            <p className="text-center">Changes the orientation of the display.</p>
                        </TooltipContent>
                    </Tooltip>
                </TooltipProvider>
                <Switch id="wallmounted" checked={wallMounted} onCheckedChange={(checked) => {
                    setWallMounted(checked);
                    wallmountMutation.mutate(checked);
                }} />
            </div>
            <h1 className="text-xl font-semibold mt-5">Name your device</h1>
            <div className="m-1 mt-2">
                <Input
                    {...form.register("hostname")}
                    placeholder="Device hostname"
                />
                {form.formState.errors.hostname && (
                    <p className="text-sm text-red-500">
                        {form.formState.errors.hostname.message}
                    </p>
                )}
            </div>
            <div className="mr-2 mt-10">
                <Accordion type="single" collapsible>
                    <AccordionItem value="advanced" >
                        <AccordionTrigger>Advanced</AccordionTrigger>
                        <AccordionContent>
                            <div className="flex items-center space-x-2">
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
                        </AccordionContent>
                    </AccordionItem>
                </Accordion>
            </div>
        </div>
    );
}
