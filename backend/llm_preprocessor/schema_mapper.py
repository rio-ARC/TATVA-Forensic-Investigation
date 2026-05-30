"""
llm_preprocessor/schema_mapper.py
===================================
Takes a raw pandas DataFrame + the column_mapping dict from SchemaAnalyzer,
and returns a new DataFrame with canonical column names.

Also applies schema defaults for optional columns that are absent.

This is a pure data transformation step — no LLM, no IO.
"""

import pandas as pd
from .canonical_schemas import CANONICAL_SCHEMAS


def apply_mapping(df_raw: pd.DataFrame, dataset_type: str, column_mapping: dict) -> pd.DataFrame:
    """
    Renames raw columns to canonical names and fills missing optional columns
    with their schema-defined defaults.

    Args:
        df_raw:         Raw DataFrame from the uploaded file.
        dataset_type:   One of the keys in CANONICAL_SCHEMAS (e.g. "CDR").
        column_mapping: Dict of {canonical_col: raw_col} from SchemaAnalyzer.

    Returns:
        A new DataFrame with canonical column names.

    Raises:
        ValueError: If a required canonical column has no mapping and no raw column to fall back to.
    """
    if dataset_type not in CANONICAL_SCHEMAS:
        raise ValueError(
            f"[SchemaMapper] No canonical schema for dataset type '{dataset_type}'. "
            f"Supported: {list(CANONICAL_SCHEMAS.keys())}"
        )

    schema = CANONICAL_SCHEMAS[dataset_type]
    required_cols = schema["required"]
    optional_cols = schema.get("optional", [])
    defaults = schema.get("defaults", {})

    df_out = pd.DataFrame()

    # ── Required columns ──────────────────────────────────
    for canonical_col in required_cols:
        raw_col = column_mapping.get(canonical_col)

        if raw_col and raw_col in df_raw.columns:
            df_out[canonical_col] = df_raw[raw_col].values
        elif canonical_col in df_raw.columns:
            # The raw file already uses the canonical name
            df_out[canonical_col] = df_raw[canonical_col].values
        else:
            raise ValueError(
                f"[SchemaMapper] Required column '{canonical_col}' could not be mapped "
                f"for dataset type '{dataset_type}'. "
                f"column_mapping={column_mapping}, raw_columns={list(df_raw.columns)}"
            )

    # ── Optional columns ──────────────────────────────────
    for canonical_col in optional_cols:
        raw_col = column_mapping.get(canonical_col)

        if raw_col and raw_col in df_raw.columns:
            df_out[canonical_col] = df_raw[raw_col].values
        elif canonical_col in df_raw.columns:
            df_out[canonical_col] = df_raw[canonical_col].values
        else:
            # Apply default value
            df_out[canonical_col] = defaults.get(canonical_col)

    return df_out
