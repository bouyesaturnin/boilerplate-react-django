import { AlertCircle, CheckCircle, Info, TriangleAlert, X } from 'lucide-react'
import { useState } from 'react'

const styles = {
  success: { container: 'bg-green-50 border-green-200 text-green-800',  icon: CheckCircle,     iconClass: 'text-green-500' },
  error:   { container: 'bg-red-50 border-red-200 text-red-800',        icon: AlertCircle,     iconClass: 'text-red-500'   },
  warning: { container: 'bg-yellow-50 border-yellow-200 text-yellow-800', icon: TriangleAlert, iconClass: 'text-yellow-500' },
  info:    { container: 'bg-blue-50 border-blue-200 text-blue-800',     icon: Info,            iconClass: 'text-blue-500'  },
}

export default function Alert({ variant = 'info', title, children, dismissible = false }) {
  const [visible, setVisible] = useState(true)
  if (!visible) return null

  const { container, icon: Icon, iconClass } = styles[variant]

  return (
    <div className={`flex gap-3 rounded-md border p-4 ${container}`} role="alert">
      <Icon size={18} className={`mt-0.5 shrink-0 ${iconClass}`} />
      <div className="flex-1 text-sm">
        {title && <p className="font-semibold">{title}</p>}
        {children && <p className={title ? 'mt-1' : ''}>{children}</p>}
      </div>
      {dismissible && (
        <button onClick={() => setVisible(false)} className="shrink-0 opacity-60 hover:opacity-100">
          <X size={16} />
        </button>
      )}
    </div>
  )
}
