import React from 'react';
import clsx from 'classnames';

export interface Column<T> {
  /**
   * Unique key for the column corresponding to a property on the data
   * objects.
   */
  key: keyof T;
  /**
   * Header label shown in the table head.
   */
  header: string;
  /**
   * Optional custom cell renderer.  When provided it receives the
   * underlying row and returns a React node.
   */
  render?: (row: T) => React.ReactNode;
  /**
   * Optional alignment for the cell content.
   */
  align?: 'left' | 'center' | 'right';
}

export interface DataTableProps<T> {
  /**
   * Array of column definitions determining order and rendering.
   */
  columns: Array<Column<T>>;
  /**
   * Array of row data objects.
   */
  data: T[];
  /**
   * Optional className applied to the outer table.
   */
  className?: string;
}

/**
 * A basic, flexible data table.  Consumers can provide custom
 * renderers for columns to display complex content.  The table uses
 * minimal styling that can be extended with Tailwind utility classes.
 */
export function DataTable<T>({ columns, data, className }: DataTableProps<T>): JSX.Element {
  return (
    <div className={clsx('overflow-x-auto', className)}>
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            {columns.map((col) => (
              <th
                key={String(col.key)}
                className={clsx(
                  'px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider',
                  {
                    'text-center': col.align === 'center',
                    'text-right': col.align === 'right',
                  },
                )}
              >
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {data.map((row, rowIndex) => (
            <tr key={rowIndex} className="hover:bg-gray-50">
              {columns.map((col) => (
                <td
                  key={String(col.key)}
                  className={clsx(
                    'px-4 py-2 whitespace-nowrap text-sm text-gray-700',
                    {
                      'text-center': col.align === 'center',
                      'text-right': col.align === 'right',
                    },
                  )}
                >
                  {col.render ? col.render(row) : String(row[col.key])}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default DataTable;
