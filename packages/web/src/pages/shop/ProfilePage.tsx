import { useState } from "react"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { useAuthStore } from "@/store/authStore"
import { useUpdateMe, useChangePassword } from "@/api/auth"
import { useAddresses, useCreateAddress, useDeleteAddress, useSetDefaultAddress } from "@/api/addresses"
import { formatDate } from "@/lib/utils"
import { MapPin, Plus, Trash2, Star } from "lucide-react"

type Tab = "profile" | "password" | "addresses"

const profileSchema = z.object({
  full_name: z.string().min(2),
  email: z.string().email(),
})
const passwordSchema = z.object({
  current_password: z.string().min(1),
  new_password: z.string().min(8),
})
type ProfileForm = z.infer<typeof profileSchema>
type PasswordForm = z.infer<typeof passwordSchema>

export default function ProfilePage() {
  const { user } = useAuthStore()
  const [tab, setTab] = useState<Tab>("profile")
  const updateMe = useUpdateMe()
  const changePassword = useChangePassword()
  const { data: addresses } = useAddresses()
  const createAddress = useCreateAddress()
  const deleteAddress = useDeleteAddress()
  const setDefault = useSetDefaultAddress()
  const [showAddForm, setShowAddForm] = useState(false)
  const [newAddr, setNewAddr] = useState({ street: "", city: "", country: "", postal_code: "", state: "", label: "" })
  const [profileSuccess, setProfileSuccess] = useState(false)
  const [passwordSuccess, setPasswordSuccess] = useState(false)

  const profileForm = useForm<ProfileForm>({
    resolver: zodResolver(profileSchema),
    defaultValues: { full_name: user?.full_name ?? "", email: user?.email ?? "" },
  })
  const passwordForm = useForm<PasswordForm>({ resolver: zodResolver(passwordSchema) })

  const onProfileSubmit = (data: ProfileForm) => {
    updateMe.mutate(data, { onSuccess: () => { setProfileSuccess(true); setTimeout(() => setProfileSuccess(false), 3000) } })
  }
  const onPasswordSubmit = (data: PasswordForm) => {
    changePassword.mutate(data, { onSuccess: () => { setPasswordSuccess(true); passwordForm.reset(); setTimeout(() => setPasswordSuccess(false), 3000) } })
  }
  const handleAddAddress = (e: React.FormEvent) => {
    e.preventDefault()
    createAddress.mutate(newAddr, { onSuccess: () => { setShowAddForm(false); setNewAddr({ street: "", city: "", country: "", postal_code: "", state: "", label: "" }) } })
  }

  const tabs: { key: Tab; label: string }[] = [
    { key: "profile", label: "Profile" },
    { key: "password", label: "Password" },
    { key: "addresses", label: "Addresses" },
  ]

  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold text-charcoal mb-2">Account Settings</h1>
      <p className="text-charcoal/70 text-sm mb-8">Member since {user?.created_at ? formatDate(user.created_at) : ""}</p>

      {/* Tabs */}
      <div className="flex gap-1 bg-sage/20 p-1 rounded-xl mb-8 w-fit">
        {tabs.map(({ key, label }) => (
          <button
            key={key}
            onClick={() => setTab(key)}
            className={`px-5 py-2 rounded-lg text-sm font-medium transition-all ${
              tab === key ? "bg-white shadow-sm text-charcoal" : "text-charcoal/70 hover:text-charcoal"
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {/* Profile Tab */}
      {tab === "profile" && (
        <div className="bg-white border border-sage/30 rounded-card shadow-soft p-6">
          <h2 className="font-semibold text-charcoal mb-6">Personal Information</h2>
          <form onSubmit={profileForm.handleSubmit(onProfileSubmit)} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-charcoal/80 mb-1">Full Name</label>
              <input
                {...profileForm.register("full_name")}
                className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand"
              />
              {profileForm.formState.errors.full_name && (
                <p className="text-red-500 text-xs mt-1">{profileForm.formState.errors.full_name.message}</p>
              )}
            </div>
            <div>
              <label className="block text-sm font-medium text-charcoal/80 mb-1">Email</label>
              <input
                {...profileForm.register("email")}
                type="email"
                className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand"
              />
              {profileForm.formState.errors.email && (
                <p className="text-red-500 text-xs mt-1">{profileForm.formState.errors.email.message}</p>
              )}
            </div>
            {profileSuccess && <p className="text-green-600 text-sm">Profile updated successfully!</p>}
            <button
              type="submit"
              disabled={updateMe.isPending}
              className="bg-brand text-white px-6 py-2 rounded-lg text-sm font-medium hover:bg-brand/90 disabled:opacity-60"
            >
              {updateMe.isPending ? "Saving..." : "Save Changes"}
            </button>
          </form>
        </div>
      )}

      {/* Password Tab */}
      {tab === "password" && (
        <div className="bg-white border border-sage/30 rounded-card shadow-soft p-6">
          <h2 className="font-semibold text-charcoal mb-6">Change Password</h2>
          <form onSubmit={passwordForm.handleSubmit(onPasswordSubmit)} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-charcoal/80 mb-1">Current Password</label>
              <input
                {...passwordForm.register("current_password")}
                type="password"
                className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-charcoal/80 mb-1">New Password</label>
              <input
                {...passwordForm.register("new_password")}
                type="password"
                className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand"
              />
              {passwordForm.formState.errors.new_password && (
                <p className="text-red-500 text-xs mt-1">{passwordForm.formState.errors.new_password.message}</p>
              )}
            </div>
            {changePassword.isError && (
              <p className="text-red-600 text-sm">Incorrect current password</p>
            )}
            {passwordSuccess && <p className="text-green-600 text-sm">Password changed successfully!</p>}
            <button
              type="submit"
              disabled={changePassword.isPending}
              className="bg-brand text-white px-6 py-2 rounded-lg text-sm font-medium hover:bg-brand/90 disabled:opacity-60"
            >
              {changePassword.isPending ? "Updating..." : "Update Password"}
            </button>
          </form>
        </div>
      )}

      {/* Addresses Tab */}
      {tab === "addresses" && (
        <div className="space-y-4">
          {addresses?.map((addr) => (
            <div key={addr.id} className="bg-white border border-sage/30 rounded-card shadow-soft p-5 flex items-start justify-between">
              <div className="flex items-start gap-3">
                <MapPin size={18} className="text-charcoal/70 mt-0.5 flex-none" />
                <div>
                  {addr.label && <p className="font-medium text-charcoal">{addr.label}</p>}
                  <p className="text-sm text-charcoal/70">{addr.street}, {addr.city}</p>
                  <p className="text-sm text-charcoal/70">{addr.country} {addr.postal_code}</p>
                  {addr.is_default && <span className="text-xs text-brand font-medium">Default</span>}
                </div>
              </div>
              <div className="flex gap-2">
                {!addr.is_default && (
                  <button
                    onClick={() => setDefault.mutate(addr.id)}
                    className="p-1.5 text-charcoal/70 hover:text-yellow-500"
                    title="Set as default"
                  >
                    <Star size={16} />
                  </button>
                )}
                <button
                  onClick={() => deleteAddress.mutate(addr.id)}
                  className="p-1.5 text-charcoal/70 hover:text-red-500"
                >
                  <Trash2 size={16} />
                </button>
              </div>
            </div>
          ))}

          <button
            onClick={() => setShowAddForm(!showAddForm)}
            className="flex items-center gap-2 text-brand text-sm hover:underline"
          >
            <Plus size={16} /> Add new address
          </button>

          {showAddForm && (
            <form onSubmit={handleAddAddress} className="bg-white border border-sage/30 rounded-card shadow-soft p-5 grid grid-cols-2 gap-3">
              {[
                { key: "label", placeholder: "Label (optional)", full: true },
                { key: "street", placeholder: "Street address", full: true },
                { key: "city", placeholder: "City" },
                { key: "state", placeholder: "State" },
                { key: "country", placeholder: "Country" },
                { key: "postal_code", placeholder: "Postal code" },
              ].map(({ key, placeholder, full }) => (
                <input
                  key={key}
                  placeholder={placeholder}
                  value={(newAddr as Record<string, string>)[key]}
                  onChange={(e) => setNewAddr({ ...newAddr, [key]: e.target.value })}
                  className={`border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand ${full ? "col-span-2" : ""}`}
                />
              ))}
              <button
                type="submit"
                className="col-span-2 bg-brand text-white py-2 rounded-lg text-sm font-medium hover:bg-brand/90"
              >
                Save Address
              </button>
            </form>
          )}
        </div>
      )}
    </div>
  )
}
