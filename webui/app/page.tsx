"use client"
import Dashboard from '@/components/dashboard';
import SetupWizard from '@/components/setupWizard';
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
        <Example />
      </main>
    </QueryClientProvider>
  );
}

function Example() {
  const { isPending, error, data, isFetching } = useQuery({
    queryKey: ['repoData'],
    queryFn: async () => {
      const response = await fetch(
        'https://api.github.com/repos/TanStack/query',
      )
      return await response.json()
    },
  })

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

  if (data.xyz) return (
    <SetupWizard />
  );

  return (
    <Dashboard />
  )
}