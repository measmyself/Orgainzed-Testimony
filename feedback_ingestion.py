print("🚀 feedback_ingestion started!")
print("📂 Checking feedback_ingestion input files...")

# ========================
#    SYSTEM CONFIGURATION
# ========================
from pathlib import Path
import pandas as pd
from Organized_requirementsutils import safe_clean_directory

# Automatically detect script location & set paths
SCRIPT_DIR = Path(__file__).parent
BASE_DIR = Path(r"C:\Users\gmoore\OneDrive - The Legal Aid Society\PlanningDocs - L and D Internal Team\Rep0rting\Course Feedback Rep0rting\2025 Orgainzed Testimony")

DATA_DIR = BASE_DIR / "raw_evals"
PROCESSED_DIR = BASE_DIR / "processed_reports"
SUMMARY_DIR = BASE_DIR / "Feedback_Summary"

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
SUMMARY_DIR.mkdir(parents=True, exist_ok=True)

RATING_MAP = {
    "Excellent": 4,
    "Good": 3,
    "Fair": 2,
    "Poor": 1
}

# ========================
#    DEDUPLICATION LOGIC
# ========================
def handle_duplicates(df):
    """Clean and deduplicate dataframe with comprehensive checks"""
    # Clean column names from Excel line break artifacts
    df.columns = [col.split('_x000D_')[0].strip() for col in df.columns]

    initial_rows = len(df)
    df = df.drop_duplicates()
    exact_dups = initial_rows - len(df)

    # Determine available columns for partial duplicate detection
    key_candidates = ['user name', 'event name', 'question']
    key_columns = [col for col in df.columns if col.strip().lower() in key_candidates]

    if 'response' in df.columns and key_columns:
        pre_partial = len(df)
        df = df.sort_values('response', ascending=False)\
               .drop_duplicates(subset=key_columns, keep='first')
        partial_dups = pre_partial - len(df)
        print(f"🧹 Removed duplicates: {exact_dups} exact, {partial_dups} partial")
    else:
        print(f"🧹 Removed duplicates: {exact_dups} exact")

    return df

# ========================
#    INGESTION PROCESS
# ========================
for file in DATA_DIR.glob("*.xls"):
    df = pd.read_excel(file, dtype=str)

    # Convert ratings to numerical values
    df = df.apply(lambda col: col.map(RATING_MAP) if col.name.strip().lower() == 'response' else col)

    # Handle duplicates
    df = handle_duplicates(df)

    # Save cleaned data
    cleaned_path = PROCESSED_DIR / file.name.replace(".xls", "_cleaned.xlsx")
    df.to_excel(cleaned_path, index=False)
    print(f"✅ Cleaned data saved: {cleaned_path.name}")

    # Extract and save comments
    comment_cols = [col for col in df.columns if 'comment' in col.lower() or 'apply' in col.lower()]
    if comment_cols:
        comments = df[comment_cols].dropna(how='all')
        comments = comments[comments.apply(lambda row: row.astype(str).str.len().max() > 5, axis=1)]
        if not comments.empty:
            comment_path = SUMMARY_DIR / f"comments_only_{file.stem}.xlsx"
            comments.to_excel(comment_path, index=False)
            print(f"📝 Comments saved: {comment_path.name}")

print("✅ feedback_ingestion completed successfully!")
