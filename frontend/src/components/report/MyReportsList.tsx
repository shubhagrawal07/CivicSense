import type { MyReportListItem } from "../../api/types";
import { MyReportRow } from "./MyReportRow";

interface MyReportsListProps {
  items: MyReportListItem[];
}

export function MyReportsList({ items }: MyReportsListProps) {
  return (
    <table className="report-list">
      <thead>
        <tr>
          <th>Description</th>
          <th>Reported</th>
          <th>Status</th>
          <th>Category</th>
          <th>Severity</th>
          <th>Supporting reports</th>
        </tr>
      </thead>
      <tbody>
        {items.map((item) => (
          <MyReportRow key={item.id} item={item} />
        ))}
      </tbody>
    </table>
  );
}
