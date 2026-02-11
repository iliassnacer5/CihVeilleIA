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
}

export function DataTable<T>({
  columns,
  data,
  rowKey,
  actions,
}: DataTableProps<T>) {
  return (
    <div className="border border-border rounded-lg overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="bg-secondary border-b border-border">
              {columns.map((column) => (
                <th
                  key={String(column.key)}
                  className="px-6 py-4 text-left text-sm font-semibold text-foreground"
                  style={{ width: column.width }}
                >
                  {column.label}
                </th>
              ))}
              {actions && (
                <th className="px-6 py-4 text-left text-sm font-semibold text-foreground">
                  Actions
                </th>
              )}
            </tr>
          </thead>
          <tbody>
            {data.map((row, index) => (
              <tr
                key={String(row[rowKey])}
                className="border-b border-border hover:bg-secondary transition-colors"
              >
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
                  <td className="px-6 py-4 text-sm">
                    {actions(row)}
                  </td>
                )}
              </tr>
            ))}
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
