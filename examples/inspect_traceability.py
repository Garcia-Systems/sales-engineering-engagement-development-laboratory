"""Set a debugger breakpoint and inspect the hypothesis's evidence_ids."""

from engagement_dev.scenarios import chapter_zero_report, load_chapter_zero


if __name__ == "__main__":
    data = load_chapter_zero()
    print(f"Loaded {len(data.accounts)} accounts")
    print(chapter_zero_report())
