# Department mapping

Every category in `shared/categories.json` maps to exactly one department. The mapping is `shared/category_departments.json`, a plain `category key -> department name` object. Names must match the rows in `app/seed.py`.

| Category | Department |
|---|---|
| pothole | Roads and Infrastructure |
| open_manhole | Drainage and Sewerage |
| garbage | Solid Waste Management |
| streetlight | Street Lighting |
| water_leakage | Water Supply |
| electricity_outage | Electricity |
| drainage_sewage | Drainage and Sewerage |
| damaged_infrastructure | Roads and Infrastructure |
| road_obstruction | Roads and Infrastructure |
| other | General |

## Lookup

`app/intelligence/departments.py`:

```
department_for(db, category, confidence=1.0, threshold=None)
    -> {department_id, name, confidence}
```

The mapping is keyed by name and the id is read from the `departments` table at call time, since ids are assigned by the database. If a department row is missing it raises, which means the seed has not been run.

Goes to the default department (`General`) when:

- the category is not in the mapping, with confidence reported as 0, or
- the confidence is below the threshold (same setting as the text classifier).

## Decisions

- `road_obstruction` (fallen trees, debris) goes to Roads and Infrastructure. Parks and Public Spaces would suit trees, but most of the category is debris on the carriageway.
- `damaged_infrastructure` goes to Roads and Infrastructure since footpaths, dividers and signage are road assets. Bus-stop shelters and benches could belong to Parks and Public Spaces; no category points there yet, so that department is unused.
- `open_manhole` and `drainage_sewage` share a department on purpose.
- The authority lookup (which local body and contact handles that department in a given area) is a separate step.

Tests: `backend/tests/test_departments.py` checks that the mapping covers the taxonomy exactly and only names seeded departments.
