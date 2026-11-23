from core.masker import mask_members, unmask


def test_mask_round_trip():
    text = 'FIX ("Net Income", "Income", "Actual")\n"Net Income" = "Income" * 2;\nENDFIX'
    result = mask_members(text, ["Net Income", "Income", "Actual"])
    for name in ("Net Income", "Income", "Actual"):
        assert name not in result.text
    assert unmask(result.text, result.mapping) == text


def test_extra_unquoted_names_are_masked():
    result = mask_members("Entity E100 is loaded", [], ["E100"])
    assert "E100" not in result.text
    assert unmask(result.text, result.mapping) == "Entity E100 is loaded"


def test_unmask_nested_structures():
    mapping = {"MBR_001": "Actual"}
    data = {"a": ["MBR_001", {"b": "uses MBR_001"}], "n": 3}
    assert unmask(data, mapping) == {"a": ["Actual", {"b": "uses Actual"}], "n": 3}
