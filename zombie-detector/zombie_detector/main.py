import argparse
import json
import sys
from pathlib import Path
from zombie_detector import process_zombies
from .core.processor import (
    filter_zombies,
    get_zombie_summary,
    get_killed_zombies_summary,
)
from .core.zombie_tracker import ZombieTracker
from .utils.utils import save_results_json, save_results_csv, generate_report_timestamp


def main():
    """
    Command line interface for the zombie detector.
    """
    parser = argparse.ArgumentParser(
        description="Detect zombie hosts based on performance criteria"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Main detection command
    detect_parser = subparsers.add_parser("detect", help="Detect zombies")
    detect_parser.add_argument(
        "data_path", help="Path to the input JSON file with host data"
    )
    detect_parser.add_argument(
        "--state-path",
        default="states.json",
        help="Path to the criterion states configuration file",
    )
    detect_parser.add_argument("--output", "-o", help="Output file path (JSON or CSV)")
    detect_parser.add_argument(
        "--format", choices=["json", "csv"], default="json", help="Output format"
    )
    detect_parser.add_argument(
        "--zombies-only",
        action="store_true",
        help="Return only hosts classified as zombies",
    )
    detect_parser.add_argument(
        "--summary", action="store_true", help="Show summary statistics"
    )
    detect_parser.add_argument(
        "--verbose", "-v", action="store_true", help="Verbose output"
    )
    detect_parser.add_argument(
        "--no-tracking", action="store_true", help="Disable zombie tracking"
    )
    detect_parser.add_argument(
        "--no-kafka", action="store_true", help="Disable Kafka publishing"
    )

    # Killed zombies command
    killed_parser = subparsers.add_parser("killed", help="Show killed zombies")
    killed_parser.add_argument(
        "--since-hours",
        type=int,
        default=24,
        help="Hours to look back for killed zombies (default: 24)",
    )
    killed_parser.add_argument("--output", "-o", help="Output file path")
    killed_parser.add_argument(
        "--format", choices=["json", "csv"], default="json", help="Output format"
    )

    # Check specific zombie
    check_parser = subparsers.add_parser("check", help="Check specific zombie status")
    check_parser.add_argument("zombie_id", help="Dynatrace host ID to check")
    check_parser.add_argument(
        "--lifecycle", action="store_true", help="Show full lifecycle"
    )

    # Cleanup command
    cleanup_parser = subparsers.add_parser("cleanup", help="Clean up old tracking data")
    cleanup_parser.add_argument(
        "--days", type=int, default=30, help="Days of data to keep (default: 30)"
    )

    # If no command specified, default to detect for backward compatibility
    args = parser.parse_args()
    if not args.command:
        # Parse as old-style arguments for backward compatibility
        parser = argparse.ArgumentParser(description="Detect zombie hosts")
        parser.add_argument("data_path", help="Path to the input JSON file")
        parser.add_argument("--state-path", default="states.json")
        parser.add_argument("--output", "-o")
        parser.add_argument("--format", choices=["json", "csv"], default="json")
        parser.add_argument("--zombies-only", action="store_true")
        parser.add_argument("--summary", action="store_true")
        parser.add_argument("--verbose", "-v", action="store_true")
        args = parser.parse_args()
        args.command = "detect"
        args.no_tracking = False

    try:
        if args.command == "detect":
            handle_detect_command(args)
        elif args.command == "killed":
            handle_killed_command(args)
        elif args.command == "check":
            handle_check_command(args)
        elif args.command == "cleanup":
            handle_cleanup_command(args)
        else:
            parser.print_help()
            sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def handle_detect_command(args):
    """Handle zombie detection command."""
    if not Path(args.data_path).exists():
        print(f"Error: Input file '{args.data_path}' not found", file=sys.stderr)
        sys.exit(1)

    if args.verbose:
        print(f"Processing hosts from: {args.data_path}")
        print(f"Using states from: {args.state_path}")
        if args.no_tracking:
            print("Zombie tracking disabled")
        if args.no_kafka:
            print("Kafka publishing disabled")

    # Load data and states
    with open(args.data_path) as f:
        hosts = json.load(f)

    from .core.state_loader import load_criterion_type_states

    state_map = load_criterion_type_states(args.state_path)

    # Process with updated parameters
    from .core.processor import process_host_data

    results = process_host_data(
        hosts,
        state_map,
        enable_tracking=not args.no_tracking,
        enable_kafka=not args.no_kafka,
    )

    # Filter zombies only if requested
    if args.zombies_only:
        results = filter_zombies(results)
        if args.verbose:
            print(f"Filtered to {len(results)} zombie hosts")

    # Show tracking info if available
    if not args.no_tracking and results:
        tracking_info = results[0].get("_tracking_info")
        if tracking_info and args.verbose:
            print(f"\n=== Zombie Tracking ===")
            print(f"New zombies: {len(tracking_info['new_zombies'])}")
            print(f"Persisting zombies: {len(tracking_info['persisting_zombies'])}")
            print(f"Killed zombies: {len(tracking_info['killed_zombies'])}")

            if tracking_info["killed_zombies"]:
                print(f"Recently killed: {tracking_info['killed_zombies']}")

    # Show summary if requested
    if args.summary:
        summary = get_zombie_summary(results)
        print("\n=== Zombie Detection Summary ===")
        print(f"Total hosts: {summary['total_hosts']}")
        print(f"Zombie hosts: {summary['zombie_hosts']}")
        print(f"Non-zombie hosts: {summary['non_zombie_hosts']}")
        print(f"Zombie percentage: {summary['zombie_percentage']}%")
        print("\nCriterion breakdown:")
        for criterion, count in summary["criterion_breakdown"].items():
            print(f"  {criterion}: {count}")
        print()

    # Save results if output path specified
    if args.output:
        # Remove tracking info before saving
        clean_results = []
        for result in results:
            clean_result = {k: v for k, v in result.items() if k != "_tracking_info"}
            clean_results.append(clean_result)

        if args.format == "csv":
            save_results_csv(clean_results, args.output)
        else:
            save_results_json(clean_results, args.output)

        if args.verbose:
            print(f"Results saved to: {args.output}")
    else:
        # Print to stdout (remove tracking info)
        clean_results = []
        for result in results:
            clean_result = {k: v for k, v in result.items() if k != "_tracking_info"}
            clean_results.append(clean_result)

        if args.format == "csv":
            import csv

            if clean_results:
                writer = csv.DictWriter(sys.stdout, fieldnames=clean_results[0].keys())
                writer.writeheader()
                writer.writerows(clean_results)
        else:
            print(json.dumps(clean_results, indent=2, default=str))


def handle_killed_command(args):
    """Handle killed zombies command."""
    summary = get_killed_zombies_summary(args.since_hours)

    print(f"=== Killed Zombies (last {args.since_hours} hours) ===")
    print(f"Total killed: {summary['killed_zombies_count']}")

    if summary["killed_zombies"]:
        print("\nKilled zombies:")
        for zombie in summary["killed_zombies"]:
            print(
                f"  {zombie['dynatrace_host_id']} ({zombie['hostname']}) - {zombie['criterion_alias']} - Killed at: {zombie['killed_at']}"
            )

        print("\nCriterion breakdown:")
        for criterion, count in summary["criterion_breakdown"].items():
            print(f"  {criterion}: {count}")

    if args.output:
        if args.format == "csv":
            save_results_csv(summary["killed_zombies"], args.output)
        else:
            save_results_json(summary, args.output)
        print(f"\nResults saved to: {args.output}")


def handle_check_command(args):
    """Handle check specific zombie command."""
    tracker = ZombieTracker()

    if args.lifecycle:
        lifecycle = tracker.get_zombie_lifecycle(args.zombie_id)
        print(f"=== Zombie Lifecycle: {args.zombie_id} ===")
        print(f"First seen: {lifecycle['first_seen'] or 'Never'}")
        print(f"Last seen: {lifecycle['last_seen'] or 'Never'}")
        print(f"Total detections: {lifecycle['total_detections']}")
        print(f"Currently active: {lifecycle['is_active']}")

        if lifecycle["killed_info"]:
            print(f"Killed at: {lifecycle['killed_info']['killed_at']}")
            print(f"Last type: {lifecycle['killed_info']['criterion_alias']}")

        if lifecycle["detection_history"]:
            print(f"\nDetection history:")
            for detection in lifecycle["detection_history"][-5:]:  # Last 5
                print(f"  {detection['timestamp']}: {detection['criterion_alias']}")
    else:
        killed_info = tracker.is_zombie_killed(args.zombie_id)
        if killed_info:
            print(f"✅ Zombie {args.zombie_id} was KILLED")
            print(f"   Killed at: {killed_info['killed_at']}")
            print(f"   Last type: {killed_info['criterion_alias']}")
            print(f"   Hostname: {killed_info['hostname']}")
        else:
            # Check if it's currently active
            current_zombies = tracker._load_current_zombies()
            is_active = any(
                z["dynatrace_host_id"] == args.zombie_id for z in current_zombies
            )

            if is_active:
                print(f"🧟 Zombie {args.zombie_id} is STILL ACTIVE")
            else:
                print(f"❓ Zombie {args.zombie_id} not found in recent data")


def handle_cleanup_command(args):
    """Handle cleanup command."""
    tracker = ZombieTracker()
    tracker.cleanup_old_data(args.days)
    print(f"✅ Cleaned up zombie tracking data older than {args.days} days")


if __name__ == "__main__":
    main()
