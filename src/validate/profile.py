"""Profile the deliberately messy prices file and write a validation report."""

from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt

from src.validate import rules

ROOT = Path(__file__).resolve().parents[2]
RAW_PATH = ROOT / "data" / "raw" / "prices.csv"
REPORT_PATH = ROOT / "docs" / "validation_report.md"
PLOT_PATH = ROOT / "docs" / "price_histogram.png"

QUALITY_RULES = {
    "positive_price": (rules.rule_positive_price, "Reject rows with price <= 0"),
    "duplicate_ids": (rules.rule_duplicate_ids, "Reject repeated record identifiers"),
    "duplicate_rows": (rules.rule_duplicate_rows, "Reject exact duplicate rows"),
    "valid_date": (rules.rule_valid_date, "Reject rows with invalid dates"),
    "missing_market": (rules.rule_missing_market, "Impute the market with the mode"),
    "known_commodity": (rules.rule_known_commodity, "Normalize commodity spelling/case"),
}


def profile_dataframe(df: pd.DataFrame) -> dict:
    """Return profiling and rule-failure information without changing ``df``."""
    failures = {}
    for name, (rule, _action) in QUALITY_RULES.items():
        failures[name] = rule(df)

    numeric = df.select_dtypes(include="number")
    summary = numeric.agg(["mean", "median", "min", "max", "std"]).T
    id_column = "record_id" if "record_id" in df.columns else "id"
    category_values = sorted(df["commodity"].dropna().astype(str).str.strip().str.casefold().unique())

    return {
        "schema": {column: str(dtype) for column, dtype in df.dtypes.items()},
        "row_count": int(len(df)),
        "missing_values": {column: int(count) for column, count in df.isna().sum().items()},
        "exact_duplicate_count": int(df.duplicated().sum()),
        "duplicate_id_row_count": int(failures["duplicate_ids"].shape[0]),
        "duplicate_id_value_count": int(df.loc[df[id_column].duplicated(keep=False), id_column].nunique()),
        "category_values": category_values,
        "numeric_summary": summary,
        "failures": {name: int(result.shape[0]) for name, result in failures.items()},
        "failure_frames": failures,
    }


def write_validation_report(profile: dict, path: Path = REPORT_PATH) -> None:
    """Write a concise markdown report for the raw validation pass."""
    lines = [
        "# Validation Report",
        "",
        "## Raw-file profile",
        f"- Rows: {profile['row_count']}",
        f"- Exact duplicate rows: {profile['exact_duplicate_count']}",
        f"- Rows with duplicate IDs: {profile['duplicate_id_row_count']}",
        f"- Distinct duplicated ID values: {profile['duplicate_id_value_count']}",
        "",
        "### Inferred schema",
        "",
        "| Column | Inferred type | Missing values |",
        "|---|---|---:|",
    ]
    for column, dtype in profile["schema"].items():
        lines.append(f"| {column} | `{dtype}` | {profile['missing_values'][column]} |")

    lines.extend(["", "### Rule results and actions", "", "| Rule | Failed rows | Action |", "|---|---:|---|"])
    for name, (_rule, action) in QUALITY_RULES.items():
        lines.append(f"| `{name}` | {profile['failures'][name]} | {action} |")

    lines.extend([
        "",
        "### Inconsistent categories",
        "",
        "Normalized commodity groups found: " + ", ".join(profile["category_values"]) + ".",
        "",
        "### Numeric summary",
        "",
        "| Column | Mean | Median | Min | Max | Std |",
        "|---|---:|---:|---:|---:|---:|",
    ])
    for column, values in profile["numeric_summary"].iterrows():
        lines.append(
            f"| {column} | {values['mean']:.2f} | {values['median']:.2f} | "
            f"{values['min']:.2f} | {values['max']:.2f} | {values['std']:.2f} |"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_price_plot(df: pd.DataFrame, path: Path = PLOT_PATH) -> None:
    """Plot prices to support the decision to reject non-positive values."""
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(8, 4))
    plt.hist(df["price"].dropna(), bins=20, edgecolor="black")
    plt.axvline(0, color="red", linestyle="--", label="Rule boundary: price > 0")
    plt.xlabel("Price")
    plt.ylabel("Row count")
    plt.title("Raw price distribution")
    plt.legend()
    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close()


def run_profile(path: Path = RAW_PATH) -> dict:
    df = pd.read_csv(path)
    result = profile_dataframe(df)
    write_validation_report(result)
    write_price_plot(df)
    return result


if __name__ == "__main__":
    result = run_profile()
    print(f"Profiled {result['row_count']} rows from {RAW_PATH}")
    for name, count in result["failures"].items():
        print(f"{name}: {count}")
