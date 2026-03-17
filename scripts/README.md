# Pipeline Scripts

Scripts for orchestrating the medallion architecture pipeline.

## Quick Start

```bash
# Run the entire pipeline from scratch
python scripts/run_all.py

# Validate data integrity across all layers
python scripts/validate.py

# Reset to clean slate (removes all generated files)
python scripts/reset.py
```

## Scripts

### run_all.py - Pipeline Orchestration

Executes the full medallion architecture pipeline in sequence:
1. **Raw** - Generate source data files
2. **Bronze** - Load raw data with audit columns
3. **Silver** - Clean, validate, deduplicate
4. **Gold** - Build dimensional model
5. **Serving** - Create analytics views

```bash
# Run entire pipeline
python scripts/run_all.py

# Start from a specific layer
python scripts/run_all.py --from silver

# Stop at a specific layer
python scripts/run_all.py --to gold

# Run just a range
python scripts/run_all.py --from bronze --to silver
```

### validate.py - Cross-Layer Validation

Verifies data integrity across all pipeline layers:
- Database existence and size
- Row count reconciliation (bronze → silver → gold)
- Foreign key integrity in gold layer
- Aggregate table consistency
- Date dimension coverage
- Serving view existence

```bash
# Run all validations
python scripts/validate.py

# Verbose output
python scripts/validate.py --verbose
```

**Sample Output:**
```
CROSS-LAYER VALIDATION
============================================================
  PASS: Bronze database exists (18.18 MB)
  PASS: Silver database exists (31.43 MB)
  PASS: Gold database exists (21.61 MB)
  PASS: No duplicates in silver.streams
  PASS: Stream counts match (99,493)
  PASS: All FK integrity checks passed
  PASS: All aggregates reconcile
  PASS: All 15 serving views exist

VALIDATION SUMMARY
  Passed:   17
  Failed:   0
  Warnings: 0

ALL VALIDATIONS PASSED
```

### reset.py - Clean Slate Reset

Removes all generated files to start fresh:
- Database files (bronze.db, silver.db, gold.db)
- Raw data files (01_raw/data/)
- Serving reports (05_serving/reports/)

```bash
# Preview what would be deleted
python scripts/reset.py --dry-run

# Reset with confirmation prompt
python scripts/reset.py

# Reset without confirmation
python scripts/reset.py --force
```

### utils.py - Shared Utilities

Common functions used by all scripts:
- Database connection management
- SQL file execution
- Row counting and statistics
- Path configuration
- Logging setup

## Typical Workflows

### First-Time Setup
```bash
python scripts/run_all.py
python scripts/validate.py
```

### Re-run After Code Changes
```bash
python scripts/reset.py --force
python scripts/run_all.py
python scripts/validate.py
```

### Debug a Specific Layer
```bash
# Reset and run up to silver
python scripts/reset.py --force
python scripts/run_all.py --to silver

# Check silver data manually, then continue
python scripts/run_all.py --from gold
```

### Quick Validation Check
```bash
python scripts/validate.py
```

## Exit Codes

| Script | Code | Meaning |
|--------|------|---------|
| run_all.py | 0 | Pipeline completed successfully |
| run_all.py | 1 | Pipeline failed at some layer |
| validate.py | 0 | All validations passed |
| validate.py | 1 | One or more validations failed |
| reset.py | 0 | Reset completed (or cancelled) |

## Project Paths

The scripts use relative paths from the project root:

```
data_modeling/
├── scripts/          # This directory
│   ├── run_all.py
│   ├── validate.py
│   ├── reset.py
│   └── utils.py
├── 01_raw/           # Raw data generation
├── 02_bronze/        # Bronze layer + bronze.db
├── 03_silver/        # Silver layer + silver.db
├── 04_gold/          # Gold layer + gold.db
└── 05_serving/       # Serving layer (views in gold.db)
```

## Troubleshooting

### "Module not found" errors
Run scripts from the project root:
```bash
cd data_modeling
python scripts/run_all.py
```

### "Database not found" errors
Run the pipeline first:
```bash
python scripts/run_all.py
```

### Validation failures
Check the specific failure message and investigate the relevant layer. Common issues:
- Missing raw data files → Run raw layer
- FK violations → Check silver transformation logic
- Aggregate mismatches → Check aggregate load SQL
