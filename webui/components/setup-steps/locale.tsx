import { useState } from "react";
import { Popover, PopoverContent, PopoverTrigger } from "../ui/popover";
import { Button } from "../ui/button";
import { Check, ChevronsUpDown } from "lucide-react";
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList } from "../ui/command";
import { cn } from "@/lib/utils";

const locales = [
    "Europe/Vienna",
    "Europe/London",
    "America/New_York",
    "America/Los_Angeles",
    "Asia/Tokyo",
    "Australia/Sydney",
];

export default function LocalePage() {
    const [open, setOpen] = useState(false)
    const [value, setValue] = useState("Europe/Vienna")

    return (
        <div>
            <h1 className="text-2xl font-semibold mb-4">Select your location</h1>

            <p className="mb-4">
                Select your location to set the correct time and comply with local laws.
            </p>
            <Popover open={open} onOpenChange={setOpen}>
                <PopoverTrigger asChild>
                    <Button
                        variant="outline"
                        role="combobox"
                        aria-expanded={open}
                        className="w-52 justify-between"
                    >
                        {value
                            ? locales.find((locales) => locales === value)
                            : "Select Location..."}
                        <ChevronsUpDown className="opacity-50" />
                    </Button>
                </PopoverTrigger>
                <PopoverContent className="w-52 p-0">
                    <Command>
                        <CommandInput placeholder="Search Location..." />
                        <CommandList>
                            <CommandEmpty>No location found.</CommandEmpty>
                            <CommandGroup>
                                {locales.map((locale) => (
                                    <CommandItem
                                        key={locale}
                                        value={locale}
                                        onSelect={(currentValue) => {
                                            setValue(currentValue === value ? "" : currentValue)
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
    );
}
