import type { Issue, IssueContact } from "../../api/types";

const CONTACT_LABEL: Record<string, string> = {
  HELPLINE: "Helpline",
  EMERGENCY: "Emergency",
  EMAIL: "Email",
  WEBSITE: "Website",
  COMPLAINT_PORTAL: "Complaint portal",
  LOCAL_OFFICE: "Local office",
};

function ContactValue({ contact }: { contact: IssueContact }) {
  if (contact.type === "EMAIL") {
    return <a href={`mailto:${contact.value}`}>{contact.value}</a>;
  }
  if (contact.type === "WEBSITE" || contact.type === "COMPLAINT_PORTAL") {
    return (
      <a href={contact.value} target="_blank" rel="noopener noreferrer">
        {contact.value}
      </a>
    );
  }
  return <>{contact.value}</>;
}

function ContactItem({ contact }: { contact: IssueContact }) {
  return (
    <li>
      <strong>{CONTACT_LABEL[contact.type] ?? contact.type}:</strong>{" "}
      <ContactValue contact={contact} />
      {!contact.verified && <em> (unverified)</em>}
      <div>
        Source:{" "}
        {contact.source_url ? (
          <a href={contact.source_url} target="_blank" rel="noopener noreferrer">
            {contact.source_url}
          </a>
        ) : (
          "not recorded"
        )}
        {" · "}
        Last verified:{" "}
        {contact.last_verified_at
          ? new Date(contact.last_verified_at).toLocaleDateString()
          : "never"}
      </div>
    </li>
  );
}

export function AuthoritySection({ issue }: { issue: Issue }) {
  const { department, authority, contacts } = issue;

  return (
    <section>
      <h3>Who is responsible</h3>
      <dl>
        <dt>Department</dt>
        <dd>{department?.name ?? "Not assigned yet"}</dd>
        <dt>Authority</dt>
        <dd>
          {authority
            ? `${authority.name} (${authority.jurisdiction})`
            : "Not assigned yet"}
        </dd>
      </dl>
      {contacts.length === 0 ? (
        <p>No official contacts are available for this issue yet.</p>
      ) : (
        <ul>
          {contacts.map((contact, index) => (
            <ContactItem key={index} contact={contact} />
          ))}
        </ul>
      )}
    </section>
  );
}
