import React, { useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { motion } from 'framer-motion'
import { Upload, FileUp } from 'lucide-react'

const ACCEPTED_EXTENSIONS: Record<string, string[]> = {
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
  'application/vnd.ms-excel': ['.xls'],
  'text/csv': ['.csv'],
  'application/pdf': ['.pdf'],
  'image/png': ['.png'],
  'image/jpeg': ['.jpg', '.jpeg'],
  'image/tiff': ['.tiff', '.tif'],
  'image/webp': ['.webp'],
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
  'text/plain': ['.txt'],
  'application/vnd.openxmlformats-officedocument.presentationml.presentation': ['.pptx'],
  'application/x-xmind': ['.xmind'],
  'application/xml': ['.mm'],
}

const MAX_FILE_SIZE = 100 * 1024 * 1024 // 100 MB

interface DropZoneProps {
  onFilesAccepted: (files: File[]) => void
  disabled?: boolean
}

export default function DropZone({ onFilesAccepted, disabled }: DropZoneProps) {
  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      onFilesAccepted(acceptedFiles)
    },
    [onFilesAccepted]
  )

  const { getRootProps, getInputProps, isDragActive, isDragReject } = useDropzone({
    onDrop,
    accept: ACCEPTED_EXTENSIONS,
    maxSize: MAX_FILE_SIZE,
    maxFiles: 20,
    disabled,
    multiple: true,
  })

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <div
        {...getRootProps()}
        className={`relative border-2 border-dashed rounded-xl p-12 text-center cursor-pointer transition-all duration-300 ${
          disabled
            ? 'opacity-50 cursor-not-allowed border-white/10'
            : isDragReject
            ? 'border-error-red bg-error-red/5'
            : isDragActive
            ? 'border-accent-green bg-accent-green/5 shadow-[0_0_30px_rgba(76,175,125,0.15)]'
            : 'border-white/10 hover:border-accent-green/50 hover:bg-accent-green/5'
        }`}
      >
        <input {...getInputProps()} />

        <div className="flex flex-col items-center gap-4">
          <div
            className={`w-16 h-16 rounded-2xl flex items-center justify-center transition-colors ${
              isDragActive ? 'bg-accent-green/20' : 'bg-white/5'
            }`}
          >
            {isDragActive ? (
              <FileUp className="w-8 h-8 text-accent-green animate-bounce" />
            ) : (
              <Upload className="w-8 h-8 text-text-muted" />
            )}
          </div>

          {isDragReject ? (
            <p className="text-error-red font-body">Some files are not supported</p>
          ) : isDragActive ? (
            <p className="text-accent-green font-body text-lg">Drop files here…</p>
          ) : (
            <>
              <div>
                <p className="text-text-primary font-body text-lg mb-1">
                  Drag & drop LCA documents here
                </p>
                <p className="text-text-muted text-sm">
                  or <span className="text-accent-green underline">browse files</span>
                </p>
              </div>
              <div className="flex flex-wrap justify-center gap-2 mt-2">
                {['xlsx', 'csv', 'pdf', 'docx', 'png', 'jpg', 'xmind', 'pptx'].map(
                  (ext) => (
                    <span
                      key={ext}
                      className="px-2 py-0.5 bg-white/5 rounded text-xs font-mono text-text-muted"
                    >
                      .{ext}
                    </span>
                  )
                )}
              </div>
              <p className="text-text-muted text-xs mt-1">Up to 20 files · 100 MB each</p>
            </>
          )}
        </div>
      </div>
    </motion.div>
  )
}
