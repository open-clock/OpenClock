"use client"

import { Check, ChevronsUpDown } from "lucide-react"

import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import {
    Command,
    CommandEmpty,
    CommandGroup,
    CommandInput,
    CommandItem,
    CommandList,
} from "@/components/ui/command"
import {
    Popover,
    PopoverContent,
    PopoverTrigger,
} from "@/components/ui/popover"
import { useState } from "react"
import { Input } from "@/components/ui/input"

const updateOptions = [
    {
        value: "url",
        label: "From URL",
    },
    {
        value: "customfile",
        label: "Custom file",
    }
]

export default function Home() {
    const [open, setOpen] = useState(false)
    const [value, setValue] = useState("")

    return (
        <div className="min-h-screen flex flex-col justify-center items-center">
            <h1 className="text-center text-4xl">Update device</h1>
            <Popover open={open} onOpenChange={setOpen}>
                <PopoverTrigger asChild>
                    <Button
                        variant="outline"
                        role="combobox"
                        aria-expanded={open}
                        className="justify-between"
                    >
                        {value
                            ? updateOptions.find((updateOption) => updateOption.value === value)?.label
                            : "Select framework..."}
                        <ChevronsUpDown className="opacity-50" />
                    </Button>
                </PopoverTrigger>
                <PopoverContent className="p-0">
                    <Command>
                        <CommandList>
                            <CommandEmpty>Select source...</CommandEmpty>
                            <CommandGroup>
                                {updateOptions.map((updateOption) => (
                                    <CommandItem
                                        key={updateOption.value}
                                        value={updateOption.value}
                                        onSelect={(currentValue) => {
                                            setValue(currentValue === value ? "" : currentValue)
                                            setOpen(false)
                                        }}
                                    >
                                        {updateOption.label}
                                        <Check
                                            className={cn(
                                                "ml-auto",
                                                value === updateOption.value ? "opacity-100" : "opacity-0"
                                            )}
                                        />
                                    </CommandItem>
                                ))}
                            </CommandGroup>
                        </CommandList>
                    </Command>
                </PopoverContent>
            </Popover>
            <div className="mt-4">
                {value === "url" && (
                    <Input
                        type="text"
                        placeholder="Enter URL"
                        className="border p-2 rounded"
                    />
                )}
                {value === "customfile" && (
                    <Input
                        type="file"
                        accept=".bin, .zip"
                        className="border p-2 rounded"
                    />
                )}
            </div>
            <Button
                className="mt-4"
                onClick={() => {
                    // Handle the update logic here
                    console.log("Update device with value:", value)
                }}
            >Update</Button>
        </div>
    );
}