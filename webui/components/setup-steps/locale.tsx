import { useState } from "react";
import { Popover, PopoverContent, PopoverTrigger } from "../ui/popover";
import { Button } from "../ui/button";
import { Check, ChevronsUpDown } from "lucide-react";
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList } from "../ui/command";
import { cn } from "@/lib/utils";
import { API_ENDPOINT } from "@/lib/constants";
import { useQuery } from "@tanstack/react-query";
import { Skeleton } from "../ui/skeleton";

export default function LocalePage() {
    const [open, setOpen] = useState(false)
    const [value, setValue] = useState("Europe/Vienna")

    const { isPending, error, data, isFetching } = useQuery<string[], Error>({
        queryKey: ['config/getTimezones'],
        queryFn: async (): Promise<string[]> => {
            const response = await fetch(
                `${API_ENDPOINT}/config/getTimezones`,
            );
            return await response.json();
        },
    });

    if (isPending) return (
        <div>
            <h1 className="text-2xl font-semibold mb-4">Select your location</h1>

            <p className="mb-4">
                Select your location to set the correct time and comply with local laws.
            </p>
            <div className="flex justify-center">
                <Skeleton className="h-10 w-96" />
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
            <h1 className="text-2xl font-semibold mb-4">Select your location</h1>

            <p className="mb-4">
                Select your location to set the correct time and comply with local laws.
            </p>
            <div className="flex justify-center">
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
        </div>
    );
}
