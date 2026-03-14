import { useUsers, useActivateUser, useDeactivateUser } from "@/api/users"
import { formatDate } from "@/lib/utils"
import { usePagination } from "@/hooks/usePagination"
import PaginationControls from "@/components/shared/PaginationControls"

export default function UsersPage() {
  const { skip, limit, page, nextPage, prevPage } = usePagination(20)
  const { data: users, isLoading } = useUsers({ skip, limit })
  const activateUser = useActivateUser()
  const deactivateUser = useDeactivateUser()

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Users</h1>

      <div className="bg-white border rounded-xl overflow-hidden">
        {isLoading ? (
          <div className="space-y-2 p-4">
            {Array.from({ length: 8 }).map((_, i) => (
              <div key={i} className="h-12 bg-gray-100 animate-pulse rounded" />
            ))}
          </div>
        ) : !users || users.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            <p className="font-medium">No users found</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b">
                <tr>
                  <th className="px-4 py-3 text-left font-medium text-gray-600">Name</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-600">Email</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-600">Role</th>
                  <th className="px-4 py-3 text-center font-medium text-gray-600">Active</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-600">Joined</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-600">Actions</th>
                </tr>
              </thead>
              <tbody>
                {users.map((user) => (
                  <tr key={user.id} className="border-b last:border-0 hover:bg-gray-50">
                    <td className="px-4 py-3 font-medium text-gray-900">{user.full_name}</td>
                    <td className="px-4 py-3 text-gray-600">{user.email}</td>
                    <td className="px-4 py-3">
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium capitalize ${
                          user.role === "admin"
                            ? "bg-purple-100 text-purple-700"
                            : "bg-gray-100 text-gray-600"
                        }`}
                      >
                        {user.role}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                          user.is_active ? "bg-green-100 text-green-700" : "bg-red-100 text-red-600"
                        }`}
                      >
                        {user.is_active ? "Active" : "Inactive"}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-gray-600 whitespace-nowrap">
                      {formatDate(user.created_at)}
                    </td>
                    <td className="px-4 py-3">
                      {user.is_active ? (
                        <button
                          onClick={() => deactivateUser.mutate(user.id)}
                          disabled={deactivateUser.isPending}
                          className="px-3 py-1 text-xs font-medium text-red-600 border border-red-300 rounded hover:bg-red-50 disabled:opacity-50 transition-colors"
                        >
                          Deactivate
                        </button>
                      ) : (
                        <button
                          onClick={() => activateUser.mutate(user.id)}
                          disabled={activateUser.isPending}
                          className="px-3 py-1 text-xs font-medium text-green-700 border border-green-300 rounded hover:bg-green-50 disabled:opacity-50 transition-colors"
                        >
                          Activate
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <PaginationControls
        page={page}
        hasPrev={skip > 0}
        hasNext={!!users && users.length === limit}
        onPrev={prevPage}
        onNext={nextPage}
      />
    </div>
  )
}
