import pytest

from core.detector import detect_rule_type
from core.validator import ValidationError, validate_rule_text

CALC_EXAMPLES = [
    'FIX ("Actual")\n"Sales" = "Units" * "Price";\nENDFIX',
    '"Sales"->"Jan" = 100;',  # cross-dim operator must NOT look like Groovy
    "SET UPDATECALC OFF;\nCALC ALL;",
    'DATACOPY "Actual" TO "Forecast";',
    'AGG ("Entity");',
]
GROOVY_EXAMPLES = [
    "def x = 1",
    "/* RTPS: {Entity} */\nreturn 'x'",
    "operation.grid.dataCellIterator()",
    "import java.text.DecimalFormat",
    "list.each { item -> println(item) }",
]


@pytest.mark.parametrize("text", CALC_EXAMPLES)
def test_detects_calc_script(text):
    assert detect_rule_type(text) == "calc_script"


@pytest.mark.parametrize("text", GROOVY_EXAMPLES)
def test_detects_groovy(text):
    assert detect_rule_type(text) == "groovy"


def test_empty_rejected():
    with pytest.raises(ValidationError):
        validate_rule_text("   \n  ")


def test_binary_rejected():
    with pytest.raises(ValidationError):
        validate_rule_text(b"abc\x00def")


def test_line_limits():
    ok = validate_rule_text("x\n" * 1000)
    assert ok.warnings == []
    warned = validate_rule_text("x\n" * 1001)
    assert warned.warnings
    with pytest.raises(ValidationError):
        validate_rule_text("x\n" * 2001)


def test_windows_line_endings_normalised():
    result = validate_rule_text(b"FIX\r\nENDFIX\r\n")
    assert "\r" not in result.text and result.line_count == 2
