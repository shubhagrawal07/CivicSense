import type { MyReportListItem } from "../../api/types";
import { MyReportRow } from "./MyReportRow";

interface MyReportsListProps {
  items: MyReportListItem[];
}

export function MyReportsList({ items }: MyReportsListProps) {
  return (
    <ul>
      {items.map((item) => (
        <MyReportRow key={item.id} item={item} />
      ))}
    </ul>
  );
}
