import { DialogContent, DialogTitle } from "./ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { DialogFooter, DialogHeader } from "./ui/dialog";
import { Button } from "./ui/button";
import SettingsGeneralPage from "./settings-pages/general";
import SettingsAccountsPage from "./settings-pages/accounts";
import SettingsIntervalsPage from "./settings-pages/intervals";

export default function SettingsDialogContent({ defaultTab = "general" }) {
  return (
    <DialogContent className="">
      <Tabs defaultValue={defaultTab} className="">
        <DialogHeader>
          <DialogTitle>Settings</DialogTitle>
          <TabsList>
            <TabsTrigger value="general">General</TabsTrigger>
            <TabsTrigger value="accounts">Accounts</TabsTrigger>
            <TabsTrigger value="intervals">Intervals</TabsTrigger>
          </TabsList>
        </DialogHeader>
        <SettingsGeneralPage />
        <SettingsAccountsPage />
        <SettingsIntervalsPage />
      </Tabs>
      <DialogFooter>
        <Button type="submit">OK</Button>
      </DialogFooter>
    </DialogContent>
  );
}