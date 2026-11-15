import { useState } from "react";
import type { IssueStatusBucket, Severity } from "../../api/types";
import {
  CATEGORY_OPTIONS,
  EMPTY_FILTERS,
  SEVERITY_OPTIONS,
  STATUS_OPTIONS,
  toggleValue,
} from "./filters";
import type { AppliedFilters } from "./filters";

interface IssueFiltersProps {
  onApply: (filters: AppliedFilters) => void;
}

export function IssueFilters({ onApply }: IssueFiltersProps) {
  const [category, setCategory] = useState("");
  const [severity, setSeverity] = useState<Severity[]>([]);
  const [status, setStatus] = useState<IssueStatusBucket[]>([]);
  const [from, setFrom] = useState("");
  const [to, setTo] = useState("");

  function apply() {
    onApply({ category, severity, status, from, to });
  }

  function clear() {
    setCategory("");
    setSeverity([]);
    setStatus([]);
    setFrom("");
    setTo("");
    onApply(EMPTY_FILTERS);
  }

  return (
    <div className="data-filters">
      <select value={category} onChange={(e) => setCategory(e.target.value)}>
        <option value="">All categories</option>
        {CATEGORY_OPTIONS.map((option) => (
          <option key={option} value={option}>
            {option}
          </option>
        ))}
      </select>
      <div className="checkbox-group">
        {SEVERITY_OPTIONS.map((option) => (
          <label key={option}>
            <input
              type="checkbox"
              checked={severity.includes(option)}
              onChange={() => setSeverity((current) => toggleValue(current, option))}
            />
            {option}
          </label>
        ))}
      </div>
      <div className="checkbox-group">
        {STATUS_OPTIONS.map((option) => (
          <label key={option}>
            <input
              type="checkbox"
              checked={status.includes(option)}
              onChange={() => setStatus((current) => toggleValue(current, option))}
            />
            {option}
          </label>
        ))}
      </div>
      <input type="date" value={from} onChange={(e) => setFrom(e.target.value)} />
      <input type="date" value={to} onChange={(e) => setTo(e.target.value)} />
      <button type="button" onClick={apply}>
        Apply
      </button>
      <button type="button" onClick={clear}>
        Clear
      </button>
    </div>
  );
}
