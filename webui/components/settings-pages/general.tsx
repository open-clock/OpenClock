import { TabsContent } from "../ui/tabs";
import DebugSettings from "./settings-components/debug-settings";
import HostnameSettings from "./settings-components/hostname-settings";
import TimezoneSettings from "./settings-components/timezone-settings";
import WallmountedSettings from "./settings-components/wallmounted-settings";
import {
    Accordion,
    AccordionContent,
    AccordionItem,
    AccordionTrigger,
} from "@/components/ui/accordion"

export default function SettingsGeneralPage() {


    return (
        <TabsContent value="general">
            <TimezoneSettings />
            <HostnameSettings />
            <WallmountedSettings />
            <div className="mr-2 mt-10">
                <Accordion type="single" collapsible>
                    <AccordionItem value="advanced" >
                        <AccordionTrigger>Advanced</AccordionTrigger>
                        <AccordionContent>
                            <DebugSettings />
                        </AccordionContent>
                    </AccordionItem>
                </Accordion>
            </div>
        </TabsContent>
    );
}