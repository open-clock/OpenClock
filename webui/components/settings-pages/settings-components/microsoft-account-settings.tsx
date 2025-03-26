import { MicrosoftGetAccountsResponse } from "@/lib/apitypes";
import { API_ENDPOINT } from "@/lib/constants";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Loader2Icon, Trash2Icon } from "lucide-react";
import { toast } from "sonner";

export default function MicrosoftAccountSettings() {
    const queryClient = useQueryClient();

    const { isPending, error, data, isFetching } = useQuery<MicrosoftGetAccountsResponse[], Error>({
        queryKey: ['microsoft/accounts'],
        queryFn: async (): Promise<MicrosoftGetAccountsResponse[]> => {
            const response = await fetch(
                `${API_ENDPOINT}/microsoft/accounts`,
            );
            return await response.json();
        },
    });

    const LogoutMutation = useMutation({
        mutationFn: async (): Promise<{ status: string, message: string }> => {
            const response = await fetch(`${API_ENDPOINT}/microsoft/logout`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
            });
            return response.json();
        },
        onError: (error) => {
            toast.error(error.message);
        },
        onSuccess: (data) => {
            if (data.status === 'error') {
                toast.error(data.message);
                return;
            }
            toast.success('Logged out of Microsoft account');
            queryClient.invalidateQueries({ queryKey: ['microsoft/accounts'] });
        }
    });



    if (isPending) return (
        <div className="flex items-center justify-center">
            <Loader2Icon className="animate-spin h-6 w-6 mr-2" />
            Loading...
        </div>
    );

    if (error) return (
        <div className="flex items-center justify-center">
            <h1 className="text-center text-xl">An error has occurred: {error.message}</h1>
        </div>
    );

    if (data.length === 0) return (
        <div>
            <h1 className="text-2xl font-semibold">Microsoft Account</h1>
            <div className="mt-4">
                <div className="p-4 mb-4">
                    <h2 className="text-lg font-semibold">No accounts connected</h2>
                    <p className="text-sm text-gray-500">You have not connected any Microsoft accounts yet.</p>
                </div>
            </div>
        </div>
    );

    return (
        <div>
            <h1 className="text-2xl font-semibold">Microsoft Account</h1>
            <div className="mt-4">
                {data.map((account) => (
                    <div key={account.home_account_id} className="rounded-lg p-4 shadow-md mb-4 flex justify-between items-center">
                        <div>
                            <h2 className="text-lg font-semibold">{account.username}</h2>
                            <p className="text-sm text-gray-500">{account.environment}</p>
                        </div>
                        <Trash2Icon className="w-6 h-6 text-red-500 cursor-pointer" onClick={() => { LogoutMutation.mutate(); }} />
                    </div>
                ))}
            </div>
        </div>
    );
}
