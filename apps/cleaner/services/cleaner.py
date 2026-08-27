"""
Core DataFrame cleaning engine for DataPilot.
"""

from __future__ import annotations

import pandas as pd


MISSING_VALUE_MARKERS = [
    "", " ", "n/a", "N/A", "na", "NA",
    "null", "NULL", "none", "None", "-",
]

DEFAULT_TEXT_FILL_VALUE = "Unknown"


def clean_dataframe(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, dict]:
    """
    Clean a DataFrame and return the cleaned DataFrame plus
    structured cleaning statistics.
    """

    original_rows = len(df)
    original_columns = len(df.columns)

    cleaned_df = df.copy()

    cleaned_df = _standardize_column_names(cleaned_df)
    cleaned_df = _normalize_missing_markers(cleaned_df)

    missing_before = _count_missing_values(cleaned_df)

    cleaned_df, empty_rows_removed = _drop_empty_rows(
        cleaned_df
    )

    cleaned_df, duplicate_rows = _drop_duplicate_rows(
        cleaned_df
    )

    cleaned_df = _strip_text_columns(cleaned_df)

    missing_values = missing_before

    cleaned_df = _fill_missing_values(
        cleaned_df
    )

    final_rows = len(cleaned_df)

    findings = _build_findings(
        missing_before=missing_before,
        duplicate_rows=duplicate_rows,
        empty_rows_removed=empty_rows_removed,
        columns=df.columns,
    )

    statistics = {
        "original_rows": original_rows,
        "final_rows": final_rows,
        "original_columns": original_columns,
        "final_columns": len(cleaned_df.columns),
        "missing_values": missing_values,
        "duplicates_removed": duplicate_rows,
        "empty_rows_removed": empty_rows_removed,
        "rows_removed": original_rows - final_rows,
        "findings": findings,
    }

    return cleaned_df, statistics


def _standardize_column_names(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """Normalize column names into snake_case."""

    df.columns = (
        df.columns.astype(str)
        .str.strip()
        .str.lower()
        .str.replace(" ", "_", regex=False)
    )

    return df


def _normalize_missing_markers(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """Normalize common missing-value markers."""

    return df.replace(
        MISSING_VALUE_MARKERS,
        pd.NA,
    )


def _count_missing_values(
    df: pd.DataFrame,
) -> int:
    return int(
        df.isna().sum().sum()
    )


def _drop_empty_rows(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, int]:
    """Remove rows containing no useful data."""

    before = len(df)

    df = df.dropna(
        how="all"
    )

    return df, before - len(df)


def _drop_duplicate_rows(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, int]:
    """Remove exact duplicate rows."""

    duplicate_count = int(
        df.duplicated().sum()
    )

    return (
        df.drop_duplicates(),
        duplicate_count,
    )


def _strip_text_columns(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """Trim whitespace from text columns."""

    text_columns = df.select_dtypes(
        include=["object", "string"]
    ).columns

    for column in text_columns:
        df[column] = (
            df[column]
            .astype("string")
            .str.strip()
        )

    return df


def _fill_missing_values(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """Fill remaining missing values."""

    for column in df.columns:

        if pd.api.types.is_numeric_dtype(
            df[column]
        ):
            if df[column].isna().any():

                median = df[column].median()

                if pd.notna(median):
                    df[column] = (
                        df[column]
                        .fillna(median)
                    )

        else:
            df[column] = (
                df[column]
                .fillna(DEFAULT_TEXT_FILL_VALUE)
            )

    return df


def _build_findings(
    *,
    missing_before: int,
    duplicate_rows: int,
    empty_rows_removed: int,
    columns,
) -> list[dict]:
    """Build structured findings for persistence."""

    findings = []

    if missing_before:
        findings.append(
            {
                "finding_type": "missing",
                "column_name": "",
                "description": (
                    f"{missing_before:,} missing values "
                    "were detected."
                ),
                "fixed": True,
            }
        )

    if duplicate_rows:
        findings.append(
            {
                "finding_type": "duplicate",
                "column_name": "",
                "description": (
                    f"{duplicate_rows:,} duplicate rows "
                    "were removed."
                ),
                "fixed": True,
            }
        )

    if empty_rows_removed:
        findings.append(
            {
                "finding_type": "invalid",
                "column_name": "",
                "description": (
                    f"{empty_rows_removed:,} completely empty "
                    "rows were removed."
                ),
                "fixed": True,
            }
        )

    return findings
