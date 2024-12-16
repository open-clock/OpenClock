export default function WifiPage() {
    return (
        <div>
            <h1 className="text-2xl font-semibold mb-4">Connect to Wi-Fi</h1>

            <p className="mb-4">
                Connect to a Wi-Fi network to enable over-the-air updates and other features.
            </p>

            <div className="mb-4">
                <label className="block mb-2">Network Name (SSID)</label>
                <input type="text" className="w-full px-3 py-2 border rounded" />
            </div>

            <div className="mb-4">
                <label className="block mb-2">Password</label>
                <input type="password" className="w-full px-3 py-2 border rounded" />
            </div>
        </div>
    );
}