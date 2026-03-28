import argparse
import json
from pathlib import Path
from statistics import mean
from typing import Dict, Any, List


def _load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object in {path}")
    return payload


def _safe_mean(values: List[float]) -> float:
    return mean(values) if values else 0.0


def _extract_records(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    records = payload.get("records", [])
    if not isinstance(records, list):
        return []
    return [record for record in records if isinstance(record, dict)]


def _summarize(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    latency_delta = [float(r.get("delta", {}).get("avg_latency_ms", 0.0)) for r in records]
    clarify_delta = [float(r.get("delta", {}).get("clarify_rate", 0.0)) for r in records]
    add_success_delta = [float(r.get("delta", {}).get("add_intent_success_rate", 0.0)) for r in records]
    followup_delta = [float(r.get("delta", {}).get("redundant_followup_suspected_rate", 0.0)) for r in records]

    return {
        "samples": len(records),
        "avg_delta_latency_ms": round(_safe_mean(latency_delta), 2),
        "avg_delta_clarify_rate": round(_safe_mean(clarify_delta), 4),
        "avg_delta_add_success_rate": round(_safe_mean(add_success_delta), 4),
        "avg_delta_redundant_followup_rate": round(_safe_mean(followup_delta), 4),
    }


def _evaluate(summary: Dict[str, Any], targets: Dict[str, Any], min_samples: int) -> Dict[str, Any]:
    checks = {
        "samples_ready": summary["samples"] >= min_samples,
        "latency_target_met": summary["avg_delta_latency_ms"] <= 0,
        "clarify_rate_not_worse": summary["avg_delta_clarify_rate"] <= 0,
        "add_success_not_worse": summary["avg_delta_add_success_rate"] >= 0,
        "redundant_followup_not_worse": summary["avg_delta_redundant_followup_rate"] <= 0,
    }

    all_pass = all(checks.values())
    verdict = "promote" if all_pass else "hold"

    return {
        "verdict": verdict,
        "checks": checks,
        "targets_reference": {
            "avg_latency_ms_target": targets.get("avg_latency_ms_target"),
            "clarify_rate_target": targets.get("clarify_rate_target"),
            "add_success_target": targets.get("one_turn_add_success_rate_target"),
            "redundant_followup_target": targets.get("redundant_followup_suspected_rate_target"),
            "min_samples_required": min_samples,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate rollout promotion gate report from monitor logs.")
    parser.add_argument(
        "--monitor-file",
        default="logs/rollout_monitor_24h.json",
        help="Path to rollout monitor JSON file",
    )
    parser.add_argument(
        "--targets-file",
        default="success_targets.json",
        help="Path to success targets JSON file",
    )
    parser.add_argument(
        "--min-samples",
        type=int,
        default=24,
        help="Minimum monitor samples required before promotion decision",
    )
    parser.add_argument(
        "--output-file",
        default="logs/rollout_gate_report.json",
        help="Path to write gate evaluation report",
    )
    args = parser.parse_args()

    monitor_path = Path(args.monitor_file)
    targets_path = Path(args.targets_file)
    output_path = Path(args.output_file)

    if not monitor_path.exists():
        raise FileNotFoundError(f"Monitor file not found: {monitor_path}")
    if not targets_path.exists():
        raise FileNotFoundError(f"Targets file not found: {targets_path}")

    monitor_payload = _load_json(monitor_path)
    targets_payload = _load_json(targets_path)

    records = _extract_records(monitor_payload)
    summary = _summarize(records)
    evaluation = _evaluate(summary, targets_payload, max(1, int(args.min_samples)))

    report = {
        "monitor_file": str(monitor_path),
        "targets_file": str(targets_path),
        "summary": summary,
        "evaluation": evaluation,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)

    print(json.dumps(report, indent=2))
    print(f"Saved gate report to: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
