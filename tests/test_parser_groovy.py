from core.parser_groovy import parse_groovy


def test_groovy_rtps_and_api_calls(sample):
    facts = parse_groovy(sample("recalc_entity.groovy"))
    assert facts.rule_type == "groovy"
    assert "{Entity}" in facts.runtime_prompts
    assert "rtps.Scenario" in facts.runtime_prompts
    assert "operation.grid" in facts.groovy_api_calls
    assert "throwVetoException" in facts.groovy_api_calls


def test_embedded_calc_script_is_parsed(sample):
    facts = parse_groovy(sample("recalc_entity.groovy"))
    assert len(facts.fix_blocks) == 1
    assert {"CALC DIM", "AGG"} <= set(facts.commands)
    assert "Working" in facts.members
