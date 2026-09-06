interface Props {
  isLoading?: boolean
  error?: string | null
  onRetry?: () => void
}

export default function StatusScreen({ isLoading, error, onRetry }: Props) {
  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 12 }}>
      {isLoading && (
        <p style={{ color: '#aaa', fontSize: 14 }}>Loading...</p>
      )}
      {error && (
        <>
          <p style={{ color: '#888', fontSize: 14 }}>{error}</p>
          {onRetry && (
            <button
              onClick={onRetry}
              style={{ fontSize: 14, color: '#FF9600', padding: '8px 24px', border: '1.5px solid #FF9600', borderRadius: 999, background: 'none', cursor: 'pointer' }}
            >
              Try Again
            </button>
          )}
        </>
      )}
    </div>
  )
}
