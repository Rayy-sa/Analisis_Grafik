import type { TablePayload } from "../lib/types";

type Props = {
  table: TablePayload;
};

export function DataTable({ table }: Props) {
  return (
    <div className="table-scroll overflow-auto rounded-2xl border border-line">
      <table className="min-w-full text-left text-sm">
        <thead className="bg-paper text-mute">
          <tr>
            {table.columns.map((col) => (
              <th key={col} className="whitespace-nowrap px-4 py-3 font-medium">
                {col}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {table.rows.map((row, index) => (
            <tr key={index} className="border-t border-line/80 bg-cream/50">
              {table.columns.map((col) => (
                <td key={col} className="whitespace-nowrap px-4 py-2.5 text-ink">
                  {row[col] === null || row[col] === undefined ? "—" : String(row[col])}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
