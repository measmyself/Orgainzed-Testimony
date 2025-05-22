import logging
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime
import sys
import re
from Organized_requirementsutils import safe_clean_directory

# ========================
#      CONFIGURATION
# ========================
VERSION = "2.2.2"
SCRIPT_DIR = Path(__file__).parent
BASE_DIR = Path(r"C:\Users\gmoore\OneDrive - The Legal Aid Society\PlanningDocs - L and D Internal Team\Rep0rting\Course Feedback Rep0rting\2025 Orgainzed Testimony")

PROCESSED_DIR = BASE_DIR / "processed_reports"
SUMMARY_DIR = BASE_DIR / "Feedback_Summary"
LOG_DIR = BASE_DIR / "logs"
SUMMARY_DIR.mkdir(exist_ok=True)

# ========================
#      LOGGING SETUP
# ========================
def setup_logging():
    log_file = LOG_DIR / f"feedback_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    LOG_DIR.mkdir(exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)-8s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    logging.info(f"🚀 Starting feedback_metrics v{VERSION}")
    return log_file

# ========================
#      CORE FUNCTIONS
# ========================
def clean_column_name(col):
    """Enhanced column cleaning handling Excel artifacts"""
    col = str(col)
    col = re.sub(r'_x[0-9a-f]{4}_', '', col)  # Remove Excel artifacts
    col = re.sub(r'[\r\n\t]', ' ', col)       # Remove line breaks
    col = re.sub(r'[^\w\s]', ' ', col)        # Remove special chars
    col = re.sub(r'\s+', ' ', col).strip()    # Normalize spaces
    col = col.lower().replace(' ', '_')       # Convert to snake_case
    return re.sub(r'_+', '_', col).strip('_') # Clean underscores

def find_column(df, possible_names):
    """Smart column detection with multiple fallbacks"""
    if not isinstance(df, pd.DataFrame) or df.empty:
        return None
        
    col_map = {col.lower(): col for col in df.columns}  # Case-insensitive lookup
    
    for name in possible_names:
        # Check all possible variants
        variants = [
            name.lower(),                      # Original name
            clean_column_name(name).lower(),   # Cleaned version
            (name + '_x000d_x000d_x000d').lower()  # Excel format
        ]
        for variant in variants:
            if variant in col_map:
                return col_map[variant]  # Return original column name
    return None

def validate_response_scores(df):
    """Validate score ranges with detailed logging"""
    if not isinstance(df, pd.DataFrame) or df.empty or 'response' not in df.columns:
        return False
        
    scores = pd.to_numeric(df['response'], errors='coerce').dropna()
    if scores.empty:
        return False
    
    min_score, max_score = scores.min(), scores.max()
    
    if min_score < 1:
        logging.warning(f"Invalid score <1: {min_score}")
        return False
        
    if max_score not in {5, 10}:
        logging.warning(f"Unexpected max score: {max_score} (expected 5 or 10)")
        return False
        
    return True

