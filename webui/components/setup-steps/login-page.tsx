import {
    Card,
    CardContent,
    CardDescription,
    CardFooter,
    CardHeader,
    CardTitle,
} from "@/components/ui/card";
import { Dialog, DialogTrigger } from "@radix-ui/react-dialog";
import MicrosoftLoginDialogContent from "../signins/microsoftlogin";
import UntisLoginDialogContent from "../signins/untislogin";
import DiscordLoginDialogContent from "../signins/discordlogin";
import { useState } from "react";

export default function LoginPage() {
    const [microsoftOpen, setMicrosoftOpen] = useState(false);
    const [untisOpen, setUntisOpen] = useState(false);
    const [discordOpen, setDiscordOpen] = useState(false);

    return (
        <div>
            <h1 className="text-2xl font-bold mb-4">Login</h1>
            <div className="grid grid-cols-2 gap-4">
                <Dialog open={microsoftOpen} onOpenChange={setMicrosoftOpen}>
                    <DialogTrigger asChild>
                        <Card className="cursor-pointer hover:bg-light-secondary dark:hover:bg-dark-secondary">
                            <CardHeader>
                                <CardTitle>Sign in with Microsoft</CardTitle>
                                <CardDescription>Sign in with Microsoft to gain access to Teams and Outlook Notifications</CardDescription>
                            </CardHeader>
                        </Card>
                    </DialogTrigger>
                    <MicrosoftLoginDialogContent setMicrosoftOpen={setMicrosoftOpen} />
                </Dialog>
                <Dialog open={untisOpen} onOpenChange={setUntisOpen}>
                    <DialogTrigger asChild>
                        <Card className="cursor-pointer hover:bg-light-secondary dark:hover:bg-dark-secondary">
                            <CardHeader>
                                <CardTitle>Sign in with Untis</CardTitle>
                                <CardDescription>Sign in with Untis to gain access to the TimeTable view</CardDescription>
                            </CardHeader>
                        </Card>
                    </DialogTrigger>
                    <UntisLoginDialogContent setUntisOpen={setUntisOpen} />
                </Dialog>
                <Dialog open={discordOpen} onOpenChange={setDiscordOpen}>
                    <DialogTrigger asChild>
                        <Card className="cursor-pointer hover:bg-light-secondary dark:hover:bg-dark-secondary">
                            <CardHeader>
                                <CardTitle>Sign in with Discord</CardTitle>
                                <CardDescription>Sign in with Discord to gain access to Discord Notifications</CardDescription>
                            </CardHeader>
                        </Card>
                    </DialogTrigger>
                    <DiscordLoginDialogContent setDiscordOpen={setDiscordOpen} />
                </Dialog>
            </div>
        </div>
    );
}