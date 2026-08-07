"""Command-line entry point for executable chapters."""

import argparse

from engagement_dev.scenarios import chapter_four_report, chapter_one_report, chapter_three_report, chapter_two_report, chapter_zero_report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="engagement-dev")
    parser.add_argument("chapter", choices=("chapter-0", "chapter-1", "chapter-2", "chapter-3", "chapter-4"), help="chapter scenario to run")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.chapter == "chapter-0":
        print(chapter_zero_report(), end="")
    elif args.chapter == "chapter-1":
        print(chapter_one_report(), end="")
    elif args.chapter == "chapter-2":
        print(chapter_two_report(), end="")
    elif args.chapter == "chapter-3":
        print(chapter_three_report(), end="")
    elif args.chapter == "chapter-4":
        print(chapter_four_report(), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
