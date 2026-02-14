import React from 'react'

interface Column<T> {
  key: keyof T
  label: string
  render?: (value: T[keyof T], row: T) => React.ReactNode
  width?: string
}

interface DataTableProps<T> {
  columns: Column<T>[]
  data: T[]
  rowKey: keyof T
  actions?: (row: T) => React.ReactNode
  onSelectionChange?: (selectedKeys: Set<string>) => void
  selectedKeys?: Set<string>
}

export function DataTable<T>({
  columns,
  data,
  rowKey,
  actions,
  onSelectionChange,
  selectedKeys = new Set(),
}: DataTableProps<T>) {
  const handleSelectAll = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!onSelectionChange) return
    if (e.target.checked) {
      const allKeys = new Set(data.map((item) => String(item[rowKey])))
      onSelectionChange(allKeys)
    } else {
      onSelectionChange(new Set())
    }
  }

  const handleSelectRow = (key: string) => {
    if (!onSelectionChange) return
    const newSelection = new Set(selectedKeys)
    if (newSelection.has(key)) {
      newSelection.delete(key)
    } else {
      newSelection.add(key)
    }
    onSelectionChange(newSelection)
  }

  const isAllSelected = data.length > 0 && selectedKeys.size === data.length

  return (
    <div className="border border-border rounded-lg overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="bg-secondary border-b border-border">
              {onSelectionChange && (
                <th className="px-6 py-4 text-left w-10">
                  <input
                    type="checkbox"
                    checked={isAllSelected}
                    onChange={handleSelectAll}
                    className="h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary"
                  />
                </th>
              )}
              {columns.map((column) => (
                <th
                  key={String(column.key)}
                  className="px-6 py-4 text-left text-sm font-semibold text-foreground uppercase tracking-wider"
                  style={{ width: column.width }}
                >
                  {column.label}
                </th>
              ))}
              {actions && (
                <th className="px-6 py-4 text-right text-sm font-semibold text-foreground uppercase tracking-wider">
                  Actions
                </th>
              )}
            </tr>
          </thead>
          <tbody>
            {data.map((row, index) => {
              const key = row[rowKey] != null ? String(row[rowKey]) : `row-${index}`
              const isSelected = selectedKeys.has(key)

              return (
                <tr
                  key={key}
                  className={`border-b border-border transition-colors ${isSelected ? 'bg-primary/5' : 'hover:bg-secondary/50'
                    }`}
                >
                  {onSelectionChange && (
                    <td className="px-6 py-4">
                      <input
                        type="checkbox"
                        checked={isSelected}
                        onChange={() => handleSelectRow(key)}
                        className="h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary"
                      />
                    </td>
                  )}
                  {columns.map((column) => (
                    <td
                      key={String(column.key)}
                      className="px-6 py-4 text-sm text-foreground"
                    >
                      {column.render
                        ? column.render(row[column.key], row)
                        : String(row[column.key])}
                    </td>
                  ))}
                  {actions && (
                    <td className="px-6 py-4 text-sm text-right">
                      {actions(row)}
                    </td>
                  )}
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
      {data.length === 0 && (
        <div className="text-center py-12">
          <p className="text-muted-foreground">No data to display</p>
        </div>
      )}
    </div>
  )
}
