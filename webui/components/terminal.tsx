import { useEffect, useRef, useState } from "react"
import { useMutation } from "@tanstack/react-query"
import { DialogContent, DialogTitle } from "./ui/dialog"
import { Button } from "./ui/button"
import { AlertCircle } from "lucide-react"
import {
    Alert,
    AlertDescription,
    AlertTitle,
} from "@/components/ui/alert"
import {
    Collapsible,
    CollapsibleContent,
    CollapsibleTrigger,
} from "@/components/ui/collapsible"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Input } from "@/components/ui/input"
import { API_ENDPOINT } from "@/lib/constants"
import { CommandOutput } from "@/lib/apitypes"


export default function TerminalDialogContent() {
    const [command, setCommand] = useState("")
    const [history, setHistory] = useState<Array<{ command: string, output: CommandOutput }>>([])
    const scrollRef = useRef<HTMLDivElement>(null)
    const inputRef = useRef<HTMLInputElement>(null)

    useEffect(() => {
        scrollRef.current?.scrollIntoView({ behavior: "smooth" })
        inputRef.current?.focus()
        inputRef.current?.select()
    }, [history])

    const runCommand = useMutation({
        mutationFn: async (cmd: string) => {
            const res = await fetch(`${API_ENDPOINT}/system/run`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ command: cmd }),
            })
            return res.json() as Promise<CommandOutput>
        },
        onSuccess: (data, variables) => {
            setHistory(prev => [...prev, { command: variables, output: data }])
            setCommand("")
        },
    })

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault()
        if (command.trim()) {
            runCommand.mutate(command)
        }
    }

    return (
        <DialogContent className="min-w-[80vw]">
            <DialogTitle>Terminal</DialogTitle>
            <Collapsible defaultOpen>
                <CollapsibleTrigger>
                    <CollapsibleContent>
                        <Alert variant="destructive">
                            <AlertCircle className="h-4 w-4" />
                            <AlertTitle>Warning</AlertTitle>
                            <AlertDescription>
                                This is a root terminal on your device. Be careful. Any actions you take here are on you and not covered by anyone or anything.
                            </AlertDescription>
                        </Alert>
                    </CollapsibleContent>
                </CollapsibleTrigger>
            </Collapsible>
            <ScrollArea className="h-[70vh] p-4 font-mono">
                {history.map((entry, i) => (
                    <div key={i} className="mb-4">
                        <div className="text-light-accent dark:text-dark-accent">$ {entry.command}</div>
                        <div className="whitespace-pre-wrap">
                            {entry.output.error && <span className="text-red-500">{entry.output.error}</span>}
                            {entry.output.output}
                        </div>
                    </div>
                ))}
                <div ref={scrollRef} />
            </ScrollArea>
            <form onSubmit={handleSubmit} className="flex gap-2">
                <Input
                    ref={inputRef}
                    className="flex-grow font-mono"
                    placeholder="root@localhost"
                    value={command}
                    onChange={(e) => setCommand(e.target.value)}
                    disabled={runCommand.isPending}
                />
                <Button type="submit" disabled={runCommand.isPending}>
                    {runCommand.isPending ? "Running..." : "Run"}
                </Button>
            </form>
        </DialogContent>
    )
}