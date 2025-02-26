import { Loader2Icon } from "lucide-react";
import { useEffect, useState } from "react";
import { Popover, PopoverContent, PopoverTrigger } from "../../ui/popover";
import { Button } from "../../ui/button";
import { Check, ChevronsUpDown } from "lucide-react";
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList } from "../../ui/command";
import { cn } from "@/lib/utils";
import { API_ENDPOINT } from "@/lib/constants";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

export default function TimezoneSettings() {
    const [open, setOpen] = useState(false)
    const [value, setValue] = useState("Europe/Vienna")
    const queryClient = useQueryClient();

    const { isPending, error, data, isFetching } = useQuery<string[], Error>({
        queryKey: ['config/getTimezones'],
        queryFn: async (): Promise<string[]> => {
            const response = await fetch(
                `${API_ENDPOINT}/config/getTimezones`,
            );
            return await response.json();
        },
    });

    const timezoneQuery = useQuery<string, Error>({
        queryKey: ['config/getTimezone'],
        queryFn: async (): Promise<string> => {
            const response = await fetch(
                `${API_ENDPOINT}/config/getTimezone`,
            );
            return await response.json();
        },
    });

    const timezoneMutation = useMutation({
        mutationFn: async (newTimezone: string) => {
            const response = await fetch(`${API_ENDPOINT}/config/setTimezone?timezone=${newTimezone}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
            });
            return response.json();
        },
        onSuccess: () => {
            // invalidate the query
            queryClient.invalidateQueries({ queryKey: ['config/getTimezone'] });
        }
    });

    useEffect(() => {
        setValue(timezoneQuery.data || "Europe/Vienna")
    }, [timezoneQuery.data]);


    if (isPending || timezoneQuery.isPending) return (
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

    if (timezoneQuery.error) return (
        <div className="min-h-screen flex items-center justify-center">
            <h1 className="text-center text-2xl">An error has occurred: {timezoneQuery.error.message}</h1>
        </div>
    );
    return (
        <div className="flex justify-center items-center my-2">
            <p className="">Timezone:</p>
            <div className="w-5"></div>
            <Popover open={open} onOpenChange={setOpen}>
                <PopoverTrigger asChild>
                    <Button
                        variant="outline"
                        role="combobox"
                        aria-expanded={open}
                        className="w-96 justify-between"
                    >
                        {value
                            ? data.find((locales) => locales === value)
                            : "Select Location..."}
                        <ChevronsUpDown className="opacity-50" />
                    </Button>
                </PopoverTrigger>
                <PopoverContent className="w-96 p-0">
                    <Command>
                        <CommandInput placeholder="Search Location..." />
                        <CommandList>
                            <CommandEmpty>No location found.</CommandEmpty>
                            <CommandGroup>
                                {data.map((locale) => (
                                    <CommandItem
                                        key={locale}
                                        value={locale}
                                        onSelect={(currentValue) => {
                                            setValue(currentValue)
                                            setOpen(false)
                                            timezoneMutation.mutate(currentValue)
                                        }}
                                    >
                                        {locale}
                                        <Check
                                            className={cn(
                                                "ml-auto",
                                                value === locale ? "opacity-100" : "opacity-0"
                                            )}
                                        />
                                    </CommandItem>
                                ))}
                            </CommandGroup>
                        </CommandList>
                    </Command>
                </PopoverContent>
            </Popover>
        </div>
    );
}