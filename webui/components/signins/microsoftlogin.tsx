import { DialogContent, DialogTitle } from "../ui/dialog";

export default function MicrosoftLoginDialogContent({ setMicrosoftOpen, setMicrosoftComplete }: { setMicrosoftOpen: (value: boolean) => void, setMicrosoftComplete: (value: boolean) => void }) {
    return (
        <DialogContent>
            <DialogTitle>Microsoft Login</DialogTitle>
            <h1>Microsoft</h1>
        </DialogContent>
    )
}