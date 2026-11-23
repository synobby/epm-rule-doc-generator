/* RTPS: {Entity} {Scenario} */
// Recalculate the selected entity and push results to reporting
def entity = rtps.Entity.member.name
def scenario = rtps.Scenario.member.name

if (!entity) {
    throwVetoException("Please select an entity.")
}

operation.grid.dataCellIterator().each { cell ->
    println(cell.getMemberName("Account"))
}

String calc = """
FIX ("$scenario", "Working", "$entity")
    CALC DIM ("Account");
    AGG ("Product");
ENDFIX
"""
return calc
