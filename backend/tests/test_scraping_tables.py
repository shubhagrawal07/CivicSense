from sqlalchemy import func, select

from app.models import Jurisdiction, RawDocument, ScrapeRun
from app.models.enums import JurisdictionStatus, ScrapeStatus

SQUARE = (
    "SRID=4326;MULTIPOLYGON(((72.90 19.10, 73.00 19.10, "
    "73.00 19.20, 72.90 19.20, 72.90 19.10)))"
)


def point(lng, lat):
    return func.ST_SetSRID(func.ST_MakePoint(lng, lat), 4326)


def test_boundary_is_found_with_st_contains(db):
    ward = Jurisdiction(name="Test ward", type="ward", boundary=SQUARE)
    db.add(ward)
    db.flush()

    def found_at(lng, lat):
        return db.scalar(
            select(Jurisdiction.id).where(
                Jurisdiction.id == ward.id,
                func.ST_Contains(Jurisdiction.boundary, point(lng, lat)),
            )
        )

    assert found_at(72.95, 19.15) == ward.id
    assert found_at(73.50, 19.15) is None
    assert ward.authority_id is None
    assert ward.status == JurisdictionStatus.CANDIDATE


def test_raw_document_keeps_content_exactly(db):
    run = ScrapeRun(source="bmc_contacts")
    db.add(run)
    db.flush()
    page = "<html>\n  <body>  Helpline: 1916  </body>\n</html>\n"
    doc = RawDocument(
        scrape_run_id=run.id,
        source_url="https://example.org/contacts",
        content_type="text/html",
        content=page,
    )
    db.add(doc)
    db.flush()
    db.expire(doc)

    assert db.get(RawDocument, doc.id).content == page
    assert run.status == ScrapeStatus.RUNNING
