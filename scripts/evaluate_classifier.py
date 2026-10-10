"""Measure classifier accuracy on the held-out labelled samples.

    python scripts/evaluate_classifier.py                 # offline TF-IDF model
    python scripts/evaluate_classifier.py --transformer   # needs the [ai] extra

Prints overall accuracy, accuracy among confidently classified documents, and
a per-category breakdown. Re-run it after changing training data or thresholds.
"""

import argparse
import json
import os
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

SAMPLES = ROOT / "tests" / "data" / "labeled_samples.json"


def evaluate(use_transformer: bool = False) -> dict:
    if use_transformer:
        os.environ.pop("SMART_ORGANIZER_DISABLE_TRANSFORMERS", None)
    else:
        os.environ["SMART_ORGANIZER_DISABLE_TRANSFORMERS"] = "1"

    from smart_ai_file_organizer.classifier import DocumentClassifier

    clf = DocumentClassifier(config_path=ROOT / "config.example.json")
    clf.train()
    samples = json.loads(SAMPLES.read_text(encoding="utf-8"))

    per_cat = defaultdict(lambda: [0, 0])
    total = correct = confident = confident_correct = 0
    for label, texts in samples.items():
        for text in texts:
            predicted, _, is_low = clf.predict_with_confidence(text)
            hit = predicted == label
            total += 1
            correct += hit
            per_cat[label][0] += hit
            per_cat[label][1] += 1
            if not is_low:
                confident += 1
                confident_correct += hit
    return {
        "model": clf.model_name,
        "total": total,
        "accuracy": correct / total,
        "confident": confident,
        "confident_accuracy": (confident_correct / confident) if confident else 0.0,
        "per_category": {k: v[0] / v[1] for k, v in per_cat.items()},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--transformer", action="store_true", help="use sentence-transformers")
    result = evaluate(parser.parse_args().transformer)
    print(f"Model     : {result['model']}")
    print(f"Samples   : {result['total']}")
    print(f"Accuracy  : {result['accuracy']:.1%}")
    print(f"Confident : {result['confident']}/{result['total']} documents, "
          f"{result['confident_accuracy']:.1%} accurate")
    for cat, acc in sorted(result["per_category"].items()):
        print(f"  {cat:<10} {acc:.0%}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
