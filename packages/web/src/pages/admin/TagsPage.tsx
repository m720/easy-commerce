import { useState } from "react"
import { useForm } from "react-hook-form"
import { Plus, Pencil, Trash2, X, Check } from "lucide-react"
import { useTags, useCreateTag, useUpdateTag, useDeleteTag } from "@/api/tags"
import type { Tag } from "@/types"

interface TagFormValues {
  name: string
  slug: string
}

export default function TagsPage() {
  const { data: tags, isLoading } = useTags()
  const createTag = useCreateTag()
  const updateTag = useUpdateTag()
  const deleteTag = useDeleteTag()

  const [showAddForm, setShowAddForm] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)

  const addForm = useForm<TagFormValues>({ defaultValues: { name: "", slug: "" } })
  const editForm = useForm<TagFormValues>()

  const slugify = (name: string) =>
    name.toLowerCase().replace(/\s+/g, "-").replace(/[^a-z0-9-]/g, "")

  const handleCreate = async (data: TagFormValues) => {
    await createTag.mutateAsync({ name: data.name, slug: data.slug })
    addForm.reset()
    setShowAddForm(false)
  }

  const handleEdit = (tag: Tag) => {
    setEditingId(tag.id)
    editForm.reset({ name: tag.name, slug: tag.slug })
  }

  const handleUpdate = async (data: TagFormValues) => {
    if (editingId === null) return
    await updateTag.mutateAsync({ id: editingId, name: data.name, slug: data.slug })
    setEditingId(null)
  }

  const handleDelete = (id: number, name: string) => {
    if (window.confirm(`Delete tag "${name}"?`)) {
      deleteTag.mutate(id)
    }
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Tags</h1>
        <button
          onClick={() => setShowAddForm(!showAddForm)}
          className="inline-flex items-center gap-2 bg-indigo-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-indigo-700 transition-colors"
        >
          <Plus size={16} /> Add Tag
        </button>
      </div>

      {/* Add Form */}
      {showAddForm && (
        <div className="bg-white border rounded-xl p-5 space-y-4">
          <h2 className="text-base font-semibold text-gray-800">New Tag</h2>
          <form onSubmit={addForm.handleSubmit(handleCreate)} className="flex flex-wrap gap-3 items-end">
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Name *</label>
              <input
                {...addForm.register("name", { required: true })}
                onChange={(e) => {
                  addForm.setValue("name", e.target.value)
                  if (!addForm.getValues("slug")) {
                    addForm.setValue("slug", slugify(e.target.value))
                  }
                }}
                className="border rounded-lg px-3 py-2 text-sm w-48 focus:outline-none focus:ring-2 focus:ring-indigo-300"
                placeholder="e.g. New Arrivals"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Slug *</label>
              <input
                {...addForm.register("slug", { required: true })}
                className="border rounded-lg px-3 py-2 text-sm w-48 focus:outline-none focus:ring-2 focus:ring-indigo-300"
                placeholder="e.g. new-arrivals"
              />
            </div>
            <div className="flex gap-2">
              <button
                type="submit"
                disabled={addForm.formState.isSubmitting}
                className="bg-indigo-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-indigo-700 disabled:opacity-50"
              >
                Create
              </button>
              <button
                type="button"
                onClick={() => { setShowAddForm(false); addForm.reset() }}
                className="border px-4 py-2 rounded-lg text-sm hover:bg-gray-50"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Table */}
      <div className="bg-white border rounded-xl overflow-hidden">
        {isLoading ? (
          <div className="space-y-2 p-4">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="h-10 bg-gray-100 animate-pulse rounded" />
            ))}
          </div>
        ) : !tags || tags.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            <p className="font-medium">No tags yet</p>
            <p className="text-sm mt-1">Create your first tag above.</p>
          </div>
        ) : (
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="px-4 py-3 text-left font-medium text-gray-600">Name</th>
                <th className="px-4 py-3 text-left font-medium text-gray-600">Slug</th>
                <th className="px-4 py-3 text-right font-medium text-gray-600">Actions</th>
              </tr>
            </thead>
            <tbody>
              {tags.map((tag) => (
                <>
                  <tr key={tag.id} className="border-b last:border-0 hover:bg-gray-50">
                    <td className="px-4 py-3 font-medium text-gray-900">{tag.name}</td>
                    <td className="px-4 py-3 font-mono text-xs text-gray-500">{tag.slug}</td>
                    <td className="px-4 py-3">
                      <div className="flex items-center justify-end gap-2">
                        <button
                          onClick={() => handleEdit(tag)}
                          className="p-1.5 text-gray-500 hover:text-indigo-600 hover:bg-indigo-50 rounded transition-colors"
                        >
                          <Pencil size={14} />
                        </button>
                        <button
                          onClick={() => handleDelete(tag.id, tag.name)}
                          disabled={deleteTag.isPending}
                          className="p-1.5 text-gray-500 hover:text-red-600 hover:bg-red-50 rounded transition-colors disabled:opacity-50"
                        >
                          <Trash2 size={14} />
                        </button>
                      </div>
                    </td>
                  </tr>
                  {editingId === tag.id && (
                    <tr key={`edit-${tag.id}`} className="bg-indigo-50 border-b">
                      <td colSpan={3} className="px-4 py-3">
                        <form onSubmit={editForm.handleSubmit(handleUpdate)} className="flex flex-wrap gap-3 items-end">
                          <div>
                            <label className="block text-xs font-medium text-gray-600 mb-1">Name</label>
                            <input
                              {...editForm.register("name", { required: true })}
                              className="border rounded px-2 py-1.5 text-sm w-40 focus:outline-none focus:ring-2 focus:ring-indigo-300"
                            />
                          </div>
                          <div>
                            <label className="block text-xs font-medium text-gray-600 mb-1">Slug</label>
                            <input
                              {...editForm.register("slug", { required: true })}
                              className="border rounded px-2 py-1.5 text-sm w-40 focus:outline-none focus:ring-2 focus:ring-indigo-300"
                            />
                          </div>
                          <div className="flex gap-2">
                            <button
                              type="submit"
                              disabled={editForm.formState.isSubmitting}
                              className="p-1.5 bg-indigo-600 text-white rounded hover:bg-indigo-700 disabled:opacity-50"
                            >
                              <Check size={14} />
                            </button>
                            <button
                              type="button"
                              onClick={() => setEditingId(null)}
                              className="p-1.5 border rounded hover:bg-gray-100"
                            >
                              <X size={14} />
                            </button>
                          </div>
                        </form>
                      </td>
                    </tr>
                  )}
                </>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
