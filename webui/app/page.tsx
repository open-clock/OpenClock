"use client"
import Dashboard from '@/components/dashboard';
import SetupWizard from '@/components/setupWizard';
import { StatusResponse } from '@/lib/apitypes';
import {
  QueryClient,
  QueryClientProvider,
  useQuery,
} from '@tanstack/react-query'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'

const queryClient = new QueryClient()

export default function Home() {
  return (
    <QueryClientProvider client={queryClient}>
      <ReactQueryDevtools />
      <main className="">
        <App />
      </main>
    </QueryClientProvider>
  );
}

function App() {
  const { isPending, error, data, isFetching } = useQuery<StatusResponse, Error>({
    queryKey: ['status'],
    queryFn: async (): Promise<StatusResponse> => {
      const response = await fetch(
        'http://localhost:8000/status',
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
    <SetupWizard clocktype={data.model}/>
  );

  return (
    <Dashboard clocktype={data.model} />
  )
}