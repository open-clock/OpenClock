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
import { CheckCircle } from "lucide-react";
import UntisCardHeader from "./setup-components/untis-card-header";

export default function LoginPage() {
    const [microsoftOpen, setMicrosoftOpen] = useState(false);
    const [microsoftComplete, setMicrosoftComplete] = useState(false);
    const [untisOpen, setUntisOpen] = useState(false);
    const [untisComplete, setUntisComplete] = useState(false);
    const [discordOpen, setDiscordOpen] = useState(false);
    const [discordComplete, setDiscordComplete] = useState(false);

    return (
        <div>
            <h1 className="text-2xl font-bold mb-4">Login</h1>
            <div className="grid grid-cols-2 gap-4">
                <Dialog open={microsoftOpen} onOpenChange={setMicrosoftOpen}>
                    <DialogTrigger asChild>
                        <Card className="cursor-pointer hover:bg-light-secondary dark:hover:bg-dark-secondary relative">
                            {microsoftComplete && (
                                <div className="absolute top-2 right-2 text-light-accent dark:text-dark-accent">
                                    <CheckCircle size={24} />
                                </div>
                            )}
                            <CardHeader>
                                <CardTitle>Sign in with Microsoft</CardTitle>
                                <CardDescription>Sign in with Microsoft to gain access to Teams and Outlook Notifications</CardDescription>
                            </CardHeader>
                        </Card>
                    </DialogTrigger>
                    <MicrosoftLoginDialogContent setMicrosoftOpen={setMicrosoftOpen} setMicrosoftComplete={setMicrosoftComplete} />
                </Dialog>
                <Dialog open={untisOpen} onOpenChange={setUntisOpen}>
                    <DialogTrigger asChild>
                        <Card className="cursor-pointer hover:bg-light-secondary dark:hover:bg-dark-secondary relative">
                            {untisComplete && (
                                <div className="text-light-accent dark:text-dark-accent absolute top-2 right-2">
                                    <CheckCircle size={24} />
                                </div>
                            )}
                            <UntisCardHeader />
                        </Card>
                    </DialogTrigger>
                    <UntisLoginDialogContent setUntisOpen={setUntisOpen} setUntisComplete={setUntisComplete} />
                </Dialog>
                <Dialog open={discordOpen} onOpenChange={setDiscordOpen}>
                    <DialogTrigger asChild>
                        <Card className="cursor-pointer hover:bg-light-secondary dark:hover:bg-dark-secondary relative">
                            {discordComplete && (
                                <div className="absolute top-2 right-2 text-light-accent dark:text-dark-accent">
                                    <CheckCircle size={24} />
                                </div>
                            )}
                            <CardHeader>
                                <CardTitle>Sign in with Discord</CardTitle>
                                <CardDescription>Sign in with Discord to gain access to Discord Notifications</CardDescription>
                            </CardHeader>
                        </Card>
                    </DialogTrigger>
                    <DiscordLoginDialogContent setDiscordOpen={setDiscordOpen} setDiscordComplete={setDiscordComplete} />
                </Dialog>
            </div>
        </div>
    );
}