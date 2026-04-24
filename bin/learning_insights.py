#!/usr/bin/env python3
"""Query execution metrics and learning insights."""

import sys
from pathlib import Path
import json

sys.path.insert(0, str(Path(__file__).parent.parent))

from domains.learning import LearningDomain


def print_summary(domain: LearningDomain) -> None:
    """Print overall performance summary."""
    summary = domain.get_metrics_summary()

    if summary.get("total_executions", 0) == 0:
        print("📊 No execution records yet")
        return

    print("\n📊 Overall Performance Summary")
    print("=" * 70)
    print(f"Total Executions: {summary['total_executions']}")
    print(f"Success Rate:     {summary['success_rate']:.1%}")
    print(f"Avg Time:         {summary['average_time_seconds']:.1f}s")
    print(f"Models Used:      {', '.join(summary['models_used'])}")
    print(f"Executors Used:   {', '.join(summary['executors_used'])}")


def print_task_type_breakdown(domain: LearningDomain) -> None:
    """Print performance by task type."""
    task_types = domain.get_all_task_types()

    if not task_types:
        print("ℹ️  No task execution history")
        return

    print("\n📈 Performance by Task Type")
    print("=" * 70)

    for task_type in sorted(task_types):
        summary = domain.get_metrics_summary(task_type)
        success = summary["success_rate"]
        count = summary["total_executions"]
        avg_time = summary["average_time_seconds"]

        # Icon based on success rate
        if success >= 0.8:
            icon = "✅"
        elif success >= 0.6:
            icon = "⚠️ "
        else:
            icon = "❌"

        print(
            f"{icon} {task_type:20s} {success:6.1%} success ({count:2d} tasks, {avg_time:5.1f}s avg)"
        )


def print_model_recommendations(domain: LearningDomain) -> None:
    """Print recommended models for each executor/task type combo."""
    task_types = domain.get_all_task_types()
    executors = set()

    for r in domain.records:
        executors.add(r.executor)

    if not task_types or not executors:
        return

    print("\n🤖 Model Recommendations")
    print("=" * 70)

    for task_type in sorted(task_types):
        print(f"\n{task_type}:")
        for executor in sorted(executors):
            rec = domain.recommend_model(task_type, executor)
            print(
                f"  {executor:20s} → {rec.model:30s} ({rec.success_rate:.0%} | confidence: {rec.confidence:.0%})"
            )


def print_escalation_report(domain: LearningDomain) -> None:
    """Print tasks that should be escalated."""
    report = domain.get_escalation_report()

    if not report:
        return

    escalations = [r for r in report if r[1]]

    if escalations:
        print("\n⬆️  Escalation Recommendations")
        print("=" * 70)
        for task_type, should_escalate, reason in escalations:
            print(f"  {task_type:20s} → {reason}")
    else:
        print("\n✅ No escalations needed")


def print_failure_analysis(domain: LearningDomain) -> None:
    """Print failure pattern analysis."""
    task_types = domain.get_all_task_types()

    print("\n🔍 Failure Patterns")
    print("=" * 70)

    has_patterns = False
    for task_type in sorted(task_types):
        patterns = domain.get_failure_patterns(task_type)
        if patterns:
            has_patterns = True
            print(f"\n{task_type}:")
            for error, count in patterns.items():
                print(f"  {error:25s} ({count}x)")

    if not has_patterns:
        print("✅ No significant failure patterns")


def print_recent_failures(domain: LearningDomain) -> None:
    """Print recent failures."""
    failures = domain.recent_failures(10)

    if not failures:
        print("\n✅ No recent failures")
        return

    print("\n📋 Recent Failures (Last 10)")
    print("=" * 70)

    for record in failures:
        print(f"\n  Task:    {record.task_type} - {record.description[:50]}")
        print(f"  Model:   {record.model}")
        print(f"  Error:   {record.error_type or 'Unknown'}")
        print(f"  Time:    {record.duration_seconds:.1f}s")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Query execution metrics and learning insights"
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Show overall performance summary",
    )
    parser.add_argument(
        "--by-task",
        action="store_true",
        help="Show performance breakdown by task type",
    )
    parser.add_argument(
        "--models",
        action="store_true",
        help="Show model recommendations",
    )
    parser.add_argument(
        "--escalations",
        action="store_true",
        help="Show escalation recommendations",
    )
    parser.add_argument(
        "--failures",
        action="store_true",
        help="Show failure analysis",
    )
    parser.add_argument(
        "--recent",
        action="store_true",
        help="Show recent failures",
    )
    parser.add_argument(
        "--task",
        help="Focus on specific task type",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Show all reports",
    )

    args = parser.parse_args()

    domain = LearningDomain(Path.cwd())

    # Default: show everything
    if not any(
        [
            args.summary,
            args.by_task,
            args.models,
            args.escalations,
            args.failures,
            args.recent,
            args.all,
        ]
    ):
        args.all = True

    if args.summary or args.all:
        print_summary(domain)

    if args.by_task or args.all:
        print_task_type_breakdown(domain)

    if args.models or args.all:
        print_model_recommendations(domain)

    if args.escalations or args.all:
        print_escalation_report(domain)

    if args.failures or args.all:
        print_failure_analysis(domain)

    if args.recent or args.all:
        print_recent_failures(domain)

    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
