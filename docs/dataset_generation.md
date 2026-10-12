# Text dataset generation (v2)

`ml/scripts/generate_text_dataset.py` builds `ml/datasets/civic_text_v2.csv`, a larger synthetic training set. The handwritten `civic_text_v1.csv` is kept untouched as the test set.

## Why not SDV or templates

A first attempt used SDV's Gaussian copula on `civic_text_v1.csv`. It resamples existing column values independently, so it repeated 330 distinct texts and attached the wrong labels to most of them. A later template-based file (`civic_text_synthetic_1000.csv`) had the right labels but only about 230 distinct sentences, one topic for the whole `other` class and a stiff formal tone. Neither writes varied sentences, so the text now comes from a language model.

## How it works

1. The script builds a prompt per request. Each asks a model for a handful of messages on one subcategory. The tone, length, language mix (English, Hinglish) and location use are drawn from a seeded random generator, so one seed always gives the same prompts. The category and subcategory come from the prompt, so the label cannot drift.
2. A backend produces the text (below). The prompts and the model used are saved to `ml/datasets/raw_v2/manifest.json`.
3. `collect` cleans each line (numbering, quotes and "Here are..." lead-ins removed, very short or very long lines dropped).
4. Duplicates are removed: exact matches after lowercasing and stripping punctuation, then near-duplicates by TF-IDF cosine similarity of 0.85 or more within a category. Anything close to a `civic_text_v1.csv` row is dropped too, so no test text leaks into training.
5. Each category is cut to `--per-class` rows (default 1000), shuffled, and written with `source` set to the backend and `split=train`. The categories and subcategories come from `shared/categories.json`.

## Backends

**Ollama (free, local).** Nothing leaves the machine and there are no rate limits.

```
brew install ollama
ollama serve                  # leave running, or open the Ollama app
ollama pull llama3.2:3b       # about 2 GB, fits in 8 GB RAM
python ml/scripts/generate_text_dataset.py run-local --dry-run --per-class 100
python ml/scripts/generate_text_dataset.py run-local --per-class 100   # try small first
python ml/scripts/generate_text_dataset.py collect
```

Requests run one after another and each reply is saved to `ml/datasets/raw_v2/local/`. If a run is interrupted, running the same command again skips the finished requests. A small model asks for 15 messages per request with 1.6x spare rows (`--per-request`, `--overshoot`), because it repeats itself more than a large one. A full 1000-per-class run is roughly 1000 requests and takes hours on a laptop, so test with 100 first and look at the output. `--model` selects another installed model.

**Claude Haiku 5.5 (paid batch).** `submit` sends one Message Batch at half price, and `collect` reads it when it has finished. It needs `ANTHROPIC_API_KEY` and the `anthropic` package.

## Limits to check after a run

- `collect` prints each category's count and how far it is short. A small model may fall well under 1000 after dedupe. Rerun with another `--seed` or a larger `--overshoot`, or accept a smaller balanced set.
- A 3B model's Hinglish is weak and it may repeat phrases. Read a sample of each category, especially `other`, before training. Delete the rows or subcategories that look wrong.
- Evaluate only on the handwritten v1 rows. Never on generated text.
- Record the model name, date and final counts in `ml/datasets/README.md` once the real run is done.
