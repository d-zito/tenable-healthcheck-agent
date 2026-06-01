# AI Analysis Behavior

## Quick Reference

| Command | AI Behavior | Token Cost | Use Case |
|---------|-------------|------------|----------|
| `python3 src/generate_report.py` | **Runs fresh AI** | Yes (every time) | Production reports |
| `python3 src/generate_report.py --skip-ai` | Uses cached AI | No | HTML formatting iterations |

## Normal Mode (Default)

### Command
```bash
python3 src/generate_report.py
```

### Behavior
- **ALWAYS runs fresh AI analysis** with Claude
- Uses latest AI model capabilities
- Gets current insights and recommendations
- Caches result to JSON as a side effect (for testing mode)

### Token Usage
**YES** - Uses tokens every time

### When to Use
- **Production reports** (cron jobs, scheduled reports)
- **Real health checks** that need current AI analysis
- **Sharing with stakeholders**
- **Any time you want fresh insights**

### Example Output
```
Running AI analysis with Claude...
Caching AI analysis to data file for future testing...
Generating HTML report...
```

---

## Test Mode (`--skip-ai`)

### Command
```bash
python3 src/generate_report.py --skip-ai
```

### Behavior
- Skips AI processing entirely
- Uses cached AI analysis from JSON file
- Shows warning if no cache available

### Token Usage
**NO** - Zero tokens used

### When to Use
- **HTML/CSS formatting iterations**
- **Testing layout changes**
- **Quick report regeneration**
- **Any time you're NOT changing the data or analysis**

### Prerequisites
You must run normal mode at least once first to cache AI analysis:
```bash
# First: Generate with AI (caches analysis)
python3 src/generate_report.py --output reports/baseline.html

# Then: Iterate with --skip-ai (uses cache, no tokens)
python3 src/generate_report.py --skip-ai --output reports/test1.html
python3 src/generate_report.py --skip-ai --output reports/test2.html
# ... repeat as needed
```

### Example Output
```
⚙️  Test mode: Skipping AI analysis (using cached data from JSON)
Generating HTML report...
```

---

## Cron Job Setup

### Daily Data Collection (No AI, No Reports)
```bash
# Collect health data every day at 9am (no tokens used)
0 9 * * * cd /path/to/tenable-healthcheck-agent && source venv/bin/activate && python3 src/main.py
```

### Weekly Report with Fresh AI
```bash
# Generate report every Monday at 10am (uses tokens)
0 10 * * MON cd /path/to/tenable-healthcheck-agent && source venv/bin/activate && python3 src/generate_report.py --output reports/weekly_$(date +\%Y\%m\%d).html
```

### Result
- **Data collected**: 7 times per week (daily)
- **AI analysis runs**: 1 time per week (Monday)
- **Token cost**: 1x per week

---

## Typical Workflows

### Workflow 1: Production Report
```bash
# Generate report with fresh AI analysis
python3 src/generate_report.py --output reports/production.html

# Open and send to stakeholders
open reports/production.html
```
**Token cost**: 1x

---

### Workflow 2: HTML Formatting Iteration
```bash
# Step 1: Generate baseline with AI (pays once)
python3 src/generate_report.py --output reports/baseline.html

# Step 2: Edit HTML reporter
vim src/reporters/html_reporter.py

# Step 3: Test with cached AI (free)
python3 src/generate_report.py --skip-ai --output reports/test.html

# Step 4: Review
open reports/test.html

# Step 5: Repeat steps 2-4 as many times as needed (all free)
```
**Token cost**: 1x (only the baseline)

---

### Workflow 3: Multiple Report Formats
```bash
# Generate with fresh AI once
python3 src/generate_report.py --output reports/full_report.html

# Now generate additional formats using cached AI (no tokens)
python3 src/generate_report.py --skip-ai --output reports/summary.html
python3 src/generate_report.py --skip-ai --output reports/executive.html
```
**Token cost**: 1x (only the first)

---

## Why This Design?

### Philosophy
**Production reports deserve fresh AI analysis**
- AI models improve over time
- Fresh analysis = best insights
- Each report gets Claude's latest capabilities

**Test mode is for efficiency**
- Rapid HTML/CSS iteration
- No need to re-analyze same data
- Cache is a convenience, not the primary feature

### Benefits
1. **Quality First**: Normal mode always gives best results
2. **Cost Efficient**: Test mode enables free iteration
3. **Clear Intent**: Flag name (`--skip-ai`) makes purpose obvious
4. **No Surprises**: Default behavior is always fresh analysis

### Trade-offs
- **More token usage**: Every production report costs tokens
- **Worth it**: Fresh analysis is more valuable than saving tokens
- **Mitigated**: Test mode allows unlimited formatting iterations

---

## FAQ

**Q: Should I use `--skip-ai` for weekly reports?**  
A: No, use normal mode for production reports. Fresh AI analysis is worth the tokens.

**Q: When should I use `--skip-ai`?**  
A: Only when iterating on HTML/CSS formatting, or generating multiple format variations.

**Q: Will running reports multiple times use more tokens?**  
A: Yes, each normal run uses tokens. This ensures fresh analysis every time.

**Q: Can I reduce token usage?**  
A: Run reports less frequently (weekly instead of daily), but always use fresh AI for the reports you do generate.

**Q: What if I want to force fresh AI even if cached?**  
A: That's the default behavior! Just don't use `--skip-ai`.
