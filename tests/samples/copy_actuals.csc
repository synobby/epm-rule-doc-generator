/* Copy Actual to Forecast for closed months */
FIX ("FY26", "Working", @RELATIVE("Total_Entity", 0))
    CLEARDATA "Forecast"->"Jan":"Mar";
    DATACOPY "Actual" TO "Forecast";
ENDFIX
