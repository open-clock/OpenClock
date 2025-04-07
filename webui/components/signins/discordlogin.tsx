import { DialogContent, DialogTitle } from "../ui/dialog";

// eslint-disable-next-line @typescript-eslint/no-unused-vars
export default function DiscordLoginDialogContent({ setDiscordOpen, setDiscordComplete }: { setDiscordOpen: (value: boolean) => void, setDiscordComplete: (value: boolean) => void }) {
    return (
        <DialogContent>
            <DialogTitle>Discord Login</DialogTitle>
            <h1>Discord</h1>
        </DialogContent>
    )
}