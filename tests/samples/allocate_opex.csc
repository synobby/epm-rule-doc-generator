/* Allocate corporate OpEx to business units based on headcount.
   Sample rule for testing - uses Vision-style member names, no client data. */
SET UPDATECALC OFF;
SET AGGMISSG ON;

FIX ({Scenario}, {Version}, &CurYear, @RELATIVE("YearTotal", 0))
    FIX (@RELATIVE("Total_BU", 0), "No Product")
        "Allocated_OpEx" (
            "Allocated_OpEx" = "Corporate_OpEx"->"BU_Corporate"->"No Product"
                * ("Headcount" / "Headcount"->"Total_BU");
        )
    ENDFIX

    // Roll up the allocated amounts
    AGG ("Entity", "Product");
ENDFIX
