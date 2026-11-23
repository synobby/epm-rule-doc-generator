"""Input validation: empty/binary checks and line limits (spec FR-1)."""

from __future__ import annotations

import os
from dataclasses import dataclass, field

MAX_LINES = int(os.getenv("MAX_LINES", "2000"))
WARN_LINES = int(os.getenv("WARN_LINES", "1000"))


class ValidationError(ValueError):
    """Raised when the input cannot be processed."""


@dataclass
class ValidationResult:
    text: str
    line_count: int
    warnings: list[str] = field(default_factory=list)


def validate_rule_text(text: str | bytes) -> ValidationResult:
    """Check a rule before it is parsed or sent to the LLM.

    - bytes are decoded as UTF-8 (binary files are rejected)
    - empty input is rejected
    - more than MAX_LINES lines is rejected
    - more than WARN_LINES lines returns a warning
    """
    if isinstance(text, bytes):
        if b"\x00" in text:
            raise ValidationError("This looks like a binary file. Please upload a text file.")
        try:
            text = text.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValidationError("The file is not valid UTF-8 text.") from exc

    # Normalise Windows line endings so line numbers are consistent.
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    if not text.strip():
        raise ValidationError("The rule is empty. Paste a rule or upload a file.")

    line_count = len(text.rstrip("\n").split("\n"))
    if line_count > MAX_LINES:
        raise ValidationError(
            f"The rule has {line_count:,} lines. The maximum is {MAX_LINES:,}."
        )

    warnings: list[str] = []
    if line_count > WARN_LINES:
        warnings.append(
            f"This rule has {line_count:,} lines. Results may be slower and less precise "
            f"above {WARN_LINES:,} lines."
        )

    return ValidationResult(text=text, line_count=line_count, warnings=warnings)
