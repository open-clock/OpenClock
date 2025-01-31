import { DialogContent, DialogTitle } from "../ui/dialog"
import { Input } from "../ui/input"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import * as z from "zod"
import { useMutation } from "@tanstack/react-query"
import { Button } from "../ui/button"
import { useState } from "react"
import { API_ENDPOINT } from "@/lib/constants"
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion"

const loginSchema = z.object({
  username: z.string().min(1, "Username is required"),
  password: z.string().min(1, "Password is required"),
  school: z.string().min(1, "School is required"),
  server: z.string().min(1, "Server is required"),
  userAgent: z.string().optional()
})

type LoginFormData = z.infer<typeof loginSchema>

export default function UntisLoginDialogContent({ setUntisOpen }: { setUntisOpen: (value: boolean) => void }) {
  const [error, setError] = useState<string | null>(null)

  const { register, handleSubmit, formState: { errors } } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      server: "arche.webuntis.com"
    }
  })

  const loginMutation = useMutation({
    mutationFn: async (data: LoginFormData) => {
      const response = await fetch(`${API_ENDPOINT}/untis/set-creds`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      })
      if (!response.ok) {
        throw new Error('Login failed')
      }
      return response.json()
    },
    onError: (error) => {
      setError(error.message)
    },
    onSuccess: () => {
      setError(null)
      // Handle successful login here
      setUntisOpen(false)
    }
  })

  const onSubmit = (data: LoginFormData) => {
    loginMutation.mutate(data)
  }

  return (
    <DialogContent>
      <DialogTitle>Untis Login</DialogTitle>
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <div>
          <Input
            placeholder="Username"
            {...register("username")}
          />
          {errors.username && (
            <p className="text-sm text-red-500">{errors.username.message}</p>
          )}
        </div>

        <div>
          <Input
            type="password"
            placeholder="Password"
            {...register("password")}
          />
          {errors.password && (
            <p className="text-sm text-red-500">{errors.password.message}</p>
          )}
        </div>

        <div>
          <Input
            placeholder="School"
            {...register("school")}
          />
          {errors.school && (
            <p className="text-sm text-red-500">{errors.school.message}</p>
          )}
        </div>

        <div>
          <Input
            placeholder="Server"
            {...register("server")}
          />
          {errors.server && (
            <p className="text-sm text-red-500">{errors.server.message}</p>
          )}
        </div>


        <Accordion type="single" collapsible>
          <AccordionItem value="advanced">
            <AccordionTrigger>Advanced</AccordionTrigger>
            <AccordionContent>
              <div>
                <Input
                  className="m-2"
                  placeholder="User Agent (optional)"
                  {...register("userAgent")}
                />
                {errors.userAgent && (
                  <p className="text-sm text-red-500">{errors.userAgent.message}</p>
                )}
              </div>
            </AccordionContent>
          </AccordionItem>
        </Accordion>

        {error && (
          <p className="text-sm text-red-500">{error}</p>
        )}

        <Button
          type="submit"
          disabled={loginMutation.isPending}
        >
          {loginMutation.isPending ? "Logging in..." : "Login"}
        </Button>
      </form>
    </DialogContent>
  )
}