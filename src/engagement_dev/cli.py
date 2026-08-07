"""Command-line entry point for executable chapters."""

import argparse

from engagement_dev.scenarios import chapter_eight_report, chapter_five_report, chapter_four_report, chapter_nine_report, chapter_one_report, chapter_seven_report, chapter_six_report, chapter_ten_report, chapter_three_report, chapter_two_report, chapter_zero_report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="engagement-dev")
    parser.add_argument("chapter", choices=tuple(f"chapter-{number}" for number in range(11)), help="chapter scenario to run")
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
    elif args.chapter == "chapter-5":
        print(chapter_five_report(), end="")
    elif args.chapter == "chapter-6":
        print(chapter_six_report(), end="")
    elif args.chapter == "chapter-7":
        print(chapter_seven_report(), end="")
    elif args.chapter == "chapter-8":
        print(chapter_eight_report(), end="")
    elif args.chapter == "chapter-9":
        print(chapter_nine_report(), end="")
    elif args.chapter == "chapter-10":
        print(chapter_ten_report(), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
