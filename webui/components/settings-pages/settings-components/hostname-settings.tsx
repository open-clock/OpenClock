import { API_ENDPOINT } from "@/lib/constants";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Config } from "@/lib/apitypes";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import * as z from "zod"
import { Input } from "../../ui/input";
import { Loader2Icon } from "lucide-react";

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

export default function HostnameSettings() {
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
        <div className="flex justify-center items-center my-2">
            <p className="">Hostname:</p>
            <div className="w-5"></div>
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

    );
}