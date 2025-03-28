import { TabsContent } from "../ui/tabs";
import DebugSettings from "./settings-components/debug-settings";
import FactoryReset from "./settings-components/factory-reset";
import HostnameSettings from "./settings-components/hostname-settings";
import PowerSettings from "./settings-components/power-settings";
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
            <PowerSettings />
            <FactoryReset />
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