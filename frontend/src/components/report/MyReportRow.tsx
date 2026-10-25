import { useNavigate } from "react-router-dom";
import type { MyReportListItem } from "../../api/types";
import { StatusBadge } from "./StatusBadge";

interface MyReportRowProps {
  item: MyReportListItem;
}

export function MyReportRow({ item }: MyReportRowProps) {
  const navigate = useNavigate();

  return (
    <li onClick={() => navigate(`/reports/${item.id}`)} style={{ cursor: "pointer" }}>
      {item.thumbnail_url && <img src={item.thumbnail_url} alt="" width={48} height={48} />}
      <span>{item.description_preview ?? "Photo only"}</span>
      <span>{new Date(item.created_at).toLocaleDateString()}</span>
      <StatusBadge
        processingStatus={item.processing_status}
        issueStatus={item.issue_status}
      />
      <span>{item.category ?? "Not yet available"}</span>
      <span>{item.severity_level ?? "Not yet available"}</span>
      {item.issue_id && <span>{item.report_count} supporting report(s)</span>}
    </li>
  );
}
