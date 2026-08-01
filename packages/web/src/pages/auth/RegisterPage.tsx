import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { Link, useNavigate } from "react-router-dom"
import { useRegister } from "@/api/auth"

const schema = z.object({
  full_name: z.string().min(2, "Name too short"),
  email: z.string().email("Invalid email"),
  password: z.string().min(8, "Minimum 8 characters"),
})
type FormData = z.infer<typeof schema>

export default function RegisterPage() {
  const navigate = useNavigate()
  const register_ = useRegister()

  const { register, handleSubmit, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema),
  })

  const onSubmit = (data: FormData) => {
    register_.mutate(data, {
      onSuccess: () => navigate("/login"),
      onError: () => {},
    })
  }

  return (
    <div className="min-h-screen bg-zinc-50 flex items-center justify-center py-12 px-4">
      <div className="bg-white rounded-2xl shadow-sm border w-full max-w-md p-8">
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold text-zinc-900">Create account</h1>
          <p className="text-zinc-500 mt-1">Start shopping today</p>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-zinc-700 mb-1">Full Name</label>
            <input
              {...register("full_name")}
              className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              placeholder="John Doe"
            />
            {errors.full_name && <p className="text-red-500 text-xs mt-1">{errors.full_name.message}</p>}
          </div>

          <div>
            <label className="block text-sm font-medium text-zinc-700 mb-1">Email</label>
            <input
              {...register("email")}
              type="email"
              className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              placeholder="you@example.com"
            />
            {errors.email && <p className="text-red-500 text-xs mt-1">{errors.email.message}</p>}
          </div>

          <div>
            <label className="block text-sm font-medium text-zinc-700 mb-1">Password</label>
            <input
              {...register("password")}
              type="password"
              className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              placeholder="Min. 8 characters"
            />
            {errors.password && <p className="text-red-500 text-xs mt-1">{errors.password.message}</p>}
          </div>

          {register_.isError && (
            <div className="bg-red-50 text-red-700 text-sm p-3 rounded-lg">
              {(register_.error as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? "Registration failed"}
            </div>
          )}

          <button
            type="submit"
            disabled={register_.isPending}
            className="w-full bg-zinc-900 text-white py-2.5 rounded-lg font-medium hover:bg-zinc-800 disabled:opacity-60 transition-colors"
          >
            {register_.isPending ? "Creating account..." : "Create account"}
          </button>
        </form>

        <p className="text-center text-sm text-zinc-500 mt-6">
          Already have an account?{" "}
          <Link to="/login" className="text-indigo-600 hover:underline">Sign in</Link>
        </p>
      </div>
    </div>
  )
}
