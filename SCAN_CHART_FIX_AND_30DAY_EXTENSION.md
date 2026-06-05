# Scan Chart Fix and 30-Day Extension

## Summary
Fixed the "Scan Health Over Time" chart to display data correctly, and extended all scan tracking from 7 days to 30 days for better trend visibility.

## Issues Fixed

### Issue 1: Scan Chart Had No Data
**Problem:** The scan health chart was always showing zero values even though scan data was being collected.

**Root Cause:** The `trends_manager.py` was looking for `problem_scans` and `completed_scans` as arrays in the data structure, but the actual scan data uses a different structure with `scan_summary` containing individual scan statistics.

**Fix:** Modified `trends_manager.py` to calculate scan totals from `scan_summary`:
```python
# Old (incorrect):
'problem_scans': len(scans.get('problem_scans', [])),
'completed_scans': len(scans.get('completed_scans', []))

# New (correct):
scan_summary = scans.get('scan_summary', {})
total_completed = sum(s.get('completed_runs', 0) for s in scan_summary.values())
total_failed = sum(s.get('failed_runs', 0) for s in scan_summary.values())
```

### Issue 2: Extend Scan Tracking to 30 Days
**Request:** Change scan health tracking from 7 days to 30 days for better trend analysis.

**Changes Made:**
1. `src/main.py`: Changed `scan_collector.collect(days_back=7)` → `days_back=30`
2. `src/reporters/console_reporter.py`: Made header dynamic to show actual days
3. `src/reporters/html_reporter.py`: Already dynamic, automatically shows 30 days

## Files Modified

### 1. `src/storage/trends_manager.py`
**Lines 66-73** - Fixed scan metric extraction:
```python
# Extract scan metrics
scans = current_data.get('scans', {})
scan_summary = scans.get('scan_summary', {})

# Calculate totals from scan_summary
total_completed = sum(s.get('completed_runs', 0) for s in scan_summary.values())
total_failed = sum(s.get('failed_runs', 0) for s in scan_summary.values())

scan_point = {
    'timestamp': timestamp,
    'total_scans': scans.get('unique_scans', 0),
    'total_launches': scans.get('total_launches', 0),
    'problem_scans': total_failed,
    'completed_scans': total_completed
}
```

### 2. `src/main.py`
**Line 56-57** - Extended scan collection period:
```python
# Old:
logger.info("  • Collecting scan data (past 7 days)...")
scan_data = scan_collector.collect(days_back=7, previous_run_data=previous_run)

# New:
logger.info("  • Collecting scan data (past 30 days)...")
scan_data = scan_collector.collect(days_back=30, previous_run_data=previous_run)
```

### 3. `src/reporters/console_reporter.py`
**Line 22-24** - Made header dynamic:
```python
# Old:
def print_scans(self, scan_data, analysis):
    self.print_section("SCAN HEALTH (Past 7 Days)")

# New:
def print_scans(self, scan_data, analysis):
    days_back = scan_data.get('days_back', 30)
    self.print_section(f"SCAN HEALTH (Past {days_back} Days)")
```

## Data Structure Reference

### Current Scan Data Structure (from collector)
```json
{
  "scans": {
    "days_back": 30,
    "total_launches": 218,
    "currently_running": 4,
    "unique_scans": 13,
    "scan_summary": {
      "Scan Name 1": {
        "completed_runs": 15,
        "failed_runs": 0,
        "stopped_runs": 0,
        "disabled_runs": 1,
        ...
      },
      "Scan Name 2": {
        "completed_runs": 12,
        "failed_runs": 2,
        ...
      }
    }
  }
}
```

### Trend Data Point (saved to trends.json)
```json
{
  "timestamp": "2026-06-05T16:29:56.127210+00:00",
  "total_scans": 13,
  "total_launches": 218,
  "problem_scans": 0,
  "completed_scans": 212
}
```

## Chart Display

The **Scan Health Over Time** chart now shows:
- **X-Axis:** Daily data points (e.g., "May 29", "Jun 1", "Jun 5")
- **Y-Axis:** Count of scans
- **Bar Chart:** 
  - Dark bar: Completed scans
  - Yellow bar: Problem scans (failed)

## Testing Results

**Before Fix:**
```
Scan trend data:
  total_scans: 0
  problem_scans: 0
  completed_scans: 0
```

**After Fix:**
```
Scan trend data:
  total_scans: 13
  total_launches: 218
  problem_scans: 0
  completed_scans: 212
```

## Benefits

1. ✅ **Scan chart now displays data** - Can visualize scan health trends over time
2. ✅ **30-day visibility** - Better long-term trend analysis (was 7 days)
3. ✅ **Accurate metrics** - Properly sums completed and failed runs across all scans
4. ✅ **Dynamic reporting** - Headers automatically reflect the days_back setting

## Notes

- Old trend data points (before this fix) will still show zeros for scans
- New data points collected after this fix will populate correctly
- After a few more daily runs, you'll see a complete 30-day scan health chart
- All other charts (authentication, license, agents) continue to work as before

## Future Improvements

Potential enhancements:
- Add scan success rate percentage to chart
- Show running scans as a third bar/line
- Add filters to chart by scan name or policy
- Export chart data to CSV
