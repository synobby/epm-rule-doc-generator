from core.parser_calc import parse_calc_script, strip_comments


def test_nested_fix_blocks_and_depth(sample):
    facts = parse_calc_script(sample("allocate_opex.csc"))
    assert len(facts.fix_blocks) == 2
    outer, inner = facts.fix_blocks
    assert outer.depth == 1 and inner.depth == 2
    assert outer.start_line == 6 and outer.end_line == 16
    assert inner.start_line == 7 and inner.end_line == 12
    assert '@RELATIVE("Total_BU", 0)' in inner.members


def test_members_rtps_functions_commands(sample):
    facts = parse_calc_script(sample("allocate_opex.csc"))
    assert "Corporate_OpEx" in facts.members
    assert "Headcount" in facts.members
    assert facts.runtime_prompts == ["{Scenario}", "{Version}", "&CurYear"]
    assert facts.functions == ["@RELATIVE"]
    assert "AGG" in facts.commands
    assert "SET UPDATECALC" in facts.commands and "SET AGGMISSG" in facts.commands


def test_cleardata_and_datacopy(sample):
    facts = parse_calc_script(sample("copy_actuals.csc"))
    assert {"CLEARDATA", "DATACOPY"} <= set(facts.commands)
    assert facts.fix_blocks[0].members.startswith('"FY26"')


def test_comments_are_ignored_but_lines_kept():
    text = '/* FIX ("Ignored") */\nFIX ("Real")\nENDFIX'
    cleaned = strip_comments(text)
    assert cleaned.count("\n") == text.count("\n")
    facts = parse_calc_script(text)
    assert len(facts.fix_blocks) == 1
    assert facts.fix_blocks[0].start_line == 2
    assert "Ignored" not in facts.members


def test_unbalanced_fix_produces_warning():
    facts = parse_calc_script('FIX ("A")\nFIX ("B")\nENDFIX')
    assert any("no matching ENDFIX" in w for w in facts.parse_warnings)
