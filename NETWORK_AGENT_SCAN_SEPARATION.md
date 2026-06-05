# Network and Agent Scan Separation

## Overview
Split the scan health section into two separate sections: **Network Scans** (remote) and **Agent Scans**, providing clearer visibility into each scan type.

## Implementation

### Scan Type Detection
Uses the `scan_type` field from Tenable API:
- **`remote`** = Network scan (scanner-based)
- **`agent`** = Agent scan (agent-based)
- **`unknown`** = Any other type (displayed in "Other Scans" section)

### Data Source
The `scan_type` field is retrieved from:
```python
scan_results = client.tio.scans.results(scan_id)
info = scan_results.get('info', {})
scan_type = info.get('scan_type', 'unknown')
```

## Changes Made

### 1. `src/collectors/scan_collector.py`

**Added scan_type collection:**
- Fetches `scan_type` from scan results API
- Caches scan_type along with policy and enabled status
- Stores scan_type in scan_summary for each scan

**Lines modified:**
- Added `cached_scan_type` variable for caching
- Extract `scan_type` from `info.get('scan_type', 'unknown')`
- Added `'scan_type': scan_type` to scan_summary dictionary

### 2. `src/reporters/html_reporter.py`

**Modified `_add_scan_section()` method:**

**Overview Section:**
- Renamed header to "Scan Health Overview" for clarity
- Stats cards remain the same (total launches, running, unique scans, failures)

**Separated Tables:**
- Split scans into three categories:
  - `agent_scans`: where `scan_type == 'agent'`
  - `network_scans`: where `scan_type == 'remote'`
  - `unknown_scans`: any other scan_type
  
- Created `render_scan_table()` helper function to avoid code duplication
- Each table shows:
  - Section title with emoji (🌐 for network, 🤖 for agent)
  - Count summary: X scans, Y launches, Z failures
  - Full table with all scan metrics

**Display Order:**
1. Network Scans (if any exist)
2. Agent Scans (if any exist)
3. Other Scans (if any exist with unknown type)

### 3. `src/reporters/console_reporter.py`

**Modified `print_scans()` method:**

**Summary Line:**
```
Total scan launches: 218
  Network scans: 30 launches (1 scans)
  Agent scans: 0 launches (0 scans)
Currently running: 3
```

**Separated Tables:**
- Created `print_scan_table()` helper function
- Prints "🌐 Network Scans" table first
- Then prints "🤖 Agent Scans" table
- Same columns as before for each table

## Report Structure

### HTML Report

```
📊 Scan Health Overview (Past 30 Days)
┌─────────────────────────────────────┐
│ Total Launches  | Currently Running │
│ Unique Scans    | Total Failed Runs │
└─────────────────────────────────────┘

🌐 Network Scans (5 scans, 150 launches, 2 failures)
┌─────────────────────────────────────────────────┐
│ Scan Name | Policy | Enabled | Runs | Success  │
├─────────────────────────────────────────────────┤
│ Scan 1    | ...    | ✓       | 30   | 100%     │
│ Scan 2    | ...    | ✓       | 25   | 96%      │
└─────────────────────────────────────────────────┘

🤖 Agent Scans (3 scans, 68 launches, 0 failures)
┌─────────────────────────────────────────────────┐
│ Scan Name | Policy | Enabled | Runs | Success  │
├─────────────────────────────────────────────────┤
│ Agent 1   | ...    | ✓       | 25   | 100%     │
│ Agent 2   | ...    | ✓       | 23   | 100%     │
└─────────────────────────────────────────────────┘
```

### Console Report

```
SCAN HEALTH (Past 30 Days)
--------------------------
Total scan launches: 218
  Network scans: 150 launches (5 scans)
  Agent scans: 68 launches (3 scans)
Currently running: 3

🌐 Network Scans:
Scan Name    Policy         Enabled  Total Runs  Running  Successful  ...
-----------  -------------  -------  ----------  -------  ----------  ...
Scan 1       Basic Network  ✓        30          0        30          ...
Scan 2       Advanced Net   ✓        25          0        24          ...

🤖 Agent Scans:
Scan Name    Policy         Enabled  Total Runs  Running  Successful  ...
-----------  -------------  -------  ----------  -------  ----------  ...
Agent Scan 1 Basic Agent    ✓        25          0        25          ...
Agent Scan 2 Advanced Agt   ✓        23          0        23          ...

Change from previous run:
  Total launches: +15
  Currently running: -1
```

## Benefits

1. ✅ **Clear separation** - Easy to distinguish network vs agent scanning activity
2. ✅ **Quick insights** - See at a glance how many network vs agent scans you have
3. ✅ **Better organization** - Related scans grouped together
4. ✅ **Failure tracking** - See failures by scan type in section headers
5. ✅ **Performance tuning** - Easier to identify which scan type needs attention

## Data Caching

The scan_type field is cached along with policy and enabled status:
- Only re-fetched when scan's `last_modification_date` changes
- Reduces API calls on subsequent health check runs
- Previous run data preserved in cache

## Edge Cases Handled

1. **Unknown scan types** - Displayed in separate "Other Scans" section with ❓ emoji
2. **Empty sections** - If no scans of a type exist, that section is omitted
3. **Backward compatibility** - Old data without scan_type will show as unknown type
4. **API failures** - If scan_type can't be fetched, defaults to 'unknown'

## Testing Results

**Environment Tested:**
- 1 Network scan (remote type)
- 0 Agent scans
- Total: 218 launches over 30 days

**Console Output:**
```
Total scan launches: 218
  Network scans: 30 launches (1 scans)
  Agent scans: 0 launches (0 scans)
Currently running: 3

🌐 Network Scans:
Scan Name        Policy              Enabled      Total Runs    Running    Successful
---------------  ------------------  ---------  ------------  ---------  ------------
TPM Assets Scan  Basic Network Scan  ✓                    30          0            30
```

## Future Enhancements

Potential additions:
- Separate trend charts for network vs agent scans
- Different thresholds for network vs agent scan failures
- Scan type-specific recommendations in AI analysis
- Filter charts by scan type
- Compare network vs agent success rates
