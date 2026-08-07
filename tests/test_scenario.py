from engagement_dev.scenarios import chapter_zero_report, load_chapter_zero


def test_scenario_output_is_deterministic():
    assert chapter_zero_report() == chapter_zero_report()
    assert "ACCOUNT: Harbor Street Music" in chapter_zero_report()
    assert "ACCOUNT: Blue Heron Hospitality" in chapter_zero_report()
    assert "NO_SUPPORTED_HYPOTHESIS" in chapter_zero_report()


def test_market_contains_accounts_that_do_not_become_opportunities():
    data = load_chapter_zero()
    assert len(data.accounts) == 5
    assert chapter_zero_report().count("HYPOTHESIS_SUPPORTED") == 2
