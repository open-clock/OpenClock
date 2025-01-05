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
import { ConnectNetwork, Network } from "@/lib/apitypes";
import { useMutation, useQuery } from "@tanstack/react-query";
import { API_ENDPOINT } from "@/lib/constants";
import { Skeleton } from "../ui/skeleton";
import { toast } from "sonner"

function NetworkItem({ network, onSelect }: {
    network: Network,
    onSelect: (network: Network) => void
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

function SkelNetItem() {
    return (
        <div
            className="flex items-center justify-between p-3 border rounded-lg mb-2 hover:bg-light-secondary hover:dark:bg-dark-secondary cursor-pointer"
        >
            <div className="flex items-center gap-3">
                <Skeleton className="h-5 w-5" />
                <Skeleton className="h-5 w-20" />
            </div>
        </div>
    );
}

export default function WifiPage() {
    const [selectedNetwork, setSelectedNetwork] = useState<Network | null>(null);
    const [password, setPassword] = useState("");
    const [open, setOpen] = useState(false);

    const { isPending, error, data, isFetching } = useQuery<Network[], Error>({
        queryKey: ['network/access-points'],
        queryFn: async (): Promise<Network[]> => {
            const response = await fetch(
                `${API_ENDPOINT}/network/access-points`,
            );
            return await response.json();
        },
    });

    const connectWifi = useMutation({
        mutationFn: async (network: ConnectNetwork) => {
            const res = await fetch(`${API_ENDPOINT}/network/connect`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(network),
            })
            return res.json() as Promise<{ status: string, message: string }>
        },
    })

    if (isPending) return (
        <div>
            <h1 className="text-2xl font-semibold mb-4">Connect to Wi-Fi</h1>

            <p className="mb-4">
                Connect to a Wi-Fi network to enable over-the-air updates and other features.
            </p>

            <div className="space-y-2 mb-6">
                <SkelNetItem />
                <SkelNetItem />
                <SkelNetItem />
                <SkelNetItem />
                <SkelNetItem />
                <SkelNetItem />
            </div>
        </div>
    );

    if (error) return (
        <div className="min-h-screen flex items-center justify-center">
            <h1 className="text-center text-2xl">An error has occurred: {error.message}</h1>
        </div>
    );

    const handleNetworkSelect = (network: Network) => {
        setSelectedNetwork(network);
        setOpen(true);
        setPassword("");
    };

    const handleConnect = async () => {
        if (!selectedNetwork) return;

        const response = await connectWifi.mutateAsync({
            ssid: selectedNetwork.ssid,
            password,
        });
        if (response.status) {
            data.forEach(n => {
                if (n.ssid === selectedNetwork.ssid) {
                    n.connected = true;
                } else {
                    n.connected = false;
                }
            });
            toast.success("Connected to Wi-Fi network");
        } else {
            toast.error("Failed to connect to Wi-Fi network");
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
                {data.map((network) => (
                    <NetworkItem
                        key={network.ssid + network.strength}
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