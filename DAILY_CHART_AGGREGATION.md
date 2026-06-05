# Daily Chart Aggregation Feature

## Overview
Modified the trending charts to display **daily data points** instead of showing every individual run. When multiple health checks are performed in a single day, only the **last run of that day** is used for charting.

## Changes Made

### 1. `src/storage/trends_manager.py`

**Added `_aggregate_by_day()` method:**
- Groups all data points by date (YYYY-MM-DD)
- Keeps only the last run for each date (based on timestamp)
- Returns sorted daily data points

**Modified `get_trends()` method:**
- Added `daily_aggregation=False` parameter
- When `daily_aggregation=True`, calls `_aggregate_by_day()` before returning data

### 2. `src/generate_report.py`

**Line 140 change:**
```python
# Before:
trends_data = trends_manager.get_trends()

# After:
trends_data = trends_manager.get_trends(daily_aggregation=True)
```

## How It Works

### Data Collection (No changes)
Every time you run `python3 src/main.py`, a data point is saved to `data/trends.json` with a timestamp like:
```json
{
  "timestamp": "2026-06-05T15:27:28.240943+00:00",
  "auth_succeeded_pct": 33.57,
  ...
}
```

### Aggregation Logic
When generating reports, the system now:

1. **Loads all trend data** from `trends.json`
2. **Groups by date** - All runs on the same calendar day are grouped together
3. **Keeps last run** - For each day, only the most recent run (by timestamp) is kept
4. **Sorts by date** - Daily points are returned in chronological order

### Example

**Before (19 data points):**
- May 29, 2026 @ 08:00 AM
- May 29, 2026 @ 10:30 AM
- May 29, 2026 @ 02:15 PM
- May 29, 2026 @ 08:53 PM ← **Latest on May 29**
- June 1, 2026 @ 09:10 AM
- June 1, 2026 @ 10:27 AM
- June 1, 2026 @ 08:44 PM ← **Latest on June 1**
- ... (multiple more runs)

**After daily aggregation (3 data points):**
- May 29, 2026 @ 08:53 PM
- June 1, 2026 @ 08:44 PM
- June 5, 2026 @ 03:27 PM

### Chart Display

**X-Axis:** Shows one point per day (e.g., "May 29", "Jun 1", "Jun 5")

**Y-Axis:** Shows the metric value from the last run of that day

This makes the charts:
- ✅ **Cleaner** - No clutter from multiple runs per day
- ✅ **More readable** - Clear daily trends over time
- ✅ **Accurate** - Uses most recent data from each day

## Testing Results

Tested with existing trends data:
```
Raw data points:
  authentication: 19 points
  license: 19 points
  agents: 19 points
  scans: 19 points

Daily aggregated data points:
  authentication: 3 points (May 29, Jun 1, Jun 5)
  license: 3 points
  agents: 3 points
  scans: 3 points
```

## Backward Compatibility

- ✅ **No breaking changes** - Old `get_trends()` calls without parameters work as before
- ✅ **Data format unchanged** - Raw trend data is still stored with all timestamps
- ✅ **Flexible** - Can still access raw data by using `get_trends(daily_aggregation=False)`

## Future Enhancements

Possible additions:
- Add `days` parameter filtering (e.g., last 30 days, last 90 days)
- Support for different aggregation strategies (first run, average, min/max)
- Weekly or monthly aggregation options
- Custom date range selection in reports
