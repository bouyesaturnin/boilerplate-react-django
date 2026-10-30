export default function Input({
  id,
  label,
  error,
  helper,
  className = '',
  ...props
}) {
  return (
    <div className="space-y-1">
      {label && (
        <label htmlFor={id} className="block text-sm font-medium text-gray-700">
          {label}
        </label>
      )}
      <input
        id={id}
        className={[
          'block w-full rounded-md border px-3 py-2 text-sm shadow-sm',
          'placeholder:text-gray-400',
          'focus:outline-none focus:ring-2 focus:ring-offset-0',
          error
            ? 'border-red-300 focus:border-red-400 focus:ring-red-200'
            : 'border-gray-300 focus:border-primary-500 focus:ring-primary-200',
          'disabled:bg-gray-50 disabled:text-gray-500',
          className,
        ].join(' ')}
        {...props}
      />
      {error && <p className="text-xs text-red-600">{error}</p>}
      {helper && !error && <p className="text-xs text-gray-500">{helper}</p>}
    </div>
  )
}
