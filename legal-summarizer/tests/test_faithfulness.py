from backend.services.faithfulness import faithfulness_report

SRC = "The Provider shall pay USD 240,000 by 15 January 2026 to Ardent Logistics Limited."


def test_faithful_summary_has_no_flags():
    r = faithfulness_report(SRC, "Ardent Logistics must pay USD 240,000 by January 15, 2026.")
    assert not r["unsupported_numbers"] and not r["unsupported_dates"] and not r["unsupported_terms"]


def test_altered_amount_date_and_new_party_are_flagged():
    r = faithfulness_report(SRC, "Ardent Logistics must pay USD 250,000 by 16 January 2026 to Zenith Corp.")
    assert "250000" in r["unsupported_numbers"]
    assert "2026-01-16" in r["unsupported_dates"]
    assert "Zenith" in r["unsupported_terms"]
