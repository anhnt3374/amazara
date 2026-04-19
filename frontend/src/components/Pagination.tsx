import clsx from 'clsx'

interface PaginationProps {
  currentPage: number
  totalPages: number
  onPageChange: (page: number) => void
}

export default function Pagination({ currentPage, totalPages, onPageChange }: PaginationProps) {
  function getPages(): (number | '...')[] {
    const pages: (number | '...')[] = []
    if (totalPages <= 7) {
      for (let i = 1; i <= totalPages; i++) pages.push(i)
      return pages
    }
    pages.push(1)
    if (currentPage > 3) pages.push('...')
    const start = Math.max(2, currentPage - 1)
    const end = Math.min(totalPages - 1, currentPage + 1)
    for (let i = start; i <= end; i++) pages.push(i)
    if (currentPage < totalPages - 2) pages.push('...')
    pages.push(totalPages)
    return pages
  }

  return (
    <div className="flex items-center justify-center gap-1">
      <button
        onClick={() => onPageChange(currentPage - 1)}
        disabled={currentPage <= 1}
        className={clsx(
          'px-3 py-1.5 text-xs rounded-pin border transition-colors',
          currentPage <= 1
            ? 'border-sand text-warm-silver cursor-not-allowed'
            : 'border-sand text-plum hover:border-plum'
        )}
      >
        Prev
      </button>
      {getPages().map((p, i) =>
        p === '...' ? (
          <span key={`ellipsis-${i}`} className="px-2 text-xs text-olive">...</span>
        ) : (
          <button
            key={p}
            onClick={() => onPageChange(p)}
            className={clsx(
              'w-8 h-8 text-xs rounded-pin border transition-colors',
              p === currentPage
                ? 'border-brand-red bg-brand-red text-white'
                : 'border-sand text-plum hover:border-plum'
            )}
          >
            {p}
          </button>
        )
      )}
      <button
        onClick={() => onPageChange(currentPage + 1)}
        disabled={currentPage >= totalPages}
        className={clsx(
          'px-3 py-1.5 text-xs rounded-pin border transition-colors',
          currentPage >= totalPages
            ? 'border-sand text-warm-silver cursor-not-allowed'
            : 'border-sand text-plum hover:border-plum'
        )}
      >
        Next
      </button>
    </div>
  )
}
