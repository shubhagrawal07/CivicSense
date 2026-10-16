# Text dataset

`civic_text_v1.csv` is the labelled text set for the report classifier (SL-9). Each row is one citizen complaint and the category it belongs to.

## Columns

| Column | Meaning |
|---|---|
| `id` | Row id, `t0001` onwards |
| `text` | The complaint as a citizen might type it |
| `category` | One of the 10 categories below |
| `subcategory` | Optional finer label, empty for `other` |
| `source` | `handwritten` or `augmented` |
| `split` | `train` or `test` |

## Categories and size

350 rows, 35 per category (25 handwritten and 10 augmented each, except `other` with 28 and 7).

| Category | Subcategories | Train | Test |
|---|---|---|---|
| pothole | pothole_single, road_surface_broken | 28 | 7 |
| open_manhole | lid_missing, lid_broken | 29 | 6 |
| garbage | missed_collection, bin_overflow, illegal_dumping | 27 | 8 |
| streetlight | light_off, light_flickering, pole_damaged | 28 | 7 |
| water_leakage | pipe_leak, pipe_burst | 29 | 6 |
| electricity_outage | power_cut, exposed_wire, transformer_issue | 27 | 8 |
| drainage_sewage | drain_blocked, sewage_overflow, waterlogging | 29 | 6 |
| damaged_infrastructure | footpath, railing_or_divider, public_furniture, signage | 28 | 7 |
| road_obstruction | fallen_tree, debris | 27 | 8 |
| other | none | 29 | 6 |

`other` holds vague texts ("please help", "not working"), nonsense, thanks and follow-ups, and complaints that are not about the nine issue types (noise, stray animals, parking, general queries). It is there so the classifier learns to stay unsure, and low-confidence predictions go to manual review.

## How it was made

- **Handwritten rows** were written by hand to vary length and phrasing: one-word reports, long descriptions, some with a landmark and some without, some Hinglish, some with typos or missing punctuation.
- **Augmented rows** are copies of handwritten rows with a location prefix ("Sector 7 - ...", "Near the railway station: ...") or a closing phrase ("Please fix urgently.") added. They were not rewritten.
- An augmented row always gets the same split as the row it was copied from, so a near-copy of a training row never lands in the test set.

## Known limits

- Small. 70 test rows give a noisy accuracy estimate, so treat scores as rough.
- Augmentation adds little real variety. The prefixes and suffixes are a short fixed set.
- Some subcategories are thin (`signage` has 5 rows, `pole_damaged` has 7). The classifier should not be trained on subcategories yet.
- Streetlights left on during the day are filed under `light_off`, which is not a perfect fit.
- A few categories overlap:
  - Dumped construction debris can read as `garbage` or `road_obstruction`.
  - Illegal parking is `other`, but an abandoned vehicle left on the road is `road_obstruction`.
  - A broken drain cover can read as `open_manhole` or `drainage_sewage`.
- Mostly English with some Hinglish. Other languages and scripts are not covered.
- The texts are invented, not taken from real complaints, so real reports will be messier.

## Out of scope for now

Image data and labels, a much larger dataset, and any hierarchy deeper than one level of subcategories.
