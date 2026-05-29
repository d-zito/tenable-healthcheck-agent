# Contributing

Thanks for your interest in contributing!

## Quick Start

1. Fork the repository
2. Create a branch: `git checkout -b feature/your-feature`
3. Make your changes
4. Test your changes: `python3 src/main.py`
5. Commit: `git commit -m "Add feature: description"`
6. Push: `git push origin feature/your-feature`
7. Open a Pull Request

## Adding Features

### New Data Collector
1. Create `src/collectors/your_collector.py`
2. Implement a `collect()` method that returns a dictionary
3. Add to `src/main.py`
4. Add analysis method in `src/analyzers/change_analyzer.py`
5. Add reporting in `src/reporters/console_reporter.py`

### New Output Format
1. Create `src/reporters/your_reporter.py`
2. Implement print methods for each section
3. Use in `src/main.py`

## Code Style

- Follow PEP 8
- Use descriptive variable names
- Add docstrings for complex functions
- Keep functions focused and simple

## Testing

Before submitting:
- Test with real Tenable credentials
- Verify both first-run and subsequent-run scenarios
- Check that data saves correctly to `data/history/`

## Questions?

Open an issue for discussion before major changes.
