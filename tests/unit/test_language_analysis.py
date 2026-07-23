from src.application.use_cases.language_analysis import bucket_language


def test_bucket_language_maps_unknown_to_other():
    assert bucket_language("unknown") == "other"
    assert bucket_language("gu") == "gu"
