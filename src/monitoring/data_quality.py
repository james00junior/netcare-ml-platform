"""Input-data quality checks that do not assume a live telemetry schema."""

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class DataQualityResult:
    """Result of validating an observed dataframe against an explicit contract."""

    missing_columns: tuple[str, ...]
    unexpected_columns: tuple[str, ...]
    null_counts: dict[str, int]

    @property
    def schema_valid(self) -> bool:
        return not self.missing_columns


def validate_required_columns(
    frame: pd.DataFrame,
    required_columns: list[str] | tuple[str, ...],
) -> DataQualityResult:
    """Validate only columns explicitly supplied by the caller.

    The function deliberately does not invent required fields, ranges, or null
    thresholds. Those values must come from the validated model contract or an
    approved monitoring configuration.
    """
    required = tuple(required_columns)
    observed = tuple(frame.columns)

    missing = tuple(column for column in required if column not in frame.columns)
    unexpected = tuple(column for column in observed if column not in required)
    null_counts = {
        column: int(frame[column].isna().sum()) for column in required if column in frame.columns
    }

    return DataQualityResult(
        missing_columns=missing,
        unexpected_columns=unexpected,
        null_counts=null_counts,
    )
