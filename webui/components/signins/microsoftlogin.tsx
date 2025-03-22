import { useQuery } from "@tanstack/react-query";
import { DialogContent, DialogTitle } from "../ui/dialog";
import { API_ENDPOINT } from "@/lib/constants";
import { MicrosoftLoginResponse } from "@/lib/apitypes";
import { Button } from "../ui/button";
import { InputOTP, InputOTPGroup, InputOTPSeparator, InputOTPSlot } from "../ui/input-otp";
import { Check, Copy, RefreshCw } from "lucide-react";
import React, { useState, useEffect, use } from "react";

export default function MicrosoftLoginDialogContent({ setMicrosoftOpen, setMicrosoftComplete }: {
    setMicrosoftOpen: (value: boolean) => void,
    setMicrosoftComplete: (value: boolean) => void
}) {
    const [copied, setCopied] = useState(false);
    const [timeLeft, setTimeLeft] = useState<string>("");
    let forceRefresh = false; // Doesnt need to survive rerender as it will fetch before that

    const { isPending, error, data, isFetching, refetch: qrefetch } = useQuery<MicrosoftLoginResponse, Error>({
        queryKey: ['microsoft/login', forceRefresh],
        queryFn: async (): Promise<MicrosoftLoginResponse> => {
            const response = await fetch(forceRefresh ? `${API_ENDPOINT}/microsoft/login?force` : `${API_ENDPOINT}/microsoft/login`);
            return response.json();
        },
        enabled: false,
    });

    const refetch = (force = false) => {
        forceRefresh = force;
        qrefetch();
    }

    useEffect(() => {
        refetch();
    }, []);

    useEffect(() => {
        if (!data?.expires_at) return;

        const updateTimer = () => {
            const now = Date.now() / 1000; // Current time in seconds
            const timeRemaining = data.expires_at - now;

            if (timeRemaining <= 0) {
                setTimeLeft("Expired");
                refetch(); // Automatically refresh when expired
                return;
            }

            const minutes = Math.floor(timeRemaining / 60);
            const seconds = Math.floor(timeRemaining % 60);
            setTimeLeft(`${minutes}:${seconds.toString().padStart(2, '0')}`);
        };

        const timer = setInterval(updateTimer, 1000);
        updateTimer(); // Initial update

        return () => clearInterval(timer);
    }, [data?.expires_at]);

    const handleCopy = () => {
        navigator.clipboard.writeText(data?.user_code || "");
        setCopied(true);
        setTimeout(() => setCopied(false), 1000);
    };

    if (isPending) return (
        <DialogContent>
            <DialogTitle>Microsoft Login</DialogTitle>
            <div className="flex items-center justify-center">
                <RefreshCw className="h-6 w-6 animate-spin" />
            </div>
        </DialogContent>
    );

    if (error) return (
        <DialogContent>
            <DialogTitle>Microsoft Login</DialogTitle>
            <h1 className="text-center text-2xl">An error has occurred: {error.message}</h1>
        </DialogContent>
    );

    return (
        <DialogContent>
            <DialogTitle>Microsoft Login</DialogTitle>
            <h1 className="">Visit the URL and enter the code below to sign in with Microsoft</h1>
            <div className="flex flex-col items-center gap-4 w-full">
                <a href={data.verification_uri} className="text-xl text-light-accent dark:text-dark-accent">
                    {data.verification_uri}
                </a>
                <div className="flex items-center justify-center gap-2">
                    <InputOTP maxLength={data.user_code.length} value={data.user_code} readOnly onClick={() => handleCopy()}>
                        {Array.from({ length: Math.ceil(data.user_code.length / 3) }).map((_, groupIndex) => (
                            <React.Fragment key={groupIndex}>
                                <InputOTPGroup key={groupIndex}>
                                    {data.user_code.slice(groupIndex * 3, (groupIndex + 1) * 3).split("").map((char, index) => (
                                        <InputOTPSlot index={groupIndex * 3 + index} key={groupIndex * 3 + index}>
                                            {char}
                                        </InputOTPSlot>
                                    ))}
                                </InputOTPGroup>
                                {groupIndex < Math.ceil(data.user_code.length / 3) - 1 && (
                                    <InputOTPSeparator />
                                )}
                            </React.Fragment>
                        ))}
                    </InputOTP>
                    <Button variant="outline" size="icon" onClick={handleCopy}>
                        {copied ? (
                            <Check className="text-light-accent dark:text-dark-accent" />
                        ) : (
                            <Copy />
                        )}
                    </Button>
                </div>
                <div className="flex items-center gap-2">
                    <span className="text-md text-light-secondary dark:text-dark-secondary">Expires in: {timeLeft}</span>
                    <Button
                        variant="outline"
                        size="icon"
                        onClick={() => refetch(true)}
                        disabled={isFetching}
                    >
                        <RefreshCw className={`${isFetching ? 'animate-spin' : ''}`} />
                    </Button>
                </div>
                <Button className="w-full" onClick={() => { handleCopy(); window.open(data.verification_uri, '_blank'); setMicrosoftOpen(false); setMicrosoftComplete(true); }}>
                    Copy and Open URL
                </Button>
                <Button className="w-full mt-10" onClick={() => { setMicrosoftOpen(false); setMicrosoftComplete(true); }}>
                    Done
                </Button>
            </div>
        </DialogContent>
    )
}