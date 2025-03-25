import { TabsContent } from "../ui/tabs";
import MicrosoftAccountSettings from "./settings-components/microsoft-account-settings";
import UntisAccountSettings from "./settings-components/untis-account-settings";

export default function SettingsAccountsPage() {
    return (
        <TabsContent value="accounts">
            <MicrosoftAccountSettings />
            <UntisAccountSettings />
        </TabsContent>
    );
}