interface PaginationProps {
  total: number;
  limit: number;
  offset: number;
  onOffsetChange: (nextOffset: number) => void;
}

export function Pagination({ total, limit, offset, onOffsetChange }: PaginationProps) {
  const lastShown = Math.min(offset + limit, total);
  const firstShown = total === 0 ? 0 : offset + 1;

  return (
    <div>
      <span>
        Showing {firstShown} to {lastShown} of {total}
      </span>
      <button
        type="button"
        disabled={offset === 0}
        onClick={() => onOffsetChange(Math.max(offset - limit, 0))}
      >
        Previous
      </button>
      <button
        type="button"
        disabled={offset + limit >= total}
        onClick={() => onOffsetChange(offset + limit)}
      >
        Next
      </button>
    </div>
  );
}
