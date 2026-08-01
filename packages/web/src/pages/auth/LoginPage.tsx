import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { Link, useNavigate, useSearchParams } from "react-router-dom"
import { useLogin } from "@/api/auth"

const schema = z.object({
  email: z.string().email("Invalid email"),
  password: z.string().min(1, "Password required"),
})
type FormData = z.infer<typeof schema>

export default function LoginPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const redirect = searchParams.get("redirect") ?? "/"
  const login = useLogin()

  const { register, handleSubmit, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema),
  })

  const onSubmit = (data: FormData) => {
    login.mutate(data, {
      onSuccess: () => navigate(redirect),
      onError: () => {},
    })
  }

  return (
    <div className="min-h-screen bg-cream flex items-center justify-center py-12 px-4">
      <div className="bg-white rounded-2xl shadow-sm border w-full max-w-md p-8">
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold text-charcoal">Welcome back</h1>
          <p className="text-charcoal/70 mt-1">Sign in to your account</p>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-charcoal/80 mb-1">Email</label>
            <input
              {...register("email")}
              type="email"
              className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand"
              placeholder="you@example.com"
            />
            {errors.email && <p className="text-red-500 text-xs mt-1">{errors.email.message}</p>}
          </div>

          <div>
            <label className="block text-sm font-medium text-charcoal/80 mb-1">Password</label>
            <input
              {...register("password")}
              type="password"
              className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand"
              placeholder="••••••••"
            />
            {errors.password && <p className="text-red-500 text-xs mt-1">{errors.password.message}</p>}
          </div>

          {login.isError && (
            <div className="bg-red-50 text-red-700 text-sm p-3 rounded-lg">
              Invalid email or password
            </div>
          )}

          <button
            type="submit"
            disabled={login.isPending}
            className="w-full bg-brand text-white py-2.5 rounded-lg font-medium hover:bg-brand/90 disabled:opacity-60 transition-colors"
          >
            {login.isPending ? "Signing in..." : "Sign in"}
          </button>
        </form>

        <p className="text-center text-sm text-charcoal/70 mt-6">
          Don't have an account?{" "}
          <Link to="/register" className="text-brand hover:underline">Register</Link>
        </p>
      </div>
    </div>
  )
}
