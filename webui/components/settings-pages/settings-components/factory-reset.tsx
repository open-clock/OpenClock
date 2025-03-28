import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { API_ENDPOINT } from "@/lib/constants";
import { useMutation } from "@tanstack/react-query";
import { useState } from "react";
import { toast } from "sonner";

export default function FactoryReset() {
    const [showSecondStage, setShowSecondStage] = useState(false);
    const [showThirdStage, setShowThirdStage] = useState(false);
    const [showFourthStage, setShowFourthStage] = useState(false);

    const FactoryResetMutation = useMutation({
        mutationFn: async () => {
            const response = await fetch(`${API_ENDPOINT}/system/factory-reset`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                },
            });
            return response.json();
        },
        onSuccess: () => {
            window.location.reload();
        }
    });

    return (
        <div className="flex items-center space-x-2 my-2">
            <p className="">Factory reset:</p>
            <div className="w-5"></div>
            <div>
                <Checkbox id="firststage" onCheckedChange={(checked) => { setShowSecondStage(checked === true) }} />
                <label
                    htmlFor="firststage"
                    className="text-sm ml-4"
                >
                    Factory reset the device
                </label>
                <div className={`${showSecondStage ? '' : 'hidden'}`}>
                    <Checkbox id="secondstage" onCheckedChange={(checked) => { setShowThirdStage(checked === true) }} />
                    <label
                        htmlFor="secondstage"
                        className="text-sm ml-4"
                    >
                        I am sure I want to factory reset the device
                    </label>
                    <div className={`${showThirdStage ? '' : 'hidden'}`}>
                        <Checkbox id="secondstage" onCheckedChange={(checked) => { setShowFourthStage(checked === true) }} />
                        <label
                            htmlFor="secondstage"
                            className="text-sm ml-4"
                        >
                            I know this will erase all data on the device
                        </label>
                        <Button className={`m-4 ${showFourthStage ? '' : 'hidden'}`} onClick={() => {
                            FactoryResetMutation.mutate();
                            setShowFourthStage(false);
                            setShowThirdStage(false);
                            setShowSecondStage(false);
                            toast.info("Factory reset in progress. This may take a while.");
                        }} >Factory reset</Button>
                    </div>
                </div>
            </div>

        </div>
    );
}