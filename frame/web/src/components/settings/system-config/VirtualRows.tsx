import { useMemo, useState, type ReactNode, type UIEvent } from 'react'

type VirtualRowsProps<T> = {
  items: T[]
  height?: number
  rowHeight?: number
  itemKey: (item: T, index: number) => string
  renderItem: (item: T, index: number) => ReactNode
}

function clamp(value: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, value))
}

function VirtualRows<T>({
  items,
  height = 260,
  rowHeight = 76,
  itemKey,
  renderItem,
}: VirtualRowsProps<T>) {
  const [scrollTop, setScrollTop] = useState(0)
  const visibleCount = Math.ceil(height / rowHeight) + 2
  const totalHeight = items.length * rowHeight
  const startIndex = clamp(Math.floor(scrollTop / rowHeight) - 1, 0, Math.max(0, items.length - 1))
  const visibleItems = useMemo(
    () => items.slice(startIndex, startIndex + visibleCount),
    [items, startIndex, visibleCount],
  )

  const handleScroll = (event: UIEvent<HTMLDivElement>) => {
    setScrollTop(event.currentTarget.scrollTop)
  }

  return (
    <div className="settings-virtual-list" style={{ height }} onScroll={handleScroll}>
      <div className="settings-virtual-list__spacer" style={{ height: totalHeight }}>
        <div
          className="settings-virtual-list__window"
          style={{ transform: `translateY(${startIndex * rowHeight}px)` }}
        >
          {visibleItems.map((item, offset) => {
            const index = startIndex + offset
            return (
              <div className="settings-virtual-list__row" style={{ minHeight: rowHeight }} key={itemKey(item, index)}>
                {renderItem(item, index)}
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}

export default VirtualRows
