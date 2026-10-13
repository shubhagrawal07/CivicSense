# Text classifier

Turns the optional description on a report into a category, a confidence and a list of runner-up categories. It runs only when the report has a description.

## Model

TF-IDF features feeding a Logistic Regression. Two vectorisers are joined: word 1-2 grams, and character 2-4 grams inside word boundaries (`char_wb`). The character part is there so typos and romanised Hindi ("kachra", "bijli") share some features with the spelled-out words. Classes are weighted by frequency so `other` does not drown the rest.

The fitted pipeline (vectoriser and classifier together) is one file, `ml/models/text_classifier.joblib`. It is loaded once at app startup (`lifespan` in `app/main.py`) and cached.

## Training data

- Train: the `train` split of `civic_text_v1.csv` plus the generated set, with duplicate texts dropped. The generated set is `civic_text_v2.csv` (see `dataset_generation.md`) when it exists, otherwise `civic_text_synthetic_1000.csv`.
- Hold-out: the `test` split of `civic_text_v1.csv`, handwritten and never trained on. Any training text that also appears in it is removed.
- The class list comes from `shared/categories.json`, and the script stops if the data uses a key that is not there.

## Retraining

```
python ml/training/train_text.py             # handwritten + synthetic
python ml/training/train_text.py --no-synthetic
```

Seed is fixed at 42, so a rerun gives the same model and the same `ml/reports/text_classifier.json`. The script rewrites the model, the JSON and `ml/reports/text_classifier.md`. Install `ml/requirements.txt` first. Keep the scikit-learn version the same as in `backend/requirements.txt`, because a pickled model is not guaranteed to load across versions.

## Inference

`app/intelligence/text_classifier.py`:

```
classify_text(text, threshold=None) -> {
    category, confidence, top_k: [{category, confidence}, ...], needs_review
}
```

- `top_k` is the three highest probabilities from the model, descending. The fusion step (SL-26) reads these.
- `confidence` is the top probability. If it is below the threshold, `needs_review` is true and `category` is `other`; `top_k` still shows what the model actually thought.
- Empty or punctuation-only text returns `other`, confidence 0, `needs_review` true and an empty `top_k`, without touching the model.
- The threshold is `TEXT_CONFIDENCE_THRESHOLD` in `.env` (default 0.5). The `threshold` argument overrides it per call.
- A call takes a few milliseconds once the model is loaded.

## Choosing the threshold

On the hold-out set, 0.5 answers 57% of texts on its own with 95% accuracy on those; the remaining 43% go to review. 0.4 keeps 81% at 84%, and 0.6 keeps 48% at 94%. The table is in `ml/reports/text_classifier.md`. The threshold was picked by reading that table on the hold-out itself, so treat 0.5 as a starting value and revisit it with real reports.

## Results and weaknesses

Accuracy is 0.78 on 69 hold-out rows (see `ml/reports/text_classifier.md` for per-class scores and the confusion matrix).

- The hold-out is small, about 7 rows per class, and 18 of the rows are augmented copies of others. One text changes a class score by 12 to 17 points, so the numbers are rough.
- Weakest classes are `drainage_sewage` (precision 0.5), `electricity_outage` (recall 0.5) and `streetlight` (recall 0.57).
- Short Hinglish texts such as "bijli nahi hai 6 ghante se" come out with low confidence and wrong labels. The training set has few of them. They do land in review, which is the intended outcome.
- Texts that mention a place on the road ("cable lying on the road") get pulled toward `road_obstruction`.
- Water on the road is split between `water_leakage` and `drainage_sewage`, which the dataset README already lists as an overlap.
- `other` texts that share words with real categories ("construction work noise", "thank you for fixing the road") get a real category with low confidence, so they mostly reach review rather than being wrongly routed.
- The generated training rows (`civic_text_v2.csv`, made with llama3.2:3b) are noisy. Some lines have no topic words ("Could you please send someone to fill it up") and the romanised Hindi is often not real Hindi. Training on them gave 0.783 against 0.768 for the old synthetic set and 0.725 for handwritten rows only, but one hold-out row is the gap between the first two, so that difference is not reliable.

Better coverage needs more handwritten Hinglish and more `other` examples, or the LLM-generated set described in `dataset_generation.md`.
