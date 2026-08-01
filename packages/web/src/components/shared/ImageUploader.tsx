import { useRef, useState } from "react"
import { Upload, X, Star } from "lucide-react"
import { useGetUploadUrl, useConfirmUpload, useDeleteImage, useSetPrimaryImage } from "@/api/products"
import type { ProductImage, UUID } from "@/types"

interface Props {
  productId: UUID
  images: ProductImage[]
}

export default function ImageUploader({ productId, images }: Props) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState("")

  const getUploadUrl = useGetUploadUrl(productId)
  const confirmUpload = useConfirmUpload(productId)
  const deleteImage = useDeleteImage(productId)
  const setPrimary = useSetPrimaryImage(productId)

  const handleFile = async (file: File) => {
    setUploading(true)
    setError("")
    try {
      // Step 1: Get upload URL
      const { upload_url, s3_key } = await getUploadUrl.mutateAsync({
        filename: file.name,
        content_type: file.type || "image/jpeg",
      })

      // Step 2: PUT to S3 directly (no Authorization header)
      const putRes = await fetch(upload_url, {
        method: "PUT",
        body: file,
        headers: { "Content-Type": file.type || "image/jpeg" },
      })
      if (!putRes.ok) throw new Error("S3 upload failed")

      // Step 3: Confirm upload
      const isPrimary = images.length === 0
      await confirmUpload.mutateAsync({
        s3_key,
        is_primary: isPrimary,
        sort_order: images.length,
      })
    } catch (e) {
      setError((e as Error).message ?? "Upload failed")
    } finally {
      setUploading(false)
    }
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) handleFile(file)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    const file = e.dataTransfer.files[0]
    if (file) handleFile(file)
  }

  return (
    <div className="space-y-4">
      {/* Drop zone */}
      <div
        onDrop={handleDrop}
        onDragOver={(e) => e.preventDefault()}
        onClick={() => inputRef.current?.click()}
        className="border-2 border-dashed border-sage/40 rounded-lg p-8 text-center cursor-pointer hover:border-brand transition-colors"
      >
        <Upload size={24} className="mx-auto text-charcoal/70 mb-2" />
        <p className="text-sm text-charcoal/70">
          {uploading ? "Uploading..." : "Click or drag to upload image"}
        </p>
        <input ref={inputRef} type="file" accept="image/*" onChange={handleInputChange} className="hidden" />
      </div>

      {error && <p className="text-red-500 text-sm">{error}</p>}

      {/* Image grid */}
      {images.length > 0 && (
        <div className="grid grid-cols-3 sm:grid-cols-4 gap-3">
          {images.map((img) => (
            <div key={img.id} className="relative group aspect-square">
              <img
                src={img.url ?? ""}
                alt=""
                className="w-full h-full object-cover rounded-lg border"
              />
              <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity rounded-lg flex items-center justify-center gap-2">
                {!img.is_primary && (
                  <button
                    onClick={() => setPrimary.mutate(img.id)}
                    className="p-1.5 bg-white rounded-full hover:bg-yellow-50"
                    title="Set as primary"
                  >
                    <Star size={14} className="text-yellow-500" />
                  </button>
                )}
                <button
                  onClick={() => deleteImage.mutate(img.id)}
                  className="p-1.5 bg-white rounded-full hover:bg-red-50"
                  title="Delete"
                >
                  <X size={14} className="text-red-500" />
                </button>
              </div>
              {img.is_primary && (
                <span className="absolute bottom-1 left-1 text-xs bg-yellow-400 text-white px-1.5 py-0.5 rounded">
                  Primary
                </span>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
