import { DialogContent, DialogTitle } from "./ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { DialogFooter, DialogHeader } from "./ui/dialog";
import { Button } from "./ui/button";

export default function SettingsDialogContent({defaultTab = "general"}) {
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
          <TabsContent value="general">General settings.</TabsContent>
          <TabsContent value="accounts">Account settings.</TabsContent>
          <TabsContent value="intervals">Interval settings.</TabsContent>
        </Tabs>
        <DialogFooter>
          <Button type="submit">Save changes</Button>
        </DialogFooter>
      </DialogContent>
    );
}