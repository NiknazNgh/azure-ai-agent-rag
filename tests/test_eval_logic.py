from scripts.evaluate import contains_all, contains_none


def test_contains_all_is_case_insensitive():
    text = "The ENERGY increase was 12% and investigation is not mandatory."
    assert contains_all(text, ["energy", "12%", "not mandatory"])


def test_contains_none_rejects_forbidden_claim():
    text = "No cause was confirmed in the report."
    assert contains_none(text, ["pump failure caused"])