# ========================
#   FILE PROCESS FUNCTION
# ========================
def process_feedback_file(file, file_count, total_files):
    """Process feedback file with robust error handling"""
    file_start = datetime.now()
    logging.info(f"\n{'='*50}")
    logging.info(f"📂 Processing {file_count}/{total_files}: {file.name}")
    
    try:
        # 1. Read with engine fallback
        try:
            df = pd.read_excel(file, engine='openpyxl')
        except Exception as e:
            logging.warning(f"⚠️ Retrying with xlrd: {str(e)}")
            df = pd.read_excel(file, engine='xlrd')

        # 2. Validate DataFrame
        if not isinstance(df, pd.DataFrame) or df.empty:
            logging.error("❌ Invalid or empty DataFrame")
            return None

        # 3. Clean and log column names
        orig_cols = df.columns.tolist()
        df.columns = [clean_column_name(col) for col in df.columns]
        
        if logging.getLogger().isEnabledFor(logging.DEBUG):
            logging.debug("🔍 Column name mapping:")
            for orig, new in zip(orig_cols, df.columns):
                if orig != new:
                    logging.debug(f"  {orig!r} → {new!r}")

        # 4. Find key columns
        question_col = find_column(df, ['question', 'survey_item', 'prompt'])
        response_col = find_column(df, ['response', 'rating', 'score'])
        
        if not question_col or not response_col:
            missing = []
            if not question_col: missing.append("question")
            if not response_col: missing.append("response")
            missing = [k for k, v in {'question': question_col, 'response': response_col}.items() if not v]
            logging.error(f"""
            ❌ Required columns missing: {', '.join(missing)}
            Available columns in file:
            {df.columns.tolist()}
            """.strip())
            return None

        # 5. Prepare data
        df['response'] = pd.to_numeric(df[response_col], errors='coerce')
        
        if not validate_response_scores(df):
            return None

        # 6. Analyze
        event_col = find_column(df, ['event', 'course', 'training'])
        df['event'] = df[event_col] if event_col else file.stem.replace('_cleaned', '')
        
        grouped = (
            df.dropna(subset=['response'])
            .groupby(['event', question_col])
            .agg(
                average=('response', 'mean'),
                median=('response', 'median'),
                std_dev=('response', 'std'),
                min=('response', 'min'),
                max=('response', 'max'),
                count=('response', 'count'),
                positive_pct=('response', lambda x: (x >= 4).mean() * 100)
            )
            .rename(columns={question_col: 'question'})
            .reset_index()
        )
        
        logging.info(f"✅ Processed {len(grouped)} questions in {(datetime.now()-file_start).total_seconds():.1f}s")
        return grouped

    except Exception as e:
        logging.error(f"💥 Processing failed: {str(e)}", exc_info=True)
        return None

# ========================
#         MAIN FLOW
# ========================
def main():
    log_file = setup_logging()
    start_time = datetime.now()
    
    print("\n" + "="*50)
    print("FEEDBACK METRICS PROCESSING")
    print("="*50 + "\n")

    try:
        # 1. Check for files
        files = list(PROCESSED_DIR.glob("*_cleaned.xlsx"))
        if not files:
            print(f"""
            ❌ ERROR: No processed files found!
            Location: {PROCESSED_DIR}
            Expected files matching: *_cleaned.xlsx
            
            Required steps:
            1. Run feedback_ingestion.py first
            2. Verify files exist in the folder above
            """.strip())
            sys.exit(1)

        # 2. Process files
        print(f"🔄 Processing {len(files)} feedback files...")

        # Optional: Prompt user to clean up old summary files
        from Organized_requirementsutils import safe_clean_directory
        safe_clean_directory(SUMMARY_DIR, "*.xlsx")

        results = []
        for i, file in enumerate(files, 1):
            print(f"  {i}/{len(files)}: {file.name[:30]}...")
            result = process_feedback_file(file, i, len(files))
            if result is not None:
                results.append(result)

        if not results:
            print("❌ ERROR: All files failed processing (see log)")
            sys.exit(1)

        # 3. Generate outputs
        final_df = pd.concat(results, ignore_index=True)
        final_df.columns = [
            'event', 'question', 'average', 'median', 'std_dev',
            'min', 'max', 'count', 'positive_pct'
        ]
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_path = SUMMARY_DIR / f"Feedback_Summary_{timestamp}.xlsx"
        
        with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
            final_df.to_excel(writer, index=False)
            worksheet = writer.sheets['Sheet1']
            for i, col in enumerate(final_df.columns):
                worksheet.set_column(i, i, max(
                    final_df[col].astype(str).str.len().max(),
                    len(str(col))
                ) + 2)

        final_df.to_csv(output_path.with_suffix('.csv'), index=False)

        # 4. Completion
        duration = datetime.now() - start_time
        print(f"""
        ✅ SUCCESS! Created:
        - {output_path.name}
        - {output_path.stem}.csv
        
        Log: {log_file}
        Time: {duration.total_seconds():.1f} seconds
        """.strip())

    except Exception as e:
        print(f"💥 CRITICAL ERROR: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()