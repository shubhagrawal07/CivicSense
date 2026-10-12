# Category taxonomy

The list of issue categories lives in one file, `shared/categories.json`. The classifier, department mapping, severity rules, duplicate matching and the map filters all use the same keys.

## Shape

- `categories` is a list of `{ key, label, subcategories }`. Keys are lowercase snake_case and are what gets stored in the database and written in the dataset. Labels are only for display.
- Subcategories are optional and one level deep. They are not used for classification yet.
- `fallback` names the category used when the classifier is unsure. It is `other`, and a low-confidence prediction goes to manual review instead of being trusted.
- `version` goes up whenever a key is added, renamed or removed.

## Using it

- Backend: load the file once at startup and build the allowed values from it, instead of hard-coding a second list.
- ML: `ml/datasets/civic_text_v1.csv` uses these keys in its `category` and `subcategory` columns. Training code should read the class list from this file.
- Frontend: import the JSON for filters and labels.

## Decisions

- There are ten categories. The nine issue types from SL-9 plus `road_obstruction`, added because fallen trees and dumped debris did not fit anywhere else.
- Renaming a key means updating the dataset, any stored rows and the trained model together, so avoid it. Adding a category is cheaper but needs new training examples first.
- The dataset itself is described in `ml/datasets/README.md`.
