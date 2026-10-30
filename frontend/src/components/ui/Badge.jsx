const variants = {
  default:  'bg-gray-100 text-gray-700',
  primary:  'bg-primary-100 text-primary-700',
  success:  'bg-green-100 text-green-700',
  warning:  'bg-yellow-100 text-yellow-800',
  error:    'bg-red-100 text-red-700',
}

export default function Badge({ children, variant = 'default', className = '' }) {
  return (
    <span
      className={[
        'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium',
        variants[variant],
        className,
      ].join(' ')}
    >
      {children}
    </span>
  )
}
