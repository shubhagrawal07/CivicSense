import type { AuthorityContact, AuthorityInfo } from "../../api/types";

const TYPE_LABEL: Record<string, string> = {
  HELPLINE: "Helpline",
  EMERGENCY: "Emergency",
  EMAIL: "Email",
  WEBSITE: "Website",
  COMPLAINT_PORTAL: "Complaint portal",
  LOCAL_OFFICE: "Local office",
};

function ContactValue({ contact }: { contact: AuthorityContact }) {
  if (contact.type === "EMAIL") {
    return <a href={`mailto:${contact.value}`}>{contact.value}</a>;
  }
  if (/^https?:\/\//i.test(contact.value)) {
    return <a href={contact.value}>{contact.value}</a>;
  }
  return <>{contact.value}</>;
}

export function DepartmentContacts({ info }: { info: AuthorityInfo }) {
  return (
    <section className="authority-section">
      <h3>{info.department.name}</h3>
      <p>
        Authority: <strong>{info.authority ? info.authority.name : "none on record"}</strong>
      </p>
      {info.is_fallback && (
        <p>
          This department has no contacts of its own, so the general grievance contacts are shown.
        </p>
      )}
      {info.needs_review && (
        <p>
          The point is close to an area boundary. Other possible authorities:{" "}
          {info.other_matches.map((a) => a.name).join(", ") || "none listed"}.
        </p>
      )}
      {info.contacts.length === 0 ? (
        <p>No contacts on record</p>
      ) : (
        <table className="contact-table">
          <thead>
            <tr>
              <th>Type</th>
              <th>Contact</th>
              <th>Source</th>
              <th>Last verified</th>
            </tr>
          </thead>
          <tbody>
            {info.contacts.map((contact) => (
              <tr key={`${contact.type}-${contact.value}`}>
                <td>{TYPE_LABEL[contact.type] ?? contact.type}</td>
                <td>
                  <ContactValue contact={contact} />
                  {!contact.verified && <span className="unverified-tag">Unverified</span>}
                </td>
                <td>
                  {contact.source_url ? <a href={contact.source_url}>Source</a> : "No source"}
                </td>
                <td>{contact.last_verified_at ?? "Not recorded"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}
