# Scan Status Classification Fix

## Problem
The scan collector was incorrectly classifying **disabled**, **stopped**, and **canceled** scans as **failures**.

### Example
- Joy 3, Joy 4, Joy 5 scans were manually disabled by the user
- Status in Tenable: `disabled`
- Old behavior: Counted as **FAILED** ❌
- New behavior: Counted as **STOPPED** (intentional action) ✓

## Root Cause

### Old Logic (Incorrect)
```python
failed_runs = sum(
    1 for h in recent_history
    if h.get('status', '').lower() not in ['completed', 'running']
)
```

**Problem**: Treated everything except `completed` and `running` as failures.

This meant:
- `disabled` = FAILED ❌
- `stopped` = FAILED ❌
- `canceled` = FAILED ❌
- `aborted` = FAILED ✓ (correct)
- `error` = FAILED ✓ (correct)

## Solution

### New Logic (Correct)
Categorize scan statuses into three groups:

1. **Success States**
   - `completed` - Scan finished successfully

2. **Intentional User Actions** (NOT failures)
   - `disabled` - User disabled the scan
   - `stopped` - User manually stopped the scan
   - `canceled` / `cancelled` - User canceled the scan
   - `paused` - User paused the scan

3. **Actual Failures**
   - `aborted` - Scan aborted due to error
   - `error` - Scan encountered an error
   - `failed` - Scan failed

4. **In Progress**
   - `running` - Scan currently executing

### New Code
```python
for h in recent_history:
    status = h.get('status', '').lower()

    if status == 'completed':
        completed_runs += 1
    elif status == 'running':
        running_count += 1
    elif status in ['disabled', 'stopped', 'canceled', 'cancelled', 'paused']:
        # Intentional user actions - not failures
        intentional_stops += 1
    elif status in ['aborted', 'error', 'failed']:
        # Actual failures
        failed_runs += 1
    else:
        # Unknown status - log and count as potential failure
        logger.debug(f"Unknown scan status '{status}' for scan '{scan_name}'")
        failed_runs += 1
```

## Changes Made

### 1. Updated: `src/collectors/scan_collector.py`
- Added proper status categorization
- New fields in scan summary:
  - `completed_runs` - Successfully completed scans
  - `failed_runs` - Actually failed scans (aborted, error, failed)
  - `intentional_stops` - User-stopped scans (disabled, stopped, canceled, paused)
  - `running_count` - Currently running scans
  - `success_runs` - Alias for `completed_runs` (for backwards compatibility)

### 2. Updated: `src/reporters/html_reporter.py`
- Added "Stopped" column to scan table
- Shows intentional stops with yellow badge (warning color)
- Shows failures with red badge (danger color)
- Table now shows: Total Runs | Completed | Failed | Stopped | Success Rate

### 3. Updated: `src/reporters/console_reporter.py`
- Added "Stopped" column to console output
- Updated table headers: Scan Name | Total Runs | Completed | Failed | Stopped

## New Report Output

### Console Output (Before)
```
Scan Name    Total Runs    Successful    Failed
-----------  ------------  ------------  --------
Joy 3        14            13            1        ❌ (disabled counted as failed)
Joy 4        14            13            1        ❌
Joy 5        14            13            1        ❌
```

### Console Output (After)
```
Scan Name    Total Runs    Completed    Failed    Stopped
-----------  ------------  -----------  --------  ---------
Joy 3        14            13           0         1         ✓ (disabled = stopped)
Joy 4        14            13           0         1         ✓
Joy 5        14            13           0         1         ✓
```

### HTML Report (Before)
| Scan Name | Total Runs | Successful | Failed | Success Rate |
|-----------|------------|------------|--------|--------------|
| Joy 3     | 14         | 13         | **1** 🔴 | 92.9%     |

### HTML Report (After)
| Scan Name | Total Runs | Completed | Failed | Stopped | Success Rate |
|-----------|------------|-----------|--------|---------|--------------|
| Joy 3     | 14         | 13        | **0** ✅ | **1** 🟡 | 92.9%     |

## Benefits

1. **Accurate Failure Tracking**: Only real failures (aborted, error) are counted as failures
2. **Clear User Actions**: Disabled/stopped/canceled scans are clearly visible but not alarming
3. **Better AI Analysis**: Claude will now receive accurate data (no false failures)
4. **Proper Alerting**: Alerts will only trigger for actual scan problems, not intentional stops

## Testing

To verify the fix:

1. Run data collection:
   ```bash
   python3 src/main.py
   ```

2. Check console output - Joy scans should show:
   - Failed: 0
   - Stopped: 1 (the disabled scan)

3. Generate report:
   ```bash
   python3 src/generate_report.py
   ```

4. Check HTML report - Joy scans should show:
   - Failed badge: green with "0"
   - Stopped badge: yellow with "1"

## Debugging

If you need to check actual status values from Tenable:

```bash
python3 debug_scan_status.py
```

This will show the raw status values for all Joy scans and their history.
