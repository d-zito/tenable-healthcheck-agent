# Scan Status Update: Disabled vs Stopped

## Change Summary
Separated "disabled" scans from "stopped" scans and added the date when scans were disabled.

## The Distinction

### Disabled
- **What it means**: The scan schedule was disabled/turned off in Tenable
- **User action**: Intentionally disabled the scan configuration
- **Example**: Joy 3, Joy 4, Joy 5 scans were disabled on 2026-06-01
- **Not a failure**: This is intentional configuration management

### Stopped
- **What it means**: A running scan was manually stopped mid-execution
- **User action**: Clicked "Stop" while scan was running
- **Example**: User stopped a scan that was taking too long
- **Not a failure**: Intentional intervention during scan execution

### Failed
- **What it means**: Scan encountered an error and could not complete
- **Statuses**: `aborted`, `error`, `failed`
- **Example**: Scanner lost connectivity, authentication failed, target unreachable
- **IS a failure**: These require investigation

## New Data Structure

Each scan now tracks:
- `completed_runs` - Successfully completed scans
- `failed_runs` - Actual failures (aborted, error, failed)
- `stopped_runs` - Manually stopped during execution
- `disabled_runs` - Scan schedule was disabled
- `canceled_runs` - Scan was canceled before/during execution
- `paused_runs` - Scan was paused
- `disabled_entries` - Array of disabled occurrences with dates:
  ```json
  [
    {
      "date": "2026-06-01",
      "timestamp": 1717232400
    }
  ]
  ```

## Console Output

### Before This Update
```
Scan Name    Total Runs    Completed    Failed    Stopped
-----------  ------------  -----------  --------  ---------
Joy 3        14            13           0         1
```
Problem: "Stopped" column mixed disabled and stopped together

### After This Update
```
Scan Name    Total Runs    Completed    Failed    Stopped    Disabled
-----------  ------------  -----------  --------  ---------  ----------------
Joy 3        14            13           0         0          1 (2026-06-01)
Joy 4        14            13           0         0          1 (2026-06-01)
Joy 5        14            13           0         0          1 (2026-06-01)
```
Better: Clear separation, with date showing when it was disabled

## HTML Report Table

New columns:
1. **Scan Name**
2. **Total Runs** - All launches in past 7 days
3. **Completed** - Successfully completed
4. **Failed** - Actual failures (red badge)
5. **Stopped** - Manually stopped (yellow badge)
6. **Disabled** - Disabled scans (yellow badge with date)
7. **Success Rate** - Completion percentage

Example for disabled scan:
```
Disabled: 1
         (2026-06-01)
```
Shows the count and the most recent date it was disabled.

## Status Classification

### Success States
- `completed` → Completed counter

### In Progress
- `running` → Running counter (doesn't count toward total runs shown in table)

### Intentional User Actions (NOT failures)
- `disabled` → Disabled counter + date captured
- `stopped` → Stopped counter
- `canceled` / `cancelled` → Canceled counter
- `paused` → Paused counter

### Actual Failures (require investigation)
- `aborted` → Failed counter
- `error` → Failed counter
- `failed` → Failed counter

### Unknown
- Any other status → Logged and counted as potential failure

## Benefits

1. **Clear Semantics**: "Disabled" means configuration change, "Stopped" means manual intervention
2. **Date Tracking**: Know when scans were disabled for audit purposes
3. **Accurate Reporting**: Disabled scans don't clutter the "Stopped" column
4. **Better Context**: AI analysis can distinguish between disabled schedules and stopped executions

## Example Scenarios

### Scenario 1: Disabled Scan Schedule
- User disables "Joy 3" scan on June 1st
- Report shows: Disabled = 1 (2026-06-01)
- Interpretation: Scan schedule is off, intentional

### Scenario 2: Stopped Running Scan
- User starts a scan manually
- Realizes wrong target, clicks "Stop"
- Report shows: Stopped = 1
- Interpretation: Manual intervention during execution

### Scenario 3: Actual Failure
- Scheduled scan launches
- Target host is unreachable
- Scan aborts with error
- Report shows: Failed = 1
- Interpretation: Requires investigation

## Files Changed

1. `src/collectors/scan_collector.py`
   - Separate counters for disabled, stopped, canceled, paused
   - Capture disabled dates with timestamps
   - Return detailed breakdown in scan_summary

2. `src/reporters/html_reporter.py`
   - Added "Disabled" column
   - Show disabled count with date
   - Yellow badge for disabled scans

3. `src/reporters/console_reporter.py`
   - Added "Disabled" column
   - Format: "1 (2026-06-01)" if disabled entries exist
   - Clear separation from "Stopped"

## Testing

1. Run data collection:
   ```bash
   python3 src/main.py
   ```

2. Check console output for Joy scans:
   - Stopped: 0
   - Disabled: 1 (2026-06-01)

3. Generate HTML report:
   ```bash
   python3 src/generate_report.py
   ```

4. Verify HTML table shows:
   - Stopped column: 0 (green badge)
   - Disabled column: 1 with date (yellow badge)
