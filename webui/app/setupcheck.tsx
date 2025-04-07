"use client"
import Dashboard from '@/components/dashboard';
import SetupWizard from '@/components/setupWizard';
import { StatusResponse } from '@/lib/apitypes';
import { API_ENDPOINT } from '@/lib/constants';
import {
    useQuery,
} from '@tanstack/react-query'


export default function SetupCheck({ children }: { children: React.ReactNode }) {
    const { isPending, error, data } = useQuery<StatusResponse, Error>({
        queryKey: ['status'],
        queryFn: async (): Promise<StatusResponse> => {
            const response = await fetch(
                `${API_ENDPOINT}/status`,
            );
            return await response.json();
        },
    });

    if (isPending) return (
        <div className="min-h-screen flex items-center justify-center">
            <h1 className="text-center text-2xl">Loading...</h1>
        </div>
    );

    if (error) return (
        <div className="min-h-screen flex items-center justify-center">
            <h1 className="text-center text-2xl">An error has occurred: {error.message}</h1>
        </div>
    );

    if (!data.setup) return (
        <SetupWizard clocktype={data.model} />
    );

    return (
        <Dashboard clocktype={data.model}>
            {children}
        </Dashboard>
    )
}