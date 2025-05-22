# 📝 Feedback Metrics Automation – Legal Aid Society (v2.2.3)

A Python-based automation system for transforming raw LMS course feedback into clean, summarized reports — no pivot tables required. Developed for repeatable, low-touch reporting at the Legal Aid Society.

---

## ✅ What It Does

1. **Ingests Raw Feedback**
   - Accepts `.xls` exports from viDesktop
   - Converts text ratings (e.g. Excellent, Good) into a numeric 4-point scale
   - Extracts open-ended comment responses
   - Removes exact and partial duplicates

2. **Processes Cleaned Data**
   - Cleans malformed headers (e.g., `_x000D_`)
   - Dynamically detects key columns
   - Validates all responses use the 4-point scale
   - Computes summary metrics per question

3. **Exports Results**
   - Outputs Excel + CSV reports to `/Feedback_Summary`
   - Auto-adjusts Excel columns
   - Generates logs for each run

---

## 📁 Folder Structure

```
2025 Organized Testimony/
├── raw_evals/                    ← Drop raw .xls files here  
├── processed_reports/            ← Cleaned .xlsx output files  
├── Feedback_Summary/             ← Summary metrics + comments  
├── logs/                         ← Execution logs  
├── feedback_ingestion.py         ← Preprocesses and deduplicates feedback  
├── feedback_metrics.py           ← Analyzes and summarizes data  
├── Organized_requirementsutils.py ← Shared helper functions (e.g., file cleanup)  
```

---

## 🚀 How to Use

### STEP 1: Clean Raw Files
```bash
python feedback_ingestion.py
```
- Converts `.xls` → `.xlsx`
- Maps text ratings to numbers (1–4)
- Removes duplicate responses
- Extracts comments

### STEP 2: Generate Feedback Report
```bash
python feedback_metrics.py
```
- Summarizes ratings per question
- Outputs:
  - `Feedback_Summary_<timestamp>.xlsx`
  - `Feedback_Summary_<timestamp>.csv`

---

## 🧼 Cleanup Prompt

Before analysis, you'll be prompted to clean out `/Feedback_Summary` files:

- `y` – delete all matching files  
- `n` – skip deletion and continue  
- `dry-run` – show what would be deleted  
- `p` – preview all files

---

## 📊 Summary Output – Column Definitions

| Column         | Description |
|----------------|-------------|
| `event`        | Name of the training or session (from file name or metadata) |
| `question`     | The feedback item being rated |
| `average`      | Mean rating across all valid responses |
| `median`       | Middle value of response scores |
| `std_dev`      | Standard deviation – how spread out the responses are. A higher number means more variation. |
| `min`          | The lowest response score received. |
| `max`          | The highest response score received. |
| `count`        | Total number of responses collected for that question. |
| `positive_pct` | Percentage of responses that were rated 4 or higher on the scale (e.g., “Good” or “Excellent”). |

---

## 🧪 Version Info

- **Current Version**: `v2.2.3`
- **Rating Scale**: 4-point (Excellent = 4, Good = 3, Fair = 2, Poor = 1)
- **Maintainer**: Geno Moore, Legal Aid Society

---

## 📌 Notes

- Make sure `feedback_ingestion.py` is run before generating summaries
- All column names are cleaned and normalized
- Safe deduplication logic prevents inflated metrics
