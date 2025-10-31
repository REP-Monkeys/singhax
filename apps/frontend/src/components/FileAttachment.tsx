import { FileText, File, Image as ImageIcon, X } from 'lucide-react'

interface FileAttachmentProps {
  filename: string
  fileType?: string
  size?: number
  onRemove?: () => void
  variant?: 'chat' | 'input' // 'chat' for messages, 'input' for input preview
}

export function FileAttachment({ filename, fileType, size, onRemove, variant = 'chat' }: FileAttachmentProps) {
  const getFileIcon = () => {
    const isPDF = fileType?.includes('pdf') || filename.toLowerCase().endsWith('.pdf')
    const isImage = fileType?.includes('image') || ['png', 'jpg', 'jpeg', 'gif', 'webp'].includes(
      filename.split('.').pop()?.toLowerCase() || ''
    )
    
    if (isPDF) {
      return (
        <div className="w-8 h-8 bg-red-100 rounded flex items-center justify-center">
          <FileText className="w-4 h-4 text-red-600" />
        </div>
      )
    }
    if (isImage) {
      return (
        <div className="w-8 h-8 bg-blue-100 rounded flex items-center justify-center">
          <ImageIcon className="w-4 h-4 text-blue-600" />
        </div>
      )
    }
    return (
      <div className="w-8 h-8 bg-gray-100 rounded flex items-center justify-center">
        <File className="w-4 h-4 text-gray-600" />
      </div>
    )
  }

  const formatFileSize = (bytes?: number) => {
    if (!bytes) return ''
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  const getFileTypeLabel = () => {
    if (fileType?.includes('pdf') || filename.toLowerCase().endsWith('.pdf')) return 'PDF'
    if (fileType?.includes('image')) return 'IMAGE'
    return 'FILE'
  }

  if (variant === 'input') {
    // Preview style for input area (like ChatGPT)
    return (
      <div className="flex items-center gap-3 px-3 py-2 bg-gray-100 rounded-lg border border-gray-300 max-w-sm">
        <div className="flex-shrink-0">
          {getFileIcon()}
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-gray-900 truncate">
            {filename}
          </p>
          <p className="text-xs text-gray-500">
            {getFileTypeLabel()}
          </p>
        </div>
        {onRemove && (
          <button
            onClick={onRemove}
            className="flex-shrink-0 text-gray-500 hover:text-gray-700 transition-colors"
            aria-label="Remove file"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>
    )
  }

  // Chat message style
  return (
    <div className="flex items-center gap-3 px-4 py-2 bg-gray-50 border border-gray-200 rounded-lg max-w-sm">
      <div className="flex-shrink-0">
        {getFileIcon()}
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-gray-900 truncate">
          {filename}
        </p>
        {size && (
          <p className="text-xs text-gray-500">
            {formatFileSize(size)}
          </p>
        )}
      </div>
    </div>
  )
}

