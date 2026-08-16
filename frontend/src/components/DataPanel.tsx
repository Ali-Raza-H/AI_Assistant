export function findItems(value: unknown): Record<string, unknown>[] {
  if (Array.isArray(value)) return value.filter((item): item is Record<string, unknown> => Boolean(item) && typeof item === 'object')
  if (!value || typeof value !== 'object') return []
  const object = value as Record<string, unknown>
  for (const key of ['items', 'tasks', 'events', 'data', 'results', 'entries']) {
    if (Array.isArray(object[key])) return findItems(object[key])
  }
  return Object.keys(object).length ? [object] : []
}

function textValue(item: Record<string, unknown>, keys: string[]) {
  for (const key of keys) {
    const value = item[key]
    if (typeof value === 'string' && value.trim()) return value
    if (typeof value === 'number') return String(value)
  }
  return ''
}

export function DataPanel({ title, value, limit = 4 }: { title: string; value: unknown; limit?: number }) {
  const items = findItems(value).slice(0, limit)
  if (!items.length) return null

  return (
    <section className="data-panel">
      <header>
        <span>{title}</span>
        <small>{String(items.length).padStart(2, '0')}</small>
      </header>
      <div className="data-list">
        {items.map((item, index) => {
          const titleText = textValue(item, ['title', 'name', 'summary', 'message', 'label']) || `${title} ${index + 1}`
          const meta = textValue(item, ['due_at', 'dueDate', 'start', 'date', 'status', 'severity', 'time'])
          return (
            <article key={String(item.id || `${title}-${index}`)}>
              <span className="item-index">{String(index + 1).padStart(2, '0')}</span>
              <div>
                <p>{titleText}</p>
                {meta && <small>{meta}</small>}
              </div>
            </article>
          )
        })}
      </div>
    </section>
  )
}
