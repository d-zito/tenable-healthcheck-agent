# HTML Report Formatting Changes

## Summary
Refactored the HTML report generation to:
1. Add `--skip-ai` flag for testing HTML formatting without using tokens
2. Apply consistent Tenable black (#1E2426) and yellow (#E7FF00) branding throughout
3. Condense layout to reduce vertical space and improve readability

## Changes Made

### 1. Modified: `src/generate_report.py`
**New Feature**: `--skip-ai` flag for testing

**How it works**:
- **Normal mode** (default, no flag): 
  - **ALWAYS runs fresh AI analysis** with Claude
  - Uses current AI model and latest insights
  - Caches analysis to JSON file as a side effect
  - **Costs tokens every time**
  
- **Test mode** (`--skip-ai` flag):
  - Skips AI processing entirely (**no tokens used**)
  - Uses cached AI analysis from JSON if available
  - Shows warning if no cached analysis found
  - **Perfect for iterating on HTML/CSS formatting**

**The Philosophy**:
- Production reports should always have fresh AI analysis
- Test mode is for rapid HTML formatting iterations only
- Cached analysis is a convenience for testing, not the primary use case

### 2. Redesigned: `src/reporters/html_reporter.py`
**Color Scheme** (Tenable Official Colors):
- Primary Black: `#1E2426`
- Primary Yellow: `#E7FF00`
- Success Green: `#00c853` (only for success states)
- Danger Red: `#ff1744` (only for critical issues)
- Neutral Gray: `#666` or `#fafafa` for backgrounds

**Layout Improvements**:
- **Reduced padding**: 25px → 15-20px throughout
- **Smaller fonts**: 14px base (was 16px), headers 16px (was 20px)
- **Condensed stat cards**: 140px min-width (was 200px), tighter spacing
- **Compact tables**: 8px padding (was 12px), smaller fonts (13px → 11px headers)
- **Tighter sections**: 25px margins (was 40px between sections)
- **Smaller badges**: 10px font (was 12px), less padding
- **Chart improvements**: 250px height (was 300px), cleaner styling

**Visual Improvements**:
- Header now has gradient background with yellow bottom border
- All chart colors use Tenable black/yellow palette
- Chart points highlighted with yellow (#E7FF00)
- Status cards use proper Tenable colors for borders
- Tables have black headers with white text
- Zebra striping on table rows for better readability

## Before vs After

### Color Usage
**Before** (Inconsistent):
- Purple/blue: `#667eea`, `#764ba2` ❌
- Bootstrap colors: `#28a745` (green), `#ffa500` (orange), `#dc3545` (red) ❌
- Tenable colors: Used in some places ⚠️

**After** (Consistent):
- Tenable Black: `#1E2426` ✓
- Tenable Yellow: `#E7FF00` ✓
- Semantic colors only for states: green (success), red (critical) ✓

### Space Usage
**Before**:
- Large cards with lots of whitespace
- Wide tables with heavy padding
- Vertical scrolling required for most reports

**After**:
- Compact cards with efficient spacing
- Denser tables without sacrificing readability
- More content visible without scrolling
- Grid layouts adjusted for smaller min-widths

## Usage

### Normal Report Generation (with fresh AI analysis)
```bash
source venv/bin/activate

# Generate report from latest run - RUNS FRESH AI ANALYSIS (uses tokens)
python3 src/generate_report.py

# Generate from specific date - RUNS FRESH AI ANALYSIS (uses tokens)
python3 src/generate_report.py --date 20260529_202034

# Custom output file - RUNS FRESH AI ANALYSIS (uses tokens)
python3 src/generate_report.py --output reports/my_report.html
```
**Token Usage**: Every normal report generation runs fresh AI analysis

### Test Mode (for HTML formatting iterations - NO tokens used)
```bash
source venv/bin/activate

# Generate one report WITH AI first (to cache the analysis)
python3 src/generate_report.py --output reports/baseline.html

# Now iterate on HTML formatting using --skip-ai
python3 src/generate_report.py --skip-ai --output reports/test.html

# Repeat the test command as many times as needed:
# 1. Edit src/reporters/html_reporter.py
# 2. Run: python3 src/generate_report.py --skip-ai --output reports/test.html
# 3. Open and review: open reports/test.html
# 4. Repeat steps 1-3 until satisfied!
```

**Important**: `--skip-ai` requires cached AI analysis. Run without the flag once first.

## AI Analysis Behavior

**Normal Mode (Default)**:
- **ALWAYS runs fresh AI analysis** 
- Gets latest insights from Claude
- Reflects current AI model capabilities
- Caches result to JSON as a side effect
- **Cost**: Tokens used every time

**Test Mode (`--skip-ai`)**:
- Uses cached analysis from JSON
- No tokens used
- Fast report generation
- **Purpose**: Rapid HTML/CSS iteration only

**Caching Purpose**:
- The cache is a convenience for testing mode
- Not meant to save tokens in production
- Fresh analysis ensures best results for real reports

## File Locations

- **Modified**: `src/generate_report.py` (added --skip-ai flag and caching)
- **Redesigned**: `src/reporters/html_reporter.py` (new colors & layout)
- **This doc**: `FORMATTING_CHANGES.md`
