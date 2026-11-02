"""Write LinkedIn drafts for AIOrbit Lab. You paste them.

Examples:
  python3 -m automation.run --check
  python3 -m automation.run --demo
  python3 -m automation.run --concept "What is a Kubernetes pod"
  python3 -m automation.run --week
  python3 -m automation.run --audit --file automation/examples/analytics-sample.csv
"""

import argparse
import sys
from pathlib import Path

from .config import Config


def check(config: Config) -> int:
    """Print what is already done and what still has to be supplied."""
    print("LinkedIn GIF runner")
    print("A post is one roadmap GIF plus the caption under it.")
    print("Cadence: one new topic every 2 days.")
    print(f"Roadmaps: {len(__import__('automation.boards', fromlist=['BOARDS']).BOARDS)}")
    print(f"Output: {config.output_dir}")
    print("Voice file: not used for GIF posts.")
    print("LinkedIn login: not used. Upload the GIF and paste the caption.")
    print(f"Bedrock key: {'set' if config.bedrock_token else 'missing'} ({config.bedrock_region})")
    gaps = config.missing(need_model=True)
    if gaps:
        print("\nOptional, only for comments, DMs, and model rewrites:")
        for gap in gaps:
            print(f"- {gap}")
    print("\nReady for GIF posts and the profile kit.")
    return 0


def _mode_count(args: argparse.Namespace) -> int:
    flags = (
        args.demo,
        args.week,
        bool(args.comment),
        bool(args.reply),
        bool(args.profile),
        bool(args.carousel),
        bool(args.repurpose),
        bool(args.dm),
        bool(args.inbox),
        bool(args.audit),
        bool(args.human),
    )
    return sum(1 for flag in flags if flag)


def main() -> int:
    parser = argparse.ArgumentParser(description="AIOrbit Lab LinkedIn drafts")
    parser.add_argument("--check", action="store_true", help="Show what is still missing")
    parser.add_argument("--demo", action="store_true", help="Build the demo-to-production GIF without marking it used")
    parser.add_argument("--profile-kit", action="store_true", help="Write the recruiter profile from the resume")
    parser.add_argument("--scheduled", action="store_true", help="Create a GIF only when the last one is at least 2 days old")
    parser.add_argument("--count", type=int, default=1, help="How many posts to draft this run")
    parser.add_argument("--stage", default=None, help="Run one post stage. Omit to run every stage.")
    parser.add_argument("--concept", default=None, help="Draft this idea instead of picking a topic")
    parser.add_argument("--week", action="store_true", help="Write the week plan")
    parser.add_argument("--draft", action="store_true", help="With --week, also draft the three posts")
    parser.add_argument("--comment", action="store_true", help="Comment on a pasted post")
    parser.add_argument("--reply", action="store_true", help="Reply to comments on your post")
    parser.add_argument("--profile", action="store_true", help="Score a pasted profile")
    parser.add_argument("--carousel", action="store_true", help="Build carousel copy and a PDF")
    parser.add_argument("--repurpose", action="store_true", help="Turn a transcript into posts")
    parser.add_argument("--dm", action="store_true", help="Write an invite note and two follow-ups")
    parser.add_argument("--inbox", action="store_true", help="Sort pasted messages")
    parser.add_argument("--audit", action="store_true", help="Rank a CSV of past posts")
    parser.add_argument("--human", action="store_true", help="Clean and score one text file")
    parser.add_argument("--file", default="", help="Input file for comment, reply, profile, inbox, audit, human, repurpose")
    parser.add_argument("--who", default="", help="Who the DM is for")
    parser.add_argument("--reason", default="", help="The specific reason to message them now")
    parser.add_argument("--want", default="", help="What you want from the conversation")
    parser.add_argument("--schedule", action="store_true", help="Install the every-2-days Mac schedule")
    parser.add_argument("--unschedule", action="store_true", help="Remove the Mac draft schedule")
    args = parser.parse_args()

    config = Config()
    if args.schedule:
        from .schedule import install

        install()
        return 0
    if args.unschedule:
        from .schedule import remove

        remove()
        return 0
    if args.check:
        return check(config)
    if _mode_count(args) > 1:
        print("Pick one command. For example --demo, or --week, or --concept.", flush=True)
        return 1

    source = Path(args.file) if args.file else None
    if source and not source.is_absolute():
        source = Path.cwd() / source

    if args.human:
        if source is None or not source.exists():
            print("Pass --file with the draft to clean.", flush=True)
            return 1
        from .tasks import humanize_file

        return humanize_file(source)
    if args.audit:
        if source is None or not source.exists():
            print("Pass --file with a CSV export.", flush=True)
            return 1
        from .audit_math import format_audit, load_rows

        text = format_audit(load_rows(source))
        print(text, flush=True)
        return 0
    if args.profile_kit or (args.profile and source is None):
        from .profile_kit import write_profile_kit

        folder = write_profile_kit(config.output_dir / "profile")
        print(f"Profile kit: {folder}", flush=True)
        print((folder / "PASTE-ORDER.txt").read_text(encoding="utf-8"), flush=True)
        return 0
    if args.profile:
        if not source.exists():
            print("Pass --file with the profile paste, or run --profile-kit for the resume rewrite.", flush=True)
            return 1
        from .tasks import profile_report

        return profile_report(config, source)
    if args.inbox:
        if source is None or not source.exists():
            print("Pass --file with the messages, separated by a line of ---.", flush=True)
            return 1
        from .tasks import inbox_triage

        return inbox_triage(config, source)
    if args.week:
        from .tasks import week_plan

        return week_plan(config, draft=args.draft)

    # The default path is a GIF plus a caption. It does not read a voice file.
    gif_path = args.scheduled or args.demo or (_mode_count(args) == 0 and not args.stage)
    if gif_path:
        from .feed import run_feed

        return run_feed(
            config,
            demo=args.demo,
            concept=None if args.demo else args.concept,
            count=max(1, args.count),
            scheduled=args.scheduled,
        )

    needs_model = True
    if needs_model:
        gaps = config.missing(need_model=True)
        if gaps:
            print("This run cannot start yet:", flush=True)
            for gap in gaps:
                print(f"- {gap}", flush=True)
            return 1

    if args.comment:
        if source is None or not source.exists():
            print("Pass --file with the other person's post.", flush=True)
            return 1
        from .tasks import comment_on

        return comment_on(config, source)
    if args.reply:
        if source is None or not source.exists():
            print("Pass --file with the comments, separated by a line of ---.", flush=True)
            return 1
        from .tasks import reply_to

        return reply_to(config, source)
    if args.carousel:
        if not args.concept:
            print('Pass --concept "the sequence you want on the slides".', flush=True)
            return 1
        from .tasks import carousel

        return carousel(config, args.concept)
    if args.repurpose:
        if source is None or not source.exists():
            print("Pass --file with the transcript or article.", flush=True)
            return 1
        from .tasks import repurpose

        return repurpose(config, source)
    if args.dm:
        from .tasks import write_dm

        return write_dm(config, args.who, args.reason, args.want)

    from .jobs import run_jobs

    return run_jobs(
        config,
        only=args.stage,
        demo=args.demo,
        count=max(1, args.count),
        concept=args.concept,
    )


if __name__ == "__main__":
    sys.exit(main())
