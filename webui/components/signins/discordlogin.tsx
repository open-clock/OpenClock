import { DialogContent, DialogTitle } from "../ui/dialog";

export default function DiscordLoginDialogContent({ setDiscordOpen }: { setDiscordOpen: (value: boolean) => void }) {
    return (
        <DialogContent>
            <DialogTitle>Discord Login</DialogTitle>
            <h1>Discord</h1>
        </DialogContent>
    )
}