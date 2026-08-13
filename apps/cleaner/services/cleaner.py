"""
DataFrame cleaning logic for DataPilot.

Given a raw pandas DataFrame from an uploaded CSV, produces a cleaned
DataFrame plus a statistics dict describing what changed.
"""

from __future__ import annotations

import pandas as pd

# Common ways "missing" shows up in real-world CSVs, beyond pandas' own
# NaN detection. Normalized to pd.NA before any counting happens so
# every downstream step sees a consistent representation.
MISSING_VALUE_MARKERS = [
    "", " ", "n/a", "N/A", "na", "NA", "null", "NULL", "none", "None", "-",
]

DEFAULT_TEXT_FILL_VALUE = "Unknown"


def clean_dataframe(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """
    Clean a raw DataFrame: standardize columns, normalize and count missing
    values, drop empty/duplicate rows, trim text, then fill remaining gaps.

    Args:
        df: The raw DataFrame as read from the uploaded CSV.

    Returns:
        (cleaned_df, statistics) — the cleaned DataFrame and a dict of
        counts describing what was found and changed.
    """
    original_rows = len(df)
    original_columns = len(df.columns)

    cleaned_df = df.copy()
    cleaned_df = _standardize_column_names(cleaned_df)
    cleaned_df = _normalize_missing_markers(cleaned_df)

    cleaned_df, empty_rows_removed = _drop_empty_rows(cleaned_df)
    cleaned_df, duplicate_rows = _drop_duplicate_rows(cleaned_df)
    cleaned_df = _strip_text_columns(cleaned_df)

    missing_values = int(cleaned_df.isna().sum().sum())
    cleaned_df = _fill_missing_values(cleaned_df)

    final_rows = len(cleaned_df)

    statistics = {
        "original_rows": original_rows,
        "final_rows": final_rows,
        "original_columns": original_columns,
        "final_columns": len(cleaned_df.columns),
        "missing_values": missing_values,
        "duplicates_removed": duplicate_rows,
        "empty_rows_removed": empty_rows_removed,
        "rows_removed": original_rows - final_rows,
    }

    return cleaned_df, statistics


def _standardize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """Lowercase, trim, and snake_case every column header."""
    df.columns = (
        df.columns.astype(str)
        .str.strip()
        .str.lower()
        .str.replace(" ", "_", regex=False)
    )
    return df


def _normalize_missing_markers(df: pd.DataFrame) -> pd.DataFrame:
    """Convert common "empty" text markers (n/a, null, -, etc.) into pd.NA."""
    return df.replace(MISSING_VALUE_MARKERS, pd.NA)


def _drop_empty_rows(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Remove rows that are entirely missing values. Returns (df, count_removed)."""
    before = len(df)
    df = df.dropna(how="all")
    return df, before - len(df)


def _drop_duplicate_rows(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Remove exact duplicate rows. Returns (df, count_of_duplicates_found)."""
    duplicate_count = int(df.duplicated().sum())
    return df.drop_duplicates(), duplicate_count


def _strip_text_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Trim leading/trailing whitespace on every text column."""
    text_columns = df.select_dtypes(include=["object", "string"]).columns
    for column in text_columns:
        df[column] = df[column].astype("string").str.strip()
    return df


def _fill_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """
    Fill remaining gaps: numeric columns get their median, text columns
    get a placeholder value. Must run after missing-value counting, since
    it removes the very gaps that statistic reports on.
    """
    for column in df.columns:
        if pd.api.types.is_numeric_dtype(df[column]):
            if df[column].isna().any():
                median = df[column].median()
                if pd.notna(median):
                    df[column] = df[column].fillna(median)
        else:
            df[column] = df[column].fillna(DEFAULT_TEXT_FILL_VALUE)
    return df