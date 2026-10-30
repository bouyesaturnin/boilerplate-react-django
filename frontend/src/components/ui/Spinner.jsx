import { Loader2 } from 'lucide-react'

const sizes = { sm: 16, md: 24, lg: 36 }

export default function Spinner({ size = 'md', className = '' }) {
  return (
    <Loader2
      size={sizes[size]}
      className={`animate-spin text-primary-600 ${className}`}
    />
  )
}
