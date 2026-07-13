import { ReactNode } from "react";

export interface Column<T> {
  header: string;
  // Right-align numeric columns for readability.
  align?: "left" | "right";
  render: (row: T) => ReactNode;
}

export default function QueryTable<T>({
  title,
  columns,
  rows,
  emptyText = "No data yet.",
}: {
  title: string;
  columns: Column<T>[];
  rows: T[];
  emptyText?: string;
}) {
  return (
    <div className="rounded-lg border border-gray-200 dark:border-gray-800">
      <h3 className="border-b border-gray-200 px-4 py-3 text-sm font-semibold dark:border-gray-800">
        {title}
      </h3>
      {rows.length === 0 ? (
        <p className="px-4 py-6 text-sm text-gray-400">{emptyText}</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-gray-500">
                {columns.map((col) => (
                  <th
                    key={col.header}
                    className={`px-4 py-2 font-medium ${
                      col.align === "right" ? "text-right" : ""
                    }`}
                  >
                    {col.header}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((row, i) => (
                <tr
                  key={i}
                  className="border-t border-gray-100 dark:border-gray-900"
                >
                  {columns.map((col) => (
                    <td
                      key={col.header}
                      className={`px-4 py-2 ${
                        col.align === "right"
                          ? "text-right tabular-nums"
                          : ""
                      }`}
                    >
                      {col.render(row)}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
