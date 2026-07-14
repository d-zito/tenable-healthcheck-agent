# Tenable One Health Check Agent

An open-source health monitoring tool for Tenable One that tracks scan health, credentials, license usage, agents, scanners, and connectors over time.

## Features

- 📊 **Scan Health** - Track aborted/incomplete scans since last run
- 🔐 **Credential Scans** - Monitor percentage of successful credentialed scans
- 📈 **License Tracking** - Alert on significant changes in license usage
- 🤖 **Agent Status** - Monitor offline agents (flags agents offline 14+ days)
- 🖥️ **Scanner Health** - Track scanner status and detect issues
- 🔌 **Connector Health** - Monitor connector status
- 👥 **User Management** - Track user accounts, roles, and login activity
- 🧠 **AI Analysis** - LLM-powered insights and recommendations (supports Claude, GPT-4, Ollama, and more)
- 📊 **Historical Tracking** - Compare runs over time to detect trends

## Quick Start (5 minutes)

### 1. Prerequisites

- Python 3.8 or higher
- Tenable Vulnerability Management API keys ([Get them here](https://cloud.tenable.com) → Settings → API Keys)
- (Optional) LLM provider for AI analysis:
  - **Claude CLI** (recommended for development)
  - **OpenAI API** (GPT-4)
  - **Anthropic API** (Claude via API)
  - **Ollama** (local/open-source models)
  - See [LLM Configuration Guide](docs/LLM_CONFIGURATION.md) for details

**Note:** This tool uses the official [pytenable](https://pytenable.readthedocs.io/) SDK.

### 2. Installation

```bash
cd tenable-healthcheck-agent
./setup.sh
```

This creates a virtual environment and installs dependencies.

Or manually:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp config/config.example.json config/config.json
mkdir -p data/history
```

### 3. Configure

**Option A: Configuration File** (Recommended for development)

Edit `config/config.json` with your Tenable credentials:

```json
{
  "tenable": {
    "access_key": "YOUR_ACCESS_KEY",
    "secret_key": "YOUR_SECRET_KEY",
    "base_url": "https://cloud.tenable.com"
  },
  "thresholds": {
    "credential_scan_change_percent": 10,
    "license_change_percent": 5,
    "agent_offline_days": 14
  },
  "data_retention_days": 90,
  "llm": {
    "enabled": true,
    "provider": "claude_cli"
  }
}
```

**LLM Provider Options:**

The tool supports multiple AI providers for analysis. Choose one:

| Provider | Setup | Cost | Best For |
|----------|-------|------|----------|
| `claude_cli` | Install [Claude CLI](https://claude.ai/download) | Free* | Development |
| `openai` | API key from [OpenAI](https://platform.openai.com/) | Pay per use | Production |
| `anthropic` | API key from [Anthropic](https://console.anthropic.com/) | Pay per use | Production |
| `ollama` | Install [Ollama](https://ollama.ai/) | Free | Offline/airgapped |

*Requires Claude subscription. See [LLM Configuration Guide](docs/LLM_CONFIGURATION.md) for detailed setup.

**Example configurations:**

```json
// OpenAI GPT-4
{
  "llm": {
    "enabled": true,
    "provider": "openai",
    "api_key": "sk-proj-...",
    "model": "gpt-4-turbo-preview"
  }
}

// Anthropic Claude API
{
  "llm": {
    "enabled": true,
    "provider": "anthropic",
    "api_key": "sk-ant-...",
    "model": "claude-sonnet-4-20250514"
  }
}

// Ollama (local)
{
  "llm": {
    "enabled": true,
    "provider": "ollama",
    "model": "llama2"
  }
}

// Disable AI analysis
{
  "llm": {
    "enabled": false
  }
}
```

**Option B: Environment Variables** (Recommended for production/CI)

Set environment variables instead of storing credentials in config file:

```bash
export TENABLE_ACCESS_KEY="your_access_key"
export TENABLE_SECRET_KEY="your_secret_key"
export TENABLE_BASE_URL="https://cloud.tenable.com"  # Optional
```

Environment variables take precedence over config file values.

### 4. Run

```bash
source venv/bin/activate  # Activate virtual environment
python3 src/main.py
```

**First run**: Establishes baseline data  
**Subsequent runs**: Shows comparisons and detects changes

**Note**: You must activate the virtual environment (`source venv/bin/activate`) each time before running.

### 5. Generate HTML Report (Optional)

```bash
# Generate from latest run
python3 src/generate_report.py

# Generate from specific date
python3 src/generate_report.py --date 20260528_103045

# Specify output file
python3 src/generate_report.py --output my_report.html

# Open the report in browser
open reports/healthcheck_*.html
```

HTML reports are saved to `reports/` directory with styled tables, color-coded alerts, and easy-to-read formatting.

## How It Works

### Data Flow
```
Tenable API → Collectors → Analyzers → AI Analysis (Optional) → Report
                       ↓
                   Storage (historical data)
```

### On Each Run
1. Collects current data from Tenable
2. Compares against previous run (if available)
3. Analyzes changes and detects anomalies
4. Gets AI-powered insights (if LLM provider configured)
5. Saves data for next comparison
6. Generates comprehensive report

## Project Structure

```
tenable-healthcheck-agent/
├── src/
│   ├── main.py                    # Entry point - run this!
│   ├── tenable_client.py          # Tenable API wrapper
│   ├── config_loader.py           # Configuration management
│   ├── collectors/                # Data collection modules
│   │   ├── scan_collector.py
│   │   ├── asset_collector.py
│   │   ├── license_collector.py
│   │   ├── agent_collector.py
│   │   ├── scanner_collector.py
│   │   └── connector_collector.py
│   ├── analyzers/                 # Analysis logic
│   │   ├── change_analyzer.py     # Compare runs
│   │   └── claude_analyzer.py     # AI insights
│   ├── storage/
│   │   └── storage_manager.py     # Historical data
│   └── reporters/
│       └── console_reporter.py    # Terminal output
├── config/
│   └── config.example.json        # Template config
├── data/history/                  # Historical run data (auto-created)
└── README.md
```

## Configuration Options

| Setting | Description | Default |
|---------|-------------|---------|
| `credential_scan_change_percent` | Alert threshold for credential % changes | 10 |
| `license_change_percent` | Alert threshold for license changes | 5 |
| `agent_offline_days` | Days before flagging agent as long-term offline | 14 |
| `data_retention_days` | How long to keep historical data | 90 |
| `llm.enabled` | Enable/disable AI analysis | true |
| `llm.provider` | LLM provider (claude_cli, openai, anthropic, ollama) | claude_cli |

## Sample Output

```
===============================================================================
                   TENABLE ONE HEALTH CHECK REPORT                   
                 Generated: 2026-05-28 10:30:00                 
===============================================================================

SCAN HEALTH
-----------
Total scans checked: 45
Problem scans: 2
Completed scans: 43

Problem Scans:
Name                    Status     Last Modified
Weekly Full Scan        aborted    2026-05-27 14:23
Compliance Check        stopped    2026-05-28 02:15

Change from previous run: +1 problem scans

ASSET CREDENTIAL SCANS
----------------------
Total assets: 1,250
Credentialed scans: 1,100 (88.0%)
Uncredentialed: 150

Change from previous run: ↓ 2.5%

LICENSE USAGE
-------------
Total licensed assets: 2,000
Used: 1,250 (62.5%)
Available: 750

Change from previous run: → +15 assets (+1.2%)

AGENT STATUS
------------
Total agents: 150
Online: 142
Offline: 8
Offline > 14 days: 3

Agents offline > 14 days:
Name              Status    Last Connect
Agent-Server-05   offline   2026-05-01
Agent-Laptop-23   offline   2026-04-28

USER ACCOUNTS
-------------
Total users: 45
Enabled users: 38
Disabled users: 7
New users (past 30 days): 2
Enabled users with no login in 30+ days: 5

--- User Roles ---
Role                   Count
Administrator          8
Scan Manager          12
Scan Operator         15
Basic User             10

AI ANALYSIS (Claude)
--------------------
Health Status: ⚠️ WARNING

Executive Summary:
Two scans require attention. Weekly Full Scan aborted mid-run and should be 
investigated. Overall credential scan rate of 88% is healthy. 3 agents have 
been offline for 14+ days and may need decommission review.

Key Concerns:
  • Weekly Full Scan aborted - investigate scanner connectivity
  • 3 agents offline for 14+ days - verify if systems are decommissioned

Recommendations:
  [HIGH] Weekly Full Scan aborted
         → Check scanner logs and target connectivity
  [MEDIUM] Long-term offline agents
         → Review if these systems should be removed from inventory
```

## Logging

The agent automatically logs to both console and file:
- **Console**: User-friendly output with progress updates
- **File**: Detailed logs saved to `logs/healthcheck.log`

Logs include:
- Timestamps for all operations
- API collection progress
- Error messages with stack traces
- Claude analysis status
- Storage operations

View recent logs:
```bash
tail -f logs/healthcheck.log
```

## Automation

### Linux/Mac (cron)
```bash
crontab -e
# Add this line for daily 9am runs:
0 9 * * * cd /path/to/tenable-healthcheck-agent && source venv/bin/activate && python3 src/main.py
```

### Windows (Task Scheduler)
1. Open Task Scheduler
2. Create Basic Task → Daily → 9:00 AM
3. Action: Start a Program
   - Program: `python3`
   - Arguments: `src/main.py`
   - Start in: `C:\path\to\tenable-healthcheck-agent`

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Configuration file not found" | Run `./setup.sh` or copy `config.example.json` to `config.json` |
| "Authentication failed" | Verify API keys in `config.json` are correct and haven't expired |
| "LLM provider not available" | See [LLM Configuration Guide](docs/LLM_CONFIGURATION.md) for setup instructions |
| "Module not found" | Run `pip3 install -r requirements.txt` |

## Future Enhancement Ideas

- Email/Slack notifications for critical issues
- Web dashboard for visualization
- Historical trend graphs
- Export to CSV/Excel
- Docker containerization
- Multi-environment support

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## License

MIT License - See [LICENSE](LICENSE) file for details.

## Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/tenable-healthcheck-agent/issues)
- **Documentation**: [API Reference](docs/API_REFERENCE.md)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/tenable-healthcheck-agent/discussions)

## Getting Help

**First time with Python?**
- This project is beginner-friendly!
- All code is well-commented
- Start by reading `src/main.py` to understand the flow

**Need to extend it?**
- Want a new check? Add a collector in `src/collectors/`
- Want different output? Modify `src/reporters/console_reporter.py`
- Want new analysis? Update `src/analyzers/change_analyzer.py`

**Questions?** Open an issue - we're here to help!
