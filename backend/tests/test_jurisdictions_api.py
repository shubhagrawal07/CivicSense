import pytest
from fastapi.testclient import TestClient
from geoalchemy2.shape import from_shape
from shapely.geometry import MultiPolygon, box

from app.core.db import get_db
from app.main import app
from app.models import Authority, Jurisdiction
from app.models.enums import JurisdictionStatus


@pytest.fixture
def client(db):
    app.dependency_overrides[get_db] = lambda: db
    yield TestClient(app)
    app.dependency_overrides.clear()


def add_square(db, name, type, priority, west, south, east, north, authority_id=None):
    shape = MultiPolygon([box(west, south, east, north)])
    db.add(
        Jurisdiction(
            name=name,
            type=type,
            priority=priority,
            authority_id=authority_id,
            boundary=from_shape(shape, srid=4326),
            status=JurisdictionStatus.APPROVED,
        )
    )
    db.flush()


def test_list_returns_geojson_for_the_requested_type(client, db):
    authority = Authority(name="Test Body", jurisdiction="Testville")
    db.add(authority)
    db.flush()
    add_square(db, "Test Ward", "testward", 10, 10.0, 10.0, 11.0, 11.0, authority.id)
    add_square(db, "Test Campus", "testcampus", 20, 10.2, 10.2, 10.4, 10.4)

    response = client.get("/api/jurisdictions", params={"type": "testward"})

    assert response.status_code == 200
    body = response.json()
    assert body["type"] == "FeatureCollection"
    assert len(body["features"]) == 1
    feature = body["features"][0]
    assert feature["geometry"]["type"] in ("Polygon", "MultiPolygon")
    assert feature["properties"]["name"] == "Test Ward"
    assert feature["properties"]["type"] == "testward"
    assert feature["properties"]["authority_name"] == "Test Body"


def test_at_returns_most_specific_first_and_empty_outside(client, db):
    add_square(db, "Big Ward", "testward", 10, 10.0, 10.0, 11.0, 11.0)
    add_square(db, "Small Campus", "testcampus", 20, 10.2, 10.2, 10.4, 10.4)

    inside_both = client.get("/api/jurisdictions/at", params={"lat": 10.3, "lng": 10.3})
    inside_ward = client.get("/api/jurisdictions/at", params={"lat": 10.8, "lng": 10.8})
    in_the_sea = client.get("/api/jurisdictions/at", params={"lat": 0.0, "lng": 0.0})

    names = [item["name"] for item in inside_both.json()]
    assert names == ["Small Campus", "Big Ward"]
    assert [item["name"] for item in inside_ward.json()] == ["Big Ward"]
    assert in_the_sea.status_code == 200
    assert in_the_sea.json() == []
