"""Guard against classifier regressions using the held-out labelled samples."""

import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "evaluate_classifier.py"


def _evaluate():
    spec = importlib.util.spec_from_file_location("evaluate_classifier", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.evaluate(use_transformer=False)


def test_tfidf_accuracy_on_held_out_samples():
    result = _evaluate()
    assert result["total"] >= 50
    assert result["accuracy"] >= 0.90, result


def test_confident_predictions_are_more_reliable_than_average():
    result = _evaluate()
    assert result["confident_accuracy"] >= result["accuracy"]
