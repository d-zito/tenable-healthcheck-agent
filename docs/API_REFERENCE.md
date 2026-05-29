# API Reference

This document describes the internal APIs and modules of the Tenable Health Check Agent.

## Core Modules

### ConfigLoader (`src/config_loader.py`)

Manages configuration loading and access.

```python
config = ConfigLoader(config_path="/path/to/config.json")
creds = config.get_tenable_credentials()
thresholds = config.get_thresholds()
```

**Methods:**
- `get_tenable_credentials()` - Returns dict with access_key, secret_key, base_url
- `get_thresholds()` - Returns threshold configuration
- `get_data_retention_days()` - Returns retention period
- `use_claude_cli()` - Returns boolean for Claude CLI usage

### TenableClient (`src/tenable_client.py`)

Handles all Tenable API interactions.

```python
client = TenableClient(access_key, secret_key, base_url)
scans = client.get_scans()
assets = client.list_assets()
```

**Methods:**
- `get_scans()` - Fetch all scans
- `get_scan_details(scan_id)` - Get details for specific scan
- `list_assets()` - Fetch all assets (handles pagination)
- `get_license_info()` - Get license information
- `list_agents()` - Fetch all agents (handles pagination)
- `list_scanners()` - Fetch all scanners
- `list_connectors()` - Fetch all connectors

### StorageManager (`src/storage/storage_manager.py`)

Manages historical data persistence.

```python
storage = StorageManager(data_dir="/path/to/data", retention_days=90)
storage.save_run_data(data)
previous = storage.get_previous_run()
```

**Methods:**
- `save_run_data(data)` - Save current run data
- `get_latest_run()` - Get most recent run
- `get_previous_run()` - Get second most recent run
- `get_all_runs(limit=None)` - Get all runs (or last N)

## Collectors

All collectors follow the same pattern:

```python
collector = SomeCollector(tenable_client)
data = collector.collect()
```

### ScanCollector (`src/collectors/scan_collector.py`)

**Constructor:**
```python
ScanCollector(tenable_client)
```

**Methods:**
- `collect(last_run_timestamp=None)` - Collect scan data

**Returns:**
```python
{
    'total_scans': int,
    'problem_scans': list,
    'completed_scans': list,
    'scans_checked_since': str
}
```

### AssetCollector (`src/collectors/asset_collector.py`)

**Returns:**
```python
{
    'total_assets': int,
    'credentialed_assets': int,
    'credential_percentage': float,
    'uncredentialed_assets': int
}
```

### LicenseCollector (`src/collectors/license_collector.py`)

**Returns:**
```python
{
    'total_licensed_assets': int,
    'total_used_assets': int,
    'total_available_assets': int,
    'overall_utilization_percent': float,
    'license_details': list
}
```

### AgentCollector (`src/collectors/agent_collector.py`)

**Constructor:**
```python
AgentCollector(tenable_client, offline_threshold_days=14)
```

**Returns:**
```python
{
    'total_agents': int,
    'online_agents': int,
    'offline_agents': int,
    'offline_agent_list': list,
    'long_offline_agents': int,
    'long_offline_agent_list': list,
    'offline_threshold_days': int
}
```

### ScannerCollector (`src/collectors/scanner_collector.py`)

**Returns:**
```python
{
    'total_scanners': int,
    'working_scanners': int,
    'problem_scanners': int,
    'problem_scanner_list': list
}
```

### ConnectorCollector (`src/collectors/connector_collector.py`)

**Returns:**
```python
{
    'total_connectors': int,
    'working_connectors': int,
    'problem_connectors': int,
    'problem_connector_list': list
}
```

## Analyzers

### ChangeAnalyzer (`src/analyzers/change_analyzer.py`)

Compares current data with previous runs.

```python
analyzer = ChangeAnalyzer(thresholds)
analysis = analyzer.analyze_scans(current_data, previous_data)
```

**Methods:**
- `analyze_scans(current_data, previous_data)` - Compare scan data
- `analyze_credentials(current_data, previous_data)` - Compare credential percentages
- `analyze_license(current_data, previous_data)` - Compare license usage
- `analyze_agents(current_data, previous_data)` - Compare agent status
- `analyze_scanners(current_data, previous_data)` - Compare scanner status
- `analyze_connectors(current_data, previous_data)` - Compare connector status

### ClaudeAnalyzer (`src/analyzers/claude_analyzer.py`)

Uses Claude for AI-powered analysis.

```python
analyzer = ClaudeAnalyzer(use_cli=True)
results = analyzer.analyze_health_report(current_data, analysis_results)
```

**Methods:**
- `analyze_health_report(current_data, analysis_results)` - Get AI analysis

**Returns:**
```python
{
    'health_status': 'healthy|warning|critical',
    'executive_summary': str,
    'key_concerns': list,
    'recommendations': list,
    'trends': list
}
```

## Reporters

### ConsoleReporter (`src/reporters/console_reporter.py`)

Formats output for terminal display.

```python
reporter = ConsoleReporter()
reporter.print_header()
reporter.print_scans(scan_data, analysis)
reporter.print_footer()
```

**Methods:**
- `print_header()` - Print report header
- `print_section(title)` - Print section header
- `print_scans(scan_data, analysis)` - Print scan section
- `print_assets(asset_data, analysis)` - Print asset section
- `print_license(license_data, analysis)` - Print license section
- `print_agents(agent_data, analysis)` - Print agent section
- `print_scanners(scanner_data, analysis)` - Print scanner section
- `print_connectors(connector_data, analysis)` - Print connector section
- `print_claude_analysis(claude_results)` - Print AI analysis
- `print_footer()` - Print report footer

## Data Structures

### Historical Data Format

Stored in `data/history/healthcheck_YYYYMMDD_HHMMSS.json`:

```json
{
  "timestamp": "2026-05-28T10:30:00",
  "data": {
    "scans": { ... },
    "assets": { ... },
    "license": { ... },
    "agents": { ... },
    "scanners": { ... },
    "connectors": { ... }
  }
}
```

## Extension Points

### Adding a New Collector

1. Create `src/collectors/your_collector.py`
2. Implement `collect()` method
3. Add to `main.py` imports and execution
4. Add analysis in `change_analyzer.py`
5. Add reporting in `console_reporter.py`

### Adding a New Reporter

1. Create `src/reporters/your_reporter.py`
2. Implement print methods for each section
3. Instantiate and use in `main.py`

### Adding API Support

Update `TenableClient` with new methods:

```python
def get_your_resource(self):
    return self._get('/api/endpoint')
```
