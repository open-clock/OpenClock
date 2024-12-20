import { Wifi, Check } from "lucide-react";
import { useState } from "react";
import { Button } from "../ui/button";
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogFooter,
} from "../ui/dialog";
import { Input } from "../ui/input";

const Networks = [
    { ssid: "MyNetwork", strength: 4, connected: false },
    { ssid: "OtherNetwork", strength: 2, connected: true },
    { ssid: "OpenNetwork", strength: 1, connected: false },
];

async function connectToWifi(ssid: string, password: string) {
    // Simulate a connection attempt
    await new Promise((resolve) => setTimeout(resolve, 1000));
    return true;
}

function NetworkItem({ network, onSelect }: {
    network: typeof Networks[0],
    onSelect: (network: typeof Networks[0]) => void
}) {
    const getWifiIcon = () => {
        const size = 20;
        const className = network.strength === 0 ? "text-light-text dark:text-dark-text" : "text-light-accent dark:text-dark-accent";
        return <Wifi size={size} className={className} opacity={0.25 * network.strength} />;
    };

    return (
        <div
            className="flex items-center justify-between p-3 border rounded-lg mb-2 hover:bg-light-secondary hover:dark:bg-dark-secondary cursor-pointer"
            onClick={() => !network.connected && onSelect(network)}
        >
            <div className="flex items-center gap-3">
                {getWifiIcon()}
                <span>{network.ssid}</span>
            </div>
            {network.connected && <Check size={20} className="text-light-text dark:text-dark-text" />}
        </div>
    );
}

export default function WifiPage() {
    const [selectedNetwork, setSelectedNetwork] = useState<typeof Networks[0] | null>(null);
    const [password, setPassword] = useState("");
    const [open, setOpen] = useState(false);

    const handleNetworkSelect = (network: typeof Networks[0]) => {
        setSelectedNetwork(network);
        setOpen(true);
        setPassword("");
    };

    const handleConnect = async () => {
        if (!selectedNetwork) return;

        const success = await connectToWifi(selectedNetwork.ssid, password);
        if (success) {
            Networks.forEach(n => {
                if (n.ssid === selectedNetwork.ssid) {
                    n.connected = true;
                } else {
                    n.connected = false;
                }
            });
        }
        setOpen(false);
    };

    return (
        <div>
            <h1 className="text-2xl font-semibold mb-4">Connect to Wi-Fi</h1>

            <p className="mb-4">
                Connect to a Wi-Fi network to enable over-the-air updates and other features.
            </p>

            <div className="space-y-2 mb-6">
                {Networks.map((network) => (
                    <NetworkItem
                        key={network.ssid}
                        network={network}
                        onSelect={handleNetworkSelect}
                    />
                ))}
            </div>

            <Dialog open={open} onOpenChange={setOpen}>
                <DialogContent>
                    <DialogHeader>
                        <DialogTitle>Connect to {selectedNetwork?.ssid}</DialogTitle>
                    </DialogHeader>
                    <div className="py-4">
                        <Input
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            placeholder="Enter password"
                        />
                    </div>
                    <DialogFooter>
                        <Button variant="outline" onClick={() => setOpen(false)}>
                            Cancel
                        </Button>
                        <Button onClick={handleConnect}>
                            Connect
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </div>
    );
}