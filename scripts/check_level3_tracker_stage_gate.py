"""Check whether a Level3 tracker qualification stage may unlock the next stage."""

from __future__ import annotations

import argparse
import json
import operator
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable


ROOT = Path(__file__).parents[1]
DEFAULT_GATES = ROOT / "experiments/level3_ppo_loop/tracker_qualification_gates.json"

COMPARATORS: dict[str, Callable[[Any, Any], bool]] = {
    "==": operator.eq,
    ">=": operator.ge,
    "<=": operator.le,
    ">": operator.gt,
    "<": operator.lt,
}


def parse_args() -> argparse.Namespace:
    """Parse stage-gate checker arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", required=True, help="Stage id, e.g. hover.")
    parser.add_argument("--metrics-json", type=Path, required=True)
    parser.add_argument("--gates-json", type=Path, default=DEFAULT_GATES)
    parser.add_argument("--history-json", type=Path)
    parser.add_argument(
        "--require-prerequisites",
        action="store_true",
        help="Require all earlier stages to be marked passed in metrics/history JSON.",
    )
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    """Load a JSON object from disk."""
    data = json.loads(path.read_text())
    if not isinstance(data, dict):
        raise TypeError(f"Expected JSON object in {path}")
    return data


def stage_by_id(gates: dict[str, Any], stage_id: str) -> dict[str, Any]:
    """Return one stage definition from a gate spec."""
    for stage in gates.get("stages", []):
        if stage.get("id") == stage_id:
            return stage
    raise KeyError(f"Unknown tracker qualification stage: {stage_id}")


def previous_stages(gates: dict[str, Any], stage: dict[str, Any]) -> list[dict[str, Any]]:
    """Return all stages that must already have passed before this stage."""
    stage_order = int(stage["order"])
    return sorted(
        [item for item in gates.get("stages", []) if int(item["order"]) < stage_order],
        key=lambda item: int(item["order"]),
    )


def extract_stage_metrics(metrics_doc: dict[str, Any], stage_id: str) -> dict[str, Any]:
    """Extract metrics for one stage from common report shapes."""
    for key in ("stage_results", "stages", "tasks"):
        container = metrics_doc.get(key)
        if isinstance(container, dict) and isinstance(container.get(stage_id), dict):
            return merge_top_level_context(metrics_doc, container[stage_id])
        if isinstance(container, list):
            for item in container:
                if isinstance(item, dict) and item.get("id", item.get("stage")) == stage_id:
                    return merge_top_level_context(metrics_doc, item)
    if metrics_doc.get("id", metrics_doc.get("stage")) == stage_id:
        return metrics_doc
    return metrics_doc


def merge_top_level_context(root: dict[str, Any], stage_metrics: dict[str, Any]) -> dict[str, Any]:
    """Merge report-level booleans with a stage-specific metrics object."""
    merged = {
        key: value
        for key, value in root.items()
        if key not in {"stage_results", "stages", "tasks", "metrics", "summary"}
    }
    merged.update(stage_metrics)
    return merged


def metric_lookup(metrics: dict[str, Any], name: str) -> Any:
    """Look up a metric by direct key or dotted path."""
    roots = [metrics]
    for key in ("metrics", "summary", "validation"):
        nested = metrics.get(key)
        if isinstance(nested, dict):
            roots.append(nested)

    for root in roots:
        if name in root:
            return root[name]
        value = lookup_dotted(root, name)
        if value is not _MISSING:
            return value
    return _MISSING


def lookup_dotted(root: dict[str, Any], name: str) -> Any:
    """Look up a dotted-path metric from a nested dict."""
    value: Any = root
    for part in name.split("."):
        if not isinstance(value, dict) or part not in value:
            return _MISSING
        value = value[part]
    return value


def history_stage_passed(history_doc: dict[str, Any], stage_id: str) -> bool:
    """Return whether a previous stage is marked passed in history."""
    stage_metrics = extract_stage_metrics(history_doc, stage_id)
    for key in ("passed", "stage_gate_passed", "completion_gate_passed"):
        value = metric_lookup(stage_metrics, key)
        if value is not _MISSING:
            return bool(value)
    return False


def evaluate_stage(
    gates: dict[str, Any],
    stage_id: str,
    metrics_doc: dict[str, Any],
    *,
    history_doc: dict[str, Any] | None = None,
    require_prerequisites: bool = False,
) -> dict[str, Any]:
    """Evaluate one stage gate and return a machine-readable summary."""
    stage = stage_by_id(gates, stage_id)
    metrics = extract_stage_metrics(metrics_doc, stage_id)
    history = history_doc or metrics_doc
    checked: list[dict[str, Any]] = []
    failures: list[str] = []

    if require_prerequisites:
        for prerequisite in previous_stages(gates, stage):
            prerequisite_id = str(prerequisite["id"])
            if not history_stage_passed(history, prerequisite_id):
                failures.append(f"prerequisite stage {prerequisite_id!r} is not marked passed")

    for gate in stage.get("required_metrics", []):
        metric_name = str(gate["name"])
        op = str(gate["op"])
        expected = gate["value"]
        actual = metric_lookup(metrics, metric_name)
        if actual is _MISSING:
            failures.append(f"missing metric {metric_name!r}")
            checked.append(
                {
                    "name": metric_name,
                    "op": op,
                    "expected": expected,
                    "actual": None,
                    "passed": False,
                }
            )
            continue
        passed = compare_metric(actual, op, expected)
        checked.append(
            {
                "name": metric_name,
                "op": op,
                "expected": expected,
                "actual": actual,
                "passed": passed,
            }
        )
        if not passed:
            failures.append(
                f"{metric_name}: actual {actual!r} does not satisfy {op} {expected!r}"
            )

    passed = not failures
    return {
        "lane": gates.get("lane"),
        "stage": stage_id,
        "task": stage.get("task"),
        "config": stage.get("config"),
        "environment": stage.get("environment"),
        "passed": passed,
        "next_stage_unlocked": stage.get("next_stage") if passed else None,
        "failures": failures,
        "checked_metrics": checked,
    }


def compare_metric(actual: Any, op: str, expected: Any) -> bool:
    """Compare one metric value with JSON-defined gate semantics."""
    if op not in COMPARATORS:
        raise ValueError(f"Unsupported metric operator: {op}")
    if isinstance(expected, bool):
        actual = bool(actual)
    return bool(COMPARATORS[op](actual, expected))


class _MissingMetric:
    """Sentinel for a metric that is absent from a report."""


_MISSING = _MissingMetric()


def main() -> None:
    """Run the stage-gate checker from the command line."""
    args = parse_args()
    gates = load_json(args.gates_json)
    metrics = load_json(args.metrics_json)
    history = load_json(args.history_json) if args.history_json else None
    summary = evaluate_stage(
        gates,
        args.stage,
        metrics,
        history_doc=history,
        require_prerequisites=args.require_prerequisites,
    )
    text = json.dumps(summary, indent=2, sort_keys=True) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text)
    print(text, end="")
    if not summary["passed"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
