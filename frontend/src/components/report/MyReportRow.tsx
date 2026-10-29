import { useNavigate } from "react-router-dom";
import type { MyReportListItem } from "../../api/types";
import { StatusBadge } from "./StatusBadge";

interface MyReportRowProps {
  item: MyReportListItem;
}

export function MyReportRow({ item }: MyReportRowProps) {
  const navigate = useNavigate();

  return (
    <tr className="report-row" onClick={() => navigate(`/reports/${item.id}`)}>
      <td>{item.description_preview ?? "No description"}</td>
      <td>
        {item.thumbnail_url ? (
          <a
            href={item.thumbnail_url}
            target="_blank"
            rel="noreferrer"
            onClick={(event) => event.stopPropagation()}
          >
            <img src={item.thumbnail_url} alt="Uploaded photo" width={48} height={48} />
          </a>
        ) : (
          "—"
        )}
      </td>
      <td>{new Date(item.created_at).toLocaleDateString()}</td>
      <td>
        <StatusBadge
          processingStatus={item.processing_status}
          issueStatus={item.issue_status}
        />
      </td>
      <td>{item.category ?? "Not yet available"}</td>
      <td>{item.severity_level ?? "Not yet available"}</td>
      <td>{item.issue_id ? `${item.report_count} supporting report(s)` : "—"}</td>
    </tr>
  );
}
