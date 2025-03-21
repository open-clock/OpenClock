import { CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { UntisLoginNameResponse } from "@/lib/apitypes";
import { API_ENDPOINT } from "@/lib/constants";
import { useQuery } from "@tanstack/react-query";

export default function UntisCardHeader() {
    const { isPending, error, data, isFetching } = useQuery<UntisLoginNameResponse, Error>({
        queryKey: ['untis/login-name'],
        queryFn: async (): Promise<UntisLoginNameResponse> => {
            const response = await fetch(
                `${API_ENDPOINT}/untis/login-name`,
            );
            return await response.json();
        },
    });

    if (isPending || isFetching || error || !data) {
        return (
            <CardHeader>
                <CardTitle>Sign in with Untis</CardTitle>
                <CardDescription>Sign in with Untis to gain access to the TimeTable view</CardDescription>
            </CardHeader>
        );
    }

    if (data.username !== "") {
        return (
            <CardHeader>
                <CardTitle>Sign in with Untis</CardTitle>
                <CardDescription>Logged in as {data.username}</CardDescription>
            </CardHeader>
        );
    }

    return (
        <CardHeader>
            <CardTitle>Sign in with Untis</CardTitle>
            <CardDescription>Sign in with Untis to gain access to the TimeTable view</CardDescription>
        </CardHeader>
    );
}