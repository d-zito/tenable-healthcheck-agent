from __future__ import annotations

import html
import json
from datetime import datetime, timedelta, timezone
from typing import Any


class HTMLReporter:
    def __init__(self) -> None:
        self.html_parts: list[str] = []

    @staticmethod
    def _escape(value: Any) -> str:
        return html.escape(str(value)) if value is not None else ''

    def _render_comparison_table(
        self,
        title: str,
        rows: list[dict[str, Any]],
        historical_7d: dict[str, Any] | None,
        historical_30d: dict[str, Any] | None,
        total_row: dict[str, Any] | None = None,
    ) -> str:
        lines = [f'''
                <table style="margin-bottom: 15px;">
                    <thead>
                        <tr>
                            <th></th>
                            <th style="text-align: center;">Current</th>
                            <th style="text-align: center;">7d Ago</th>
                            <th style="text-align: center;">30d Ago</th>
                        </tr>
                    </thead>
                    <tbody>''']

        for row in rows:
            label = self._escape(row['label'])
            current = row['current']
            key_7d = row.get('key')
            val_7d = historical_7d.get(key_7d, '-') if historical_7d and key_7d else '-'
            val_30d = historical_30d.get(key_7d, '-') if historical_30d and key_7d else '-'
            suffix = row.get('suffix', '')
            lines.append(f'''
                        <tr>
                            <td>{label}</td>
                            <td style="text-align: center;">{current}{suffix}</td>
                            <td style="text-align: center;">{val_7d}{suffix if val_7d != "-" else ""}</td>
                            <td style="text-align: center;">{val_30d}{suffix if val_30d != "-" else ""}</td>
                        </tr>''')

        if total_row:
            label = self._escape(total_row['label'])
            current = total_row['current']
            key_7d = total_row.get('key')
            val_7d = historical_7d.get(key_7d, '-') if historical_7d and key_7d else '-'
            val_30d = historical_30d.get(key_7d, '-') if historical_30d and key_7d else '-'
            lines.append(f'''
                        <tr style="border-top: 2px solid #1E2426;">
                            <td>{label}</td>
                            <td style="text-align: center;">{current}</td>
                            <td style="text-align: center;">{val_7d}</td>
                            <td style="text-align: center;">{val_30d}</td>
                        </tr>''')

        lines.append('''
                    </tbody>
                </table>''')
        return '\n'.join(lines)

    def _get_historical_data(self, trends_data: dict[str, Any] | None) -> dict[str, Any] | None:
        if not trends_data:
            return None

        now = datetime.now(timezone.utc)
        seven_days_ago = now - timedelta(days=7)
        thirty_days_ago = now - timedelta(days=30)

        def find_closest_data_point(data_points: list[dict], target_date: datetime) -> dict | None:
            if not data_points:
                return None
            closest = None
            min_diff: float | None = None
            for point in data_points:
                try:
                    point_date = datetime.fromisoformat(point['timestamp'])
                    diff = abs((point_date - target_date).total_seconds())
                    if min_diff is None or diff < min_diff:
                        min_diff = diff
                        closest = point
                except (ValueError, KeyError):
                    continue
            if closest and min_diff is not None and min_diff <= (2 * 24 * 60 * 60):
                return closest
            return None

        categories = ['authentication', 'license', 'agents', 'scanners', 'connectors', 'users']
        historical: dict[str, dict] = {}
        for cat in categories:
            historical[cat] = {
                '7_days': find_closest_data_point(trends_data.get(cat, []), seven_days_ago),
                '30_days': find_closest_data_point(trends_data.get(cat, []), thirty_days_ago),
            }
        return historical

    def generate(
        self,
        run_data: dict[str, Any],
        analysis_results: dict[str, Any],
        claude_analysis: dict[str, Any] | None = None,
        trends_data: dict[str, Any] | None = None,
    ) -> str:
        timestamp = run_data.get('timestamp', 'Unknown')
        data = run_data.get('data', {})

        if timestamp != 'Unknown':
            try:
                dt = datetime.fromisoformat(timestamp)
                formatted_timestamp = dt.strftime('%B %d, %Y at %I:%M %p UTC')
            except (ValueError, AttributeError):
                formatted_timestamp = timestamp
        else:
            formatted_timestamp = timestamp

        historical_data = self._get_historical_data(trends_data)

        self._add_header(formatted_timestamp)

        if claude_analysis and not claude_analysis.get('error'):
            self._add_claude_section(claude_analysis)

        self._add_health_dashboard(data, historical_data)

        self._add_changes_strip(data, historical_data)

        if trends_data:
            self._add_trends_section(trends_data)

        self.html_parts.append('<div class="status-accordion">')
        self._add_scan_section(data.get('scans', {}), analysis_results.get('scans', {}))
        self._add_asset_section(data.get('assets', {}), analysis_results.get('assets', {}), analysis_results.get('license', {}), historical_data)
        self._add_agent_section(data.get('agents', {}), analysis_results.get('agents', {}), historical_data)
        self._add_scanner_section(data.get('scanners', {}), analysis_results.get('scanners', {}), historical_data)
        self._add_connector_section(data.get('connectors', {}), analysis_results.get('connectors', {}), historical_data)
        self._add_user_section(data.get('users', {}), analysis_results.get('users', {}), historical_data)
        self.html_parts.append('</div>')

        self._add_footer()

        return '\n'.join(self.html_parts)

    def _add_header(self, timestamp: str) -> None:
        self.html_parts.append('''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Tenable Health Check Report</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Work+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: "Work Sans", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            line-height: 1.4;
            color: #1E2426;
            background: #f5f5f5;
            padding: 15px;
            padding-top: 55px;
            letter-spacing: -0.02em;
            font-size: 14px;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 4px;
            box-shadow: 0 1px 4px rgba(0,0,0,0.1);
            overflow: hidden;
        }

        /* Sticky Navigation */
        .sticky-nav {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            z-index: 1000;
            background: #1E2426;
            border-bottom: 2px solid #E7FF00;
            padding: 0 20px;
            display: flex;
            align-items: center;
            height: 40px;
            overflow-x: auto;
            white-space: nowrap;
        }
        .sticky-nav a {
            color: #ccc;
            text-decoration: none;
            font-size: 12px;
            font-weight: 500;
            padding: 8px 12px;
            border-radius: 3px;
            transition: all 0.2s;
        }
        .sticky-nav a:hover {
            color: #E7FF00;
            background: rgba(231, 255, 0, 0.1);
        }
        .sticky-nav .nav-brand {
            color: #E7FF00;
            font-weight: 700;
            font-size: 13px;
            margin-right: 10px;
            padding-right: 10px;
            border-right: 1px solid #444;
        }

        .header {
            background: linear-gradient(135deg, #1E2426 0%, #2a3235 100%);
            color: white;
            padding: 20px 25px;
            border-bottom: 3px solid #E7FF00;
        }
        .header h1 {
            font-size: 22px;
            margin-bottom: 5px;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .header .timestamp {
            font-size: 12px;
            opacity: 0.85;
            color: #E7FF00;
        }
        .content { padding: 20px 25px; }
        .section {
            margin-bottom: 40px;
            padding: 20px 22px;
            background: white;
            border-radius: 6px;
            box-shadow: 0 2px 6px rgba(0,0,0,0.06);
            border: 1px solid #e0e0e0;
        }
        .section h2 {
            color: #1E2426;
            font-size: 24px;
            margin-bottom: 15px;
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 8px;
            border-bottom: 2px solid #1E2426;
            padding-bottom: 10px;
        }
        .stat-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
            gap: 10px;
            margin-bottom: 12px;
        }
        .stat-card {
            background: #fafafa;
            padding: 10px 12px;
            border-radius: 4px;
            border-left: 3px solid #1E2426;
        }
        .stat-card .label {
            font-size: 10px;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 4px;
            font-weight: 500;
        }
        .stat-card .value {
            font-size: 18px;
            font-weight: 600;
            color: #1E2426;
        }
        .stat-card.warning { border-left-color: #b8860b; }
        .stat-card.warning .value { color: #b8860b; }
        .stat-card.success { border-left-color: #00c853; }
        .stat-card.success .value { color: #00c853; }
        .stat-card.danger { border-left-color: #ff1744; }
        .stat-card.danger .value { color: #ff1744; }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
            background: white;
            font-size: 13px;
        }
        th {
            background: #1E2426;
            color: white;
            padding: 8px 10px;
            text-align: center;
            font-weight: 600;
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        th:first-child { text-align: left; }
        td {
            padding: 6px 10px;
            border-bottom: 1px solid #e0e0e0;
            text-align: center;
        }
        td:first-child { text-align: left; }
        tr:nth-child(even) { background: #fafafa; }
        tr:hover { background: #f5f5f5; }
        tr.row-danger { background: #fff0f0 !important; }
        tr.row-danger:hover { background: #ffe5e5 !important; }
        tr.row-warning { background: #fffbea !important; }
        tr.row-warning:hover { background: #fff3cc !important; }
        .badge {
            display: inline-block;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 10px;
            font-weight: 600;
            text-transform: uppercase;
        }
        .badge.success { background: #00c853; color: white; }
        .badge.warning { background: #b8860b; color: white; }
        .badge.danger { background: #ff1744; color: white; }
        .change {
            display: inline-flex;
            align-items: center;
            gap: 4px;
            font-size: 12px;
            font-weight: 600;
        }
        .change.positive { color: #00c853; }
        .change.negative { color: #ff1744; }
        .change.neutral { color: #666; }
        .alert {
            padding: 10px 12px;
            border-radius: 4px;
            margin-top: 10px;
            font-size: 12px;
        }
        .alert.warning {
            background: #fffbea;
            border-left: 3px solid #b8860b;
            color: #1E2426;
        }
        .alert.info {
            background: #f5f5f5;
            border-left: 3px solid #1E2426;
            color: #1E2426;
        }
        .footer {
            background: #1E2426;
            padding: 15px;
            text-align: center;
            color: #E7FF00;
            font-size: 12px;
        }
        .footer a {
            color: #E7FF00;
            text-decoration: none;
            font-weight: 600;
        }
        .footer a:hover { text-decoration: underline; }
        .chart-container {
            position: relative;
            height: 250px;
            margin: 15px 0;
        }
        .chart-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(450px, 1fr));
            gap: 20px;
            margin: 15px 0;
        }
        .chart-box {
            background: #fafafa;
            padding: 15px;
            border-radius: 4px;
            border: 1px solid #e0e0e0;
        }
        .chart-box h3 {
            color: #1E2426;
            font-size: 14px;
            margin-bottom: 10px;
            font-weight: 600;
        }

        /* Collapsible sections */
        .collapsible {
            cursor: pointer;
            user-select: none;
        }
        .collapsible:after {
            content: ' \\25BC';
            font-size: 10px;
            color: #b8860b;
            transition: transform 0.2s;
        }
        .collapsible.collapsed:after {
            content: ' \\25B6';
        }
        .collapsible-content {
            max-height: 5000px;
            overflow: hidden;
            transition: max-height 0.3s ease;
        }
        .collapsible-content.collapsed {
            max-height: 0;
        }

        /* Accordion status panels */
        .status-accordion {
            margin: 20px 0;
            display: flex;
            flex-direction: column;
            gap: 10px;
        }
        .accordion-panel {
            margin-bottom: 40px;
            border: 1px solid #d0d0d0;
            border-radius: 6px;
            overflow: hidden;
            box-shadow: 0 2px 6px rgba(0,0,0,0.07);
        }
        .accordion-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 14px 18px;
            background: #1E2426;
            color: #E7FF00;
            cursor: pointer;
            user-select: none;
            border-left: 4px solid #1E2426;
            transition: background 0.15s;
        }
        .accordion-header:hover { background: #2a3235; }
        .accordion-header h2 {
            font-size: 20px;
            font-weight: 700;
            color: #E7FF00;
            margin: 0;
        }
        .accordion-header .summary-pills {
            display: flex;
            gap: 8px;
            align-items: center;
            flex-wrap: wrap;
        }
        .accordion-header .pill {
            font-size: 11px;
            font-weight: 600;
            padding: 2px 8px;
            border-radius: 10px;
            background: white;
            border: 1px solid #e0e0e0;
            color: #555;
        }
        .accordion-header .pill.good { border-color: #00c853; color: #00c853; }
        .accordion-header .pill.warn { border-color: #b8860b; color: #b8860b; }
        .accordion-header .pill.bad { border-color: #ff1744; color: #ff1744; }
        .accordion-header .toggle-icon {
            font-size: 10px;
            color: #999;
            margin-left: 12px;
            transition: transform 0.2s;
        }
        .accordion-header.collapsed .toggle-icon { transform: rotate(-90deg); }
        .accordion-body {
            padding: 12px 16px;
            border-top: 1px solid #e0e0e0;
            max-height: 5000px;
            overflow: hidden;
            transition: max-height 0.3s ease, padding 0.3s ease;
        }
        .accordion-body.collapsed {
            max-height: 0;
            padding-top: 0;
            padding-bottom: 0;
            border-top: none;
        }
        .accordion-body table { margin-top: 0; }
        .sub-section {
            margin-top: 12px;
            padding-top: 10px;
            border-top: 1px dashed #e0e0e0;
        }
        .sub-section-header {
            font-size: 12px;
            font-weight: 600;
            color: #666;
            margin-bottom: 6px;
            cursor: pointer;
            user-select: none;
        }
        .sub-section-header:after {
            content: ' \\25BC';
            font-size: 9px;
            color: #b8860b;
        }
        .sub-section-header.collapsed:after { content: ' \\25B6'; }

        /* Health Dashboard */
        .health-dashboard {
            display: flex;
            justify-content: center;
            gap: 30px;
            flex-wrap: wrap;
            padding: 20px 0;
            margin-bottom: 20px;
        }
        .health-gauge {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 8px;
        }
        .health-gauge .gauge-label {
            font-size: 11px;
            font-weight: 600;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .health-gauge svg {
            width: 90px;
            height: 90px;
        }
        .health-gauge .gauge-value {
            font-size: 16px;
            font-weight: 700;
            fill: #1E2426;
        }
        .gauge-track { fill: none; stroke: #e0e0e0; stroke-width: 8; }
        .gauge-fill { fill: none; stroke-width: 8; stroke-linecap: round; transition: stroke-dashoffset 0.5s; }

        /* Changes strip */
        .changes-strip {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            padding: 12px 15px;
            background: #f8f9fa;
            border-radius: 4px;
            border: 1px solid #e0e0e0;
            margin-bottom: 20px;
        }
        .changes-strip .change-item {
            display: inline-flex;
            align-items: center;
            gap: 5px;
            font-size: 12px;
            font-weight: 500;
            padding: 4px 10px;
            border-radius: 20px;
            background: white;
            border: 1px solid #e0e0e0;
        }
        .change-item.up { border-color: #ff1744; color: #ff1744; }
        .change-item.down { border-color: #00c853; color: #00c853; }
        .change-item.down.bad { border-color: #ff1744; color: #ff1744; }
        .change-item.up.good { border-color: #00c853; color: #00c853; }
        .change-item.neutral { border-color: #999; color: #666; }

        /* Responsive */
        @media (max-width: 768px) {
            .status-accordion { gap: 4px; }
            .chart-grid { grid-template-columns: 1fr; }
            .health-dashboard { gap: 15px; }
            .health-gauge svg { width: 70px; height: 70px; }
            .sticky-nav { padding: 0 10px; }
            .sticky-nav a { padding: 6px 8px; font-size: 11px; }
            body { padding: 10px; padding-top: 50px; }
            .content { padding: 15px; }
        }

        /* Print styles */
        @media print {
            body { padding: 0; background: white; }
            .sticky-nav { display: none; }
            .container { box-shadow: none; border-radius: 0; }
            .header { background: white !important; color: #1E2426 !important; border-bottom: 2px solid #1E2426; }
            .header .timestamp { color: #666 !important; }
            .header h1 { color: #1E2426; }
            .footer { background: white !important; color: #1E2426 !important; border-top: 1px solid #ccc; }
            .footer a { color: #1E2426 !important; }
            .chart-grid { display: none; }
            .section { page-break-inside: avoid; }
            .status-accordion { gap: 4px; }
            .health-dashboard { page-break-inside: avoid; }
            .changes-strip { page-break-inside: avoid; }
            tr.row-danger { background: #fff0f0 !important; -webkit-print-color-adjust: exact; }
            tr.row-warning { background: #fffbea !important; -webkit-print-color-adjust: exact; }
            .badge { -webkit-print-color-adjust: exact; }
            th { -webkit-print-color-adjust: exact; }
        }
    </style>
</head>
<body>
    <nav class="sticky-nav">
        <span class="nav-brand">Health Check</span>
        <a href="#ai-summary">Summary</a>
        <a href="#health-dashboard">Dashboard</a>
        <a href="#trends">Trends</a>
        <a href="#scans">Scans</a>
        <a href="#assets">Assets</a>
        <a href="#agents">Agents</a>
        <a href="#scanners">Scanners</a>
        <a href="#connectors">Connectors</a>
        <a href="#users">Users</a>
    </nav>
    <div class="container">
        <div class="header">
            <h1>Tenable Health Check Report</h1>
            <div class="timestamp">Generated: ''' + self._escape(timestamp) + '''</div>
        </div>
        <div class="content">
''')

    def _add_health_dashboard(self, data: dict[str, Any], historical_data: dict[str, Any] | None) -> None:
        assets = data.get('assets', {})
        agents = data.get('agents', {})
        scanners = data.get('scanners', {})

        licensed_assets = assets.get('licensed_assets', 0)
        auth_succeeded = assets.get('auth_succeeded', 0)
        auth_pct = (auth_succeeded / licensed_assets * 100) if licensed_assets > 0 else 0

        total_agents = agents.get('total_agents', 0)
        online_agents = agents.get('online_agents', 0)
        agent_pct = (online_agents / total_agents * 100) if total_agents > 0 else 100

        total_scanners = scanners.get('total_scanners', 0)
        working_scanners = scanners.get('working_scanners', 0)
        scanner_pct = (working_scanners / total_scanners * 100) if total_scanners > 0 else 100

        total_assets = assets.get('total_assets', 0)
        licensed_pct = (licensed_assets / total_assets * 100) if total_assets > 0 else 0

        gauges = [
            ('Auth Success', auth_pct,
             f'Assets with successful authentication / licensed assets ({auth_succeeded} / {licensed_assets})'),
            ('Agents Online', agent_pct,
             f'Online agents / total agents ({online_agents} / {total_agents})'),
            ('Scanners OK', scanner_pct,
             f'Working scanners / total managed scanners ({working_scanners} / {total_scanners})'),
            ('Licensed Assets', licensed_pct,
             f'Assets scanned in past 90 days / total assets ({licensed_assets} / {total_assets})'),
        ]

        self.html_parts.append('<div id="health-dashboard" class="health-dashboard">')
        for label, pct, tooltip in gauges:
            pct_clamped = max(0, min(100, pct))
            circumference = 2 * 3.14159 * 35
            offset = circumference * (1 - pct_clamped / 100)
            if pct_clamped >= 90:
                color = '#00c853'
            elif pct_clamped >= 70:
                color = '#b8860b'
            else:
                color = '#ff1744'
            self.html_parts.append(f'''
            <div class="health-gauge">
                <span class="gauge-label">{self._escape(label)}</span>
                <svg viewBox="0 0 80 80">
                    <circle class="gauge-track" cx="40" cy="40" r="35" />
                    <circle class="gauge-fill" cx="40" cy="40" r="35"
                        stroke="{color}"
                        stroke-dasharray="{circumference:.1f}"
                        stroke-dashoffset="{offset:.1f}"
                        transform="rotate(-90 40 40)" />
                    <text class="gauge-value" x="40" y="44" text-anchor="middle">{pct_clamped:.0f}%</text>
                </svg>
            </div>''')
        self.html_parts.append('</div>')

        self.html_parts.append(f'''
        <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 4px 20px; padding: 8px 0; margin-bottom: 15px; font-size: 11px; color: #888;">
            <span><strong style="color:#555;">Auth Success</strong> = auth succeeded / licensed assets ({auth_succeeded} / {licensed_assets})</span>
            <span><strong style="color:#555;">Agents Online</strong> = online agents / total agents ({online_agents} / {total_agents})</span>
            <span><strong style="color:#555;">Scanners OK</strong> = working / total managed scanners ({working_scanners} / {total_scanners})</span>
            <span><strong style="color:#555;">Licensed Assets</strong> = scanned in 90d / total assets ({licensed_assets} / {total_assets})</span>
        </div>''')

    def _add_changes_strip(self, data: dict[str, Any], historical_data: dict[str, Any] | None) -> None:
        if not historical_data:
            return

        changes: list[str] = []

        agents_7d = historical_data.get('agents', {}).get('7_days')
        if agents_7d:
            prev_offline = agents_7d.get('offline_agents', 0)
            curr_offline = data.get('agents', {}).get('offline_agents', 0)
            diff = curr_offline - prev_offline
            if diff > 0:
                changes.append(f'<span class="change-item up">+{diff} agents offline since last week</span>')
            elif diff < 0:
                changes.append(f'<span class="change-item down up good">{diff} agents offline (improving)</span>')

        auth_7d = historical_data.get('authentication', {}).get('7_days')
        if auth_7d:
            prev_auth = auth_7d.get('auth_succeeded_pct', 0)
            curr_auth = data.get('assets', {}).get('auth_succeeded_percentage', 0)
            diff = curr_auth - prev_auth
            if abs(diff) >= 1:
                cls = 'down bad' if diff < 0 else 'up good'
                changes.append(f'<span class="change-item {cls}">Auth success {diff:+.1f}%</span>')

        scanners_7d = historical_data.get('scanners', {}).get('7_days')
        if scanners_7d:
            prev_problems = scanners_7d.get('problem_scanners', 0)
            curr_problems = data.get('scanners', {}).get('problem_scanners', 0)
            diff = curr_problems - prev_problems
            if diff > 0:
                changes.append(f'<span class="change-item up">+{diff} new problem scanner(s)</span>')
            elif diff < 0:
                changes.append(f'<span class="change-item up good">{abs(diff)} scanner(s) recovered</span>')

        license_7d = historical_data.get('license', {}).get('7_days')
        if license_7d:
            prev_licensed = license_7d.get('total_licensed_assets', 0)
            curr_licensed = data.get('assets', {}).get('licensed_assets', 0)
            diff = curr_licensed - prev_licensed
            if abs(diff) >= 10:
                cls = 'neutral'
                changes.append(f'<span class="change-item {cls}">License count {diff:+d}</span>')

        if changes:
            self.html_parts.append('<div class="changes-strip">')
            self.html_parts.append('<strong style="font-size: 11px; color: #666; align-self: center;">CHANGES (7d):</strong>')
            self.html_parts.append(' '.join(changes))
            self.html_parts.append('</div>')

    def _add_claude_section(self, claude_analysis: dict[str, Any]) -> None:
        status = claude_analysis.get('health_status', 'unknown').upper()
        status_colors = {
            'HEALTHY': '#00c853',
            'WARNING': '#b8860b',
            'CRITICAL': '#ff1744',
            'UNKNOWN': '#666',
        }
        status_color = status_colors.get(status, '#666')
        status_emojis = {'HEALTHY': '&#10003;', 'WARNING': '&#9888;', 'CRITICAL': '&#128680;', 'UNKNOWN': '?'}
        status_emoji = status_emojis.get(status, '?')

        self.html_parts.append(f'''
            <div id="ai-summary" class="section" style="background: #fafafa; padding: 15px; border-radius: 4px; border-left: 4px solid {status_color};">
                <h2 style="margin-bottom: 12px;">AI Executive Summary</h2>
                <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 15px; background: white; padding: 12px; border-radius: 4px; border: 2px solid {status_color};">
                    <div style="font-size: 32px;">{status_emoji}</div>
                    <div>
                        <div style="font-size: 10px; color: #666; text-transform: uppercase; letter-spacing: 0.5px;">Overall Health Status</div>
                        <div style="font-size: 20px; font-weight: bold; color: {status_color};">{self._escape(status)}</div>
                    </div>
                </div>
''')

        if claude_analysis.get('executive_summary'):
            summary = self._escape(claude_analysis['executive_summary']).replace('\n', '<br>')
            self.html_parts.append(f'''
                <div style="background: white; padding: 12px; border-radius: 4px; margin-bottom: 10px; border-left: 3px solid #1E2426;">
                    <h3 style="color: #1E2426; font-size: 13px; margin-bottom: 8px; font-weight: 600;">Summary</h3>
                    <p style="line-height: 1.6; color: #333; font-size: 13px;">{summary}</p>
                </div>
''')

        if claude_analysis.get('key_concerns'):
            self.html_parts.append('''
                <div style="background: white; padding: 12px; border-radius: 4px; margin-bottom: 10px; border-left: 3px solid #ff1744;">
                    <h3 style="color: #ff1744; font-size: 13px; margin-bottom: 8px; font-weight: 600;">Key Concerns</h3>
                    <ul style="margin-left: 18px; line-height: 1.6; font-size: 13px;">
''')
            for concern in claude_analysis['key_concerns']:
                self.html_parts.append(f'                        <li style="color: #333; margin-bottom: 4px;">{self._escape(concern)}</li>')
            self.html_parts.append('''
                    </ul>
                </div>
''')

        if claude_analysis.get('recommendations'):
            self.html_parts.append('''
                <div style="background: white; padding: 12px; border-radius: 4px; margin-bottom: 10px; border-left: 3px solid #b8860b;">
                    <h3 style="color: #1E2426; font-size: 13px; margin-bottom: 8px; font-weight: 600;">Recommendations</h3>
''')
            for rec in claude_analysis['recommendations']:
                priority = rec.get('priority', 'medium').upper()
                priority_colors = {'HIGH': '#ff1744', 'MEDIUM': '#b8860b', 'LOW': '#1E2426'}
                priority_color = priority_colors.get(priority, '#666')
                issue = self._escape(rec.get('issue', 'N/A'))
                action = self._escape(rec.get('action', 'N/A'))

                self.html_parts.append(f'''
                    <div style="margin-bottom: 8px; padding: 10px; background: #fafafa; border-radius: 4px; border-left: 3px solid {priority_color};">
                        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px;">
                            <span style="background: {priority_color}; color: white; padding: 2px 6px; border-radius: 3px; font-size: 10px; font-weight: bold;">{priority}</span>
                            <strong style="color: #1E2426; font-size: 12px;">{issue}</strong>
                        </div>
                        <div style="color: #666; padding-left: 8px; border-left: 2px solid #e0e0e0; font-size: 12px;">
                            &rarr; {action}
                        </div>
                    </div>
''')
            self.html_parts.append('''
                </div>
''')

        if claude_analysis.get('trends'):
            self.html_parts.append('''
                <div style="background: white; padding: 12px; border-radius: 4px; border-left: 3px solid #1E2426;">
                    <h3 style="color: #1E2426; font-size: 13px; margin-bottom: 8px; font-weight: 600;">Trends to Monitor</h3>
                    <ul style="margin-left: 18px; line-height: 1.6; font-size: 13px;">
''')
            for trend in claude_analysis['trends']:
                self.html_parts.append(f'                        <li style="color: #333; margin-bottom: 4px;">{self._escape(trend)}</li>')
            self.html_parts.append('''
                    </ul>
                </div>
''')

        self.html_parts.append('            </div>')

    def _add_scan_section(self, scan_data: dict[str, Any], analysis: dict[str, Any]) -> None:
        days_back = scan_data.get('days_back', 7)
        scan_summary = scan_data.get('scan_summary', {})
        inactive_scans = scan_data.get('inactive_scans', 0)

        agent_scans = {name: details for name, details in scan_summary.items()
                       if details.get('scan_type') in [None, 'agent']}
        network_scans = {name: details for name, details in scan_summary.items()
                         if details.get('scan_type') not in [None, 'agent']}

        total_scans = len(scan_summary)
        network_count = len(network_scans)
        agent_count = len(agent_scans)

        def render_scan_table_html(scans_dict: dict, is_agent_table: bool = False) -> str:
            if not scans_dict:
                return ''
            parts: list[str] = []
            sorted_scans = sorted(scans_dict.items(), key=lambda x: x[1]['total_runs'], reverse=True)

            if is_agent_table:
                headers = '<th>Scan Name</th><th>Policy</th><th>Launch Type</th>'
            else:
                headers = '<th>Scan Name</th><th>Policy</th><th>Running</th><th>Completed</th><th>Incomplete</th><th>Success Rate</th>'

            parts.append(f'<table><thead><tr>{headers}</tr></thead><tbody>')
            for scan_name, details in sorted_scans:
                total_runs = details['total_runs']
                successful_runs = details.get('completed_runs', details.get('success_runs', 0))
                failed_runs = details['failed_runs']
                stopped_runs = details.get('stopped_runs', 0)
                disabled_runs = details.get('disabled_runs', 0)
                canceled_runs = details.get('canceled_runs', 0)
                paused_runs = details.get('paused_runs', 0)
                running_count = details.get('running_count', 0)
                policy_name = details.get('policy', 'N/A')

                total_stopped = stopped_runs + disabled_runs + canceled_runs + paused_runs
                total_incomplete = total_stopped + failed_runs

                completed_runs_calc = total_runs - running_count
                success_rate = (successful_runs / completed_runs_calc * 100) if completed_runs_calc > 0 else 0

                if is_agent_table:
                    launch_type = details.get('agent_scan_launch_type') or 'scheduled'
                    parts.append(f'<tr><td>{self._escape(scan_name)}</td><td>{self._escape(policy_name) if policy_name else "N/A"}</td><td>{self._escape(launch_type)}</td></tr>')
                else:
                    row_class = ''
                    if success_rate < 80:
                        row_class = ' class="row-danger"'
                    elif success_rate < 95:
                        row_class = ' class="row-warning"'
                    parts.append(f'<tr{row_class}><td>{self._escape(scan_name)}</td><td>{self._escape(policy_name) if policy_name else "N/A"}</td><td>{running_count}</td><td>{successful_runs}</td><td>{total_incomplete}</td><td>{success_rate:.1f}%</td></tr>')
            parts.append('</tbody></table>')
            return '\n'.join(parts)

        # Build accordion body content
        body_parts: list[str] = []

        if network_scans:
            net_html = render_scan_table_html(network_scans, is_agent_table=False)
            body_parts.append(f'''
                    <div class="sub-section" style="padding-top:0; border-top:none; margin-top:0;">
                        <div class="sub-section-header" onclick="toggleSubSection(this)">Network Scans (Past {days_back} Days)</div>
                        <div class="collapsible-content">
                            {net_html}''')
            if inactive_scans > 0:
                body_parts.append(f'''
                            <div style="margin-top: 10px; padding: 10px; background: #f9f9f9; border-left: 3px solid #666; font-size: 13px;">
                                <strong>{inactive_scans}</strong> additional scan(s) are configured but have not launched in the past {days_back} days
                            </div>''')
            body_parts.append('</div></div>')

        if agent_scans:
            enabled_agent_scans = {name: details for name, details in agent_scans.items() if details.get('is_enabled', True)}
            disabled_agent_scans = {name: details for name, details in agent_scans.items() if not details.get('is_enabled', True)}

            if enabled_agent_scans:
                ena_html = render_scan_table_html(enabled_agent_scans, is_agent_table=True)
                body_parts.append(f'''
                    <div class="sub-section">
                        <div class="sub-section-header" onclick="toggleSubSection(this)">Agent Scans — Enabled</div>
                        <div class="collapsible-content">{ena_html}</div>
                    </div>''')
            if disabled_agent_scans:
                dis_html = render_scan_table_html(disabled_agent_scans, is_agent_table=True)
                body_parts.append(f'''
                    <div class="sub-section">
                        <div class="sub-section-header" onclick="toggleSubSection(this)">Agent Scans — Disabled</div>
                        <div class="collapsible-content">{dis_html}</div>
                    </div>''')

        pills = f'<span class="pill">{total_scans} total</span>'
        if network_count:
            pills += f'<span class="pill">{network_count} network</span>'
        if agent_count:
            pills += f'<span class="pill">{agent_count} agent</span>'

        self.html_parts.append(f'''
            <div id="scans" class="accordion-panel">
                <div class="accordion-header" onclick="toggleAccordion(this)">
                    <h2>Scans</h2>
                    <div class="summary-pills">
                        {pills}
                        <span class="toggle-icon">&#9660;</span>
                    </div>
                </div>
                <div class="accordion-body">
                    {"".join(body_parts) if body_parts else "<p style='color:#888;font-size:13px;'>No scan data available.</p>"}
                </div>
            </div>
''')

    def _add_asset_section(self, asset_data: dict[str, Any], analysis: dict[str, Any], license_analysis: dict[str, Any], historical_data: dict[str, Any] | None = None) -> None:
        total = asset_data.get('total_assets', 0)
        licensed = asset_data.get('licensed_assets', 0)
        unlicensed = asset_data.get('unlicensed_assets', 0)
        auth_succeeded = asset_data.get('auth_succeeded', 0)
        auth_not_attempted = asset_data.get('auth_not_attempted', 0)
        auth_failed = asset_data.get('auth_failed', 0)
        success_pct = asset_data.get('auth_succeeded_percentage', 0)

        license_7d = historical_data.get('license', {}).get('7_days') if historical_data else None
        license_30d = historical_data.get('license', {}).get('30_days') if historical_data else None
        auth_7d = historical_data.get('authentication', {}).get('7_days') if historical_data else None
        auth_30d = historical_data.get('authentication', {}).get('30_days') if historical_data else None

        license_table = self._render_comparison_table(
            "Assets & Licensing",
            [
                {"label": "Licensed (90d)", "current": licensed, "key": "total_licensed_assets"},
                {"label": "Unlicensed", "current": unlicensed, "key": "unlicensed_assets"},
            ],
            license_7d, license_30d,
            total_row={"label": "Total Assets", "current": total, "key": "total_assets"},
        )
        auth_table = self._render_comparison_table(
            "Authentication",
            [
                {"label": "Auth Not Attempted", "current": auth_not_attempted, "key": "auth_not_attempted"},
                {"label": "Auth Failed", "current": auth_failed, "key": "auth_failed"},
                {"label": "Auth Succeeded", "current": auth_succeeded, "key": "auth_succeeded"},
                {"label": "Auth Succeeded %", "current": f"{success_pct:.1f}", "key": "auth_succeeded_pct", "suffix": "%"},
            ],
            auth_7d, auth_30d,
        )

        auth_pill_cls = 'good' if success_pct >= 70 else ('warn' if success_pct >= 40 else 'bad')
        self.html_parts.append(f'''
            <div id="assets" class="accordion-panel">
                <div class="accordion-header" onclick="toggleAccordion(this)">
                    <h2>Assets &amp; Licensing</h2>
                    <div class="summary-pills">
                        <span class="pill">{licensed} licensed</span>
                        <span class="pill {auth_pill_cls}">Auth {success_pct:.0f}%</span>
                        <span class="toggle-icon">&#9660;</span>
                    </div>
                </div>
                <div class="accordion-body">
                    {license_table}
                    <div class="sub-section">
                        <div class="sub-section-header" onclick="toggleSubSection(this)">Authentication</div>
                        <div class="collapsible-content">
                            {auth_table}
                        </div>
                    </div>
                </div>
            </div>
''')

    def _add_agent_section(self, agent_data: dict[str, Any], analysis: dict[str, Any], historical_data: dict[str, Any] | None = None) -> None:
        total = agent_data.get('total_agents', 0)
        online = agent_data.get('online_agents', 0)
        offline = agent_data.get('offline_agents', 0)
        long_offline = agent_data.get('long_offline_agents', 0)
        threshold_days = agent_data.get('offline_threshold_days', 14)

        agents_7d = historical_data.get('agents', {}).get('7_days') if historical_data else None
        agents_30d = historical_data.get('agents', {}).get('30_days') if historical_data else None

        table_html = self._render_comparison_table(
            "Agents",
            [
                {"label": "Online", "current": online, "key": "online_agents"},
                {"label": "Offline", "current": offline, "key": "offline_agents"},
                {"label": f"Offline > {threshold_days} days", "current": long_offline, "key": "long_offline_agents"},
            ],
            agents_7d, agents_30d,
            total_row={"label": "Total Agents", "current": total, "key": "total_agents"},
        )

        online_cls = 'good' if offline == 0 else ('warn' if offline <= 2 else 'bad')
        self.html_parts.append(f'''
            <div id="agents" class="accordion-panel">
                <div class="accordion-header" onclick="toggleAccordion(this)">
                    <h2>Agents</h2>
                    <div class="summary-pills">
                        <span class="pill {online_cls}">{online} online</span>
                        <span class="pill{" bad" if offline > 0 else ""}">{offline} offline</span>
                        <span class="toggle-icon">&#9660;</span>
                    </div>
                </div>
                <div class="accordion-body">
                    {table_html}
''')

        health_states = agent_data.get('health_states', {})
        if health_states:
            self.html_parts.append('''<div class="sub-section">
                <div class="sub-section-header" onclick="toggleSubSection(this)">Health State Distribution</div>
                <div class="collapsible-content">
                <table>
                    <thead><tr><th>Health State</th><th style="text-align:center;">Count</th></tr></thead>
                    <tbody>''')
            for state, count in sorted(health_states.items(), key=lambda x: x[1], reverse=True):
                self.html_parts.append(f'<tr><td>{self._escape(state)}</td><td style="text-align:center;">{count}</td></tr>')
            self.html_parts.append('</tbody></table></div></div>')

        core_versions = agent_data.get('core_versions', {})
        if core_versions:
            self.html_parts.append('''<div class="sub-section">
                <div class="sub-section-header" onclick="toggleSubSection(this)">Agent Versions</div>
                <div class="collapsible-content">
                <table>
                    <thead><tr><th>Core Version</th><th style="text-align:center;">Count</th></tr></thead>
                    <tbody>''')
            for version, count in sorted(core_versions.items(), key=lambda x: x[1], reverse=True):
                self.html_parts.append(f'<tr><td>{self._escape(version)}</td><td style="text-align:center;">{count}</td></tr>')
            self.html_parts.append('</tbody></table></div></div>')

        profiles = agent_data.get('profiles', {})
        if profiles:
            self.html_parts.append('''<div class="sub-section">
                <div class="sub-section-header" onclick="toggleSubSection(this)">Agent Profiles</div>
                <div class="collapsible-content">
                <table>
                    <thead><tr><th>Profile Name</th><th style="text-align:center;">Count</th></tr></thead>
                    <tbody>''')
            for profile, count in sorted(profiles.items(), key=lambda x: x[1], reverse=True):
                self.html_parts.append(f'<tr><td>{self._escape(profile)}</td><td style="text-align:center;">{count}</td></tr>')
            self.html_parts.append('</tbody></table></div></div>')

        plugin_feed_ids = agent_data.get('plugin_feed_ids', {})
        if plugin_feed_ids:
            cutoff = datetime.now(timezone.utc) - timedelta(days=7)
            recent: dict[str, int] = {}
            older_count = 0
            for feed_id, count in plugin_feed_ids.items():
                is_recent = False
                if feed_id != 'unknown' and len(feed_id) >= 12:
                    try:
                        feed_dt = datetime.strptime(feed_id[:12], '%Y%m%d%H%M').replace(tzinfo=timezone.utc)
                        is_recent = feed_dt >= cutoff
                    except ValueError:
                        pass
                if is_recent:
                    recent[feed_id] = count
                else:
                    older_count += count
            self.html_parts.append('''<div class="sub-section">
                <div class="sub-section-header" onclick="toggleSubSection(this)">Plugin Feed IDs</div>
                <div class="collapsible-content">
                <table>
                    <thead><tr><th>Plugin Feed ID</th><th style="text-align:center;">Count</th></tr></thead>
                    <tbody>''')
            for feed_id, count in sorted(recent.items(), reverse=True):
                self.html_parts.append(f'<tr><td>{self._escape(feed_id)}</td><td style="text-align:center;">{count}</td></tr>')
            if older_count > 0:
                self.html_parts.append(f'<tr><td><em>older than seven days</em></td><td style="text-align:center;">{older_count}</td></tr>')
            self.html_parts.append('</tbody></table></div></div>')

        if agent_data.get('long_offline_agent_list'):
            self.html_parts.append(f'''<div class="sub-section">
                <div class="sub-section-header" onclick="toggleSubSection(this)">Long-Term Offline (&gt;{threshold_days} days)</div>
                <div class="collapsible-content">
                <table>
                    <thead><tr><th>Agent Name</th><th>Status</th><th>Last Connect</th></tr></thead>
                    <tbody>''')
            for agent in agent_data['long_offline_agent_list']:
                last_connect = datetime.fromtimestamp(agent['last_connect']).strftime('%Y-%m-%d') if agent.get('last_connect') else 'Never'
                self.html_parts.append(f'<tr><td>{self._escape(agent["name"])}</td><td><span class="badge danger">{self._escape(agent["status"])}</span></td><td>{last_connect}</td></tr>')
            self.html_parts.append('</tbody></table></div></div>')

        self.html_parts.append('</div></div>')

    def _add_scanner_section(self, scanner_data: dict[str, Any], analysis: dict[str, Any], historical_data: dict[str, Any] | None = None) -> None:
        total = scanner_data.get('total_scanners', 0)
        working = scanner_data.get('working_scanners', 0)
        problems = scanner_data.get('problem_scanners', 0)

        scanners_7d = historical_data.get('scanners', {}).get('7_days') if historical_data else None
        scanners_30d = historical_data.get('scanners', {}).get('30_days') if historical_data else None

        table_html = self._render_comparison_table(
            "Scanners",
            [
                {"label": "Working", "current": working, "key": "working_scanners"},
                {"label": "Problems", "current": problems, "key": "problem_scanners"},
            ],
            scanners_7d, scanners_30d,
            total_row={"label": "Total Scanners", "current": total, "key": "total_scanners"},
        )

        scanner_cls = 'good' if problems == 0 else 'bad'
        self.html_parts.append(f'''
            <div id="scanners" class="accordion-panel">
                <div class="accordion-header" onclick="toggleAccordion(this)">
                    <h2>Scanners</h2>
                    <div class="summary-pills">
                        <span class="pill {scanner_cls}">{working} working</span>
                        {"<span class='pill bad'>" + str(problems) + " problem(s)</span>" if problems > 0 else ""}
                        <span class="toggle-icon">&#9660;</span>
                    </div>
                </div>
                <div class="accordion-body">
                    {table_html}
''')

        if scanner_data.get('problem_scanner_list'):
            self.html_parts.append('''<div class="sub-section">
                <div class="sub-section-header" onclick="toggleSubSection(this)">Problem Scanner Details</div>
                <div class="collapsible-content">
                <table>
                    <thead><tr><th>Scanner Name</th><th>Status</th><th>Type</th><th>Scans</th></tr></thead>
                    <tbody>''')
            for scanner in scanner_data['problem_scanner_list']:
                self.html_parts.append(f'<tr><td>{self._escape(scanner["name"])}</td><td><span class="badge danger">{self._escape(scanner["status"])}</span></td><td>{self._escape(scanner.get("type", "N/A"))}</td><td>{scanner.get("scan_count", 0)}</td></tr>')
            self.html_parts.append('</tbody></table></div></div>')

        if analysis.get('has_previous_data'):
            new_problems = analysis.get('new_problem_scanners', [])
            recovered = analysis.get('recovered_scanners', [])
            if new_problems or recovered:
                self.html_parts.append('<div class="alert warning" style="margin-top:10px;">')
                if new_problems:
                    self.html_parts.append(f'<strong>&#9888; NEW problem scanners:</strong> {len(new_problems)}<br>')
                if recovered:
                    self.html_parts.append(f'<strong>&#10003; Recovered scanners:</strong> {len(recovered)}')
                self.html_parts.append('</div>')

        self.html_parts.append('</div></div>')

    def _add_connector_section(self, connector_data: dict[str, Any], analysis: dict[str, Any], historical_data: dict[str, Any] | None = None) -> None:
        total = connector_data.get('total_connectors', 0)
        working = connector_data.get('working_connectors', 0)
        problems = connector_data.get('problem_connectors', 0)

        connectors_7d = historical_data.get('connectors', {}).get('7_days') if historical_data else None
        connectors_30d = historical_data.get('connectors', {}).get('30_days') if historical_data else None

        table_html = self._render_comparison_table(
            "Connectors",
            [
                {"label": "Working", "current": working, "key": "working_connectors"},
                {"label": "Problems", "current": problems, "key": "problem_connectors"},
            ],
            connectors_7d, connectors_30d,
            total_row={"label": "Total Connectors", "current": total, "key": "total_connectors"},
        )

        conn_cls = 'good' if problems == 0 else 'bad'
        self.html_parts.append(f'''
            <div id="connectors" class="accordion-panel">
                <div class="accordion-header" onclick="toggleAccordion(this)">
                    <h2>Connectors</h2>
                    <div class="summary-pills">
                        <span class="pill {conn_cls}">{working} working</span>
                        {"<span class='pill bad'>" + str(problems) + " problem(s)</span>" if problems > 0 else ""}
                        <span class="toggle-icon">&#9660;</span>
                    </div>
                </div>
                <div class="accordion-body">
                    {table_html}
                </div>
            </div>
''')

    def _add_user_section(self, user_data: dict[str, Any], analysis: dict[str, Any], historical_data: dict[str, Any] | None = None) -> None:
        total = user_data.get('total_users', 0)
        enabled = user_data.get('enabled_users', 0)
        disabled = user_data.get('disabled_users', 0)
        no_login = user_data.get('enabled_no_login_30_days', 0)
        role_counts = user_data.get('role_counts', {})
        no_login_list = user_data.get('enabled_no_login_list', [])

        users_7d = historical_data.get('users', {}).get('7_days') if historical_data else None
        users_30d = historical_data.get('users', {}).get('30_days') if historical_data else None

        table_html = self._render_comparison_table(
            "Users",
            [
                {"label": "Enabled Users", "current": enabled, "key": "enabled_users"},
                {"label": "Disabled Users", "current": disabled, "key": "disabled_users"},
                {"label": "No Login 30+ Days", "current": no_login, "key": "enabled_no_login_30_days"},
            ],
            users_7d, users_30d,
            total_row={"label": "Total Users", "current": total, "key": "total_users"},
        )

        no_login_cls = ' warn' if no_login > 0 else ''
        self.html_parts.append(f'''
            <div id="users" class="accordion-panel">
                <div class="accordion-header" onclick="toggleAccordion(this)">
                    <h2>User Accounts</h2>
                    <div class="summary-pills">
                        <span class="pill">{enabled} enabled</span>
                        <span class="pill{no_login_cls}">{no_login} inactive 30d</span>
                        <span class="toggle-icon">&#9660;</span>
                    </div>
                </div>
                <div class="accordion-body">
                    {table_html}
''')

        if role_counts:
            self.html_parts.append('''<div class="sub-section">
                <div class="sub-section-header" onclick="toggleSubSection(this)">Users by Role</div>
                <div class="collapsible-content">
                <table>
                    <thead><tr><th>Role</th><th style="text-align:center;">Count</th></tr></thead>
                    <tbody>''')
            for role, count in sorted(role_counts.items(), key=lambda x: x[1], reverse=True):
                self.html_parts.append(f'<tr><td>{self._escape(role)}</td><td style="text-align:center;">{count}</td></tr>')
            self.html_parts.append('</tbody></table></div></div>')

        if no_login_list:
            limited_list = no_login_list[:10]
            self.html_parts.append('''<div class="sub-section">
                <div class="sub-section-header" onclick="toggleSubSection(this)">No Login in 30+ Days (Top 10)</div>
                <div class="collapsible-content">
                <table>
                    <thead><tr><th>Username</th><th>Name</th><th style="text-align:center;">Last Login</th></tr></thead>
                    <tbody>''')
            for user in limited_list:
                self.html_parts.append(f'<tr><td>{self._escape(user["username"])}</td><td>{self._escape(user["name"])}</td><td style="text-align:center;">{self._escape(user["last_login"])}</td></tr>')
            self.html_parts.append('</tbody></table>')
            if len(no_login_list) > 10:
                self.html_parts.append(f'<div style="margin-top:6px;font-size:12px;color:#666;">... and {len(no_login_list) - 10} more users</div>')
            self.html_parts.append('</div></div>')

        self.html_parts.append('</div></div>')

    def _add_trends_section(self, trends_data: dict[str, Any]) -> None:
        auth_data = trends_data.get('authentication', [])
        if len(auth_data) < 2:
            return

        self.html_parts.append('''
            <div id="trends" class="section">
                <h2>Historical Trends</h2>
                <div class="chart-grid">
                    <div class="chart-box">
                        <h3>Authentication Success Rate Over Time</h3>
                        <div class="chart-container">
                            <canvas id="authChart"></canvas>
                        </div>
                    </div>
                    <div class="chart-box">
                        <h3>License Usage Over Time</h3>
                        <div class="chart-container">
                            <canvas id="licenseChart"></canvas>
                        </div>
                    </div>
                    <div class="chart-box">
                        <h3>Agent Status Over Time</h3>
                        <div class="chart-container">
                            <canvas id="agentChart"></canvas>
                        </div>
                    </div>
                    <div class="chart-box">
                        <h3>Scanner Status Over Time</h3>
                        <div class="chart-container">
                            <canvas id="scannerChart"></canvas>
                        </div>
                    </div>
                </div>
            </div>

            <script>
                const trendsData = ''' + json.dumps(trends_data) + ''';

                function formatDate(timestamp) {
                    const date = new Date(timestamp);
                    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
                }

                function fillLast30Days(data, valueKeys) {
                    if (!data || data.length === 0) return { labels: [], datasets: {}, isReal: [] };

                    const today = new Date();
                    today.setHours(0, 0, 0, 0);
                    const thirtyDaysAgo = new Date(today);
                    thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);

                    const dataMap = {};
                    data.forEach(point => {
                        const date = new Date(point.timestamp);
                        date.setHours(0, 0, 0, 0);
                        const dateKey = date.toISOString().split('T')[0];
                        dataMap[dateKey] = point;
                    });

                    const labels = [];
                    const datasets = {};
                    const isReal = [];
                    valueKeys.forEach(key => datasets[key] = []);

                    let lastValues = {};
                    valueKeys.forEach(key => lastValues[key] = 0);

                    for (let i = 0; i <= 30; i++) {
                        const currentDate = new Date(thirtyDaysAgo);
                        currentDate.setDate(currentDate.getDate() + i);
                        const dateKey = currentDate.toISOString().split('T')[0];

                        labels.push(formatDate(currentDate.toISOString()));

                        if (dataMap[dateKey]) {
                            isReal.push(true);
                            valueKeys.forEach(key => {
                                const value = dataMap[dateKey][key] || 0;
                                datasets[key].push(value);
                                lastValues[key] = value;
                            });
                        } else {
                            isReal.push(false);
                            valueKeys.forEach(key => {
                                datasets[key].push(lastValues[key]);
                            });
                        }
                    }

                    return { labels, datasets, isReal };
                }

                Chart.defaults.font.family = "'Work Sans', sans-serif";
                Chart.defaults.font.size = 11;

                // Authentication Success Rate Chart
                const authDataRaw = trendsData.authentication || [];
                const authFilled = fillLast30Days(authDataRaw, ['auth_succeeded_pct']);
                const authPointStyles = authFilled.isReal.map(r => r ? 'circle' : 'crossRot');
                const authPointRadii = authFilled.isReal.map(r => r ? 4 : 3);
                new Chart(document.getElementById('authChart'), {
                    type: 'line',
                    data: {
                        labels: authFilled.labels,
                        datasets: [{
                            label: 'Authentication Success %',
                            data: authFilled.datasets.auth_succeeded_pct,
                            borderColor: '#1E2426',
                            backgroundColor: 'rgba(30, 36, 38, 0.1)',
                            tension: 0.3,
                            fill: true,
                            borderWidth: 2,
                            pointBackgroundColor: authFilled.isReal.map(r => r ? '#E7FF00' : 'transparent'),
                            pointBorderColor: authFilled.isReal.map(r => r ? '#1E2426' : '#ccc'),
                            pointStyle: authPointStyles,
                            pointRadius: authPointRadii
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: { display: false },
                            tooltip: { callbacks: { label: ctx => ctx.parsed.y.toFixed(1) + '%' } }
                        },
                        scales: {
                            y: { beginAtZero: true, max: 100, ticks: { callback: v => v + '%' }, grid: { color: '#e0e0e0' } },
                            x: { grid: { display: false } }
                        }
                    }
                });

                // License Usage Chart
                const licenseDataRaw = trendsData.license || [];
                const licenseFilled = fillLast30Days(licenseDataRaw, ['total_licensed_assets']);
                const licPointStyles = licenseFilled.isReal.map(r => r ? 'circle' : 'crossRot');
                const licPointRadii = licenseFilled.isReal.map(r => r ? 4 : 3);
                new Chart(document.getElementById('licenseChart'), {
                    type: 'line',
                    data: {
                        labels: licenseFilled.labels,
                        datasets: [{
                            label: 'Licensed Assets',
                            data: licenseFilled.datasets.total_licensed_assets,
                            borderColor: '#1E2426',
                            backgroundColor: 'rgba(30, 36, 38, 0.1)',
                            tension: 0.3,
                            fill: true,
                            borderWidth: 2,
                            pointBackgroundColor: licenseFilled.isReal.map(r => r ? '#E7FF00' : 'transparent'),
                            pointBorderColor: licenseFilled.isReal.map(r => r ? '#1E2426' : '#ccc'),
                            pointStyle: licPointStyles,
                            pointRadius: licPointRadii
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: { display: false },
                            tooltip: { callbacks: { label: ctx => ctx.parsed.y.toLocaleString() + ' assets' } }
                        },
                        scales: {
                            y: { beginAtZero: true, grid: { color: '#e0e0e0' } },
                            x: { grid: { display: false } }
                        }
                    }
                });

                // Agent Status Chart
                const agentDataRaw = trendsData.agents || [];
                const agentFilled = fillLast30Days(agentDataRaw, ['online_agents', 'offline_agents']);
                new Chart(document.getElementById('agentChart'), {
                    type: 'line',
                    data: {
                        labels: agentFilled.labels,
                        datasets: [
                            {
                                label: 'Online Agents',
                                data: agentFilled.datasets.online_agents,
                                borderColor: '#1E2426',
                                backgroundColor: 'rgba(30, 36, 38, 0.1)',
                                tension: 0.3,
                                borderWidth: 2,
                                pointBackgroundColor: agentFilled.isReal.map(r => r ? '#1E2426' : 'transparent'),
                                pointBorderColor: agentFilled.isReal.map(r => r ? '#1E2426' : '#ccc'),
                                pointStyle: agentFilled.isReal.map(r => r ? 'circle' : 'crossRot'),
                                pointRadius: 3
                            },
                            {
                                label: 'Offline Agents',
                                data: agentFilled.datasets.offline_agents,
                                borderColor: '#b8860b',
                                backgroundColor: 'rgba(184, 134, 11, 0.1)',
                                tension: 0.3,
                                borderWidth: 2,
                                pointBackgroundColor: agentFilled.isReal.map(r => r ? '#b8860b' : 'transparent'),
                                pointBorderColor: agentFilled.isReal.map(r => r ? '#b8860b' : '#ccc'),
                                pointStyle: agentFilled.isReal.map(r => r ? 'circle' : 'crossRot'),
                                pointRadius: 3
                            }
                        ]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: { display: true, position: 'bottom', labels: { padding: 10, boxWidth: 12 } },
                            tooltip: { callbacks: { label: ctx => ctx.dataset.label + ': ' + ctx.parsed.y } }
                        },
                        scales: {
                            y: { beginAtZero: true, ticks: { stepSize: 1, callback: v => Math.floor(v) }, grid: { color: '#e0e0e0' } },
                            x: { grid: { display: false } }
                        }
                    }
                });

                // Scanner Status Chart
                const scannerDataRaw = trendsData.scanners || [];
                const scannerFilled = fillLast30Days(scannerDataRaw, ['working_scanners', 'problem_scanners']);
                new Chart(document.getElementById('scannerChart'), {
                    type: 'line',
                    data: {
                        labels: scannerFilled.labels,
                        datasets: [
                            {
                                label: 'Working Scanners',
                                data: scannerFilled.datasets.working_scanners,
                                borderColor: '#1E2426',
                                backgroundColor: 'rgba(30, 36, 38, 0.1)',
                                tension: 0.3,
                                borderWidth: 2,
                                pointBackgroundColor: scannerFilled.isReal.map(r => r ? '#1E2426' : 'transparent'),
                                pointBorderColor: scannerFilled.isReal.map(r => r ? '#1E2426' : '#ccc'),
                                pointStyle: scannerFilled.isReal.map(r => r ? 'circle' : 'crossRot'),
                                pointRadius: 3
                            },
                            {
                                label: 'Problem Scanners',
                                data: scannerFilled.datasets.problem_scanners,
                                borderColor: '#b8860b',
                                backgroundColor: 'rgba(184, 134, 11, 0.1)',
                                tension: 0.3,
                                borderWidth: 2,
                                pointBackgroundColor: scannerFilled.isReal.map(r => r ? '#b8860b' : 'transparent'),
                                pointBorderColor: scannerFilled.isReal.map(r => r ? '#b8860b' : '#ccc'),
                                pointStyle: scannerFilled.isReal.map(r => r ? 'circle' : 'crossRot'),
                                pointRadius: 3
                            }
                        ]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: { display: true, position: 'bottom', labels: { padding: 10, boxWidth: 12 } },
                            tooltip: { callbacks: { label: ctx => ctx.dataset.label + ': ' + ctx.parsed.y } }
                        },
                        scales: {
                            y: { beginAtZero: true, ticks: { stepSize: 1, callback: v => Math.floor(v) }, grid: { color: '#e0e0e0' } },
                            x: { grid: { display: false } }
                        }
                    }
                });
            </script>
''')

    def _add_footer(self) -> None:
        self.html_parts.append('''
        </div>
        <div class="footer">
            Generated by Tenable Health Check Agent | <a href="https://github.com/d-zito/tenable-healthcheck-agent">View on GitHub</a>
        </div>
    </div>

    <script>
        // Accordion panel toggle
        function toggleAccordion(header) {
            header.classList.toggle('collapsed');
            const body = header.nextElementSibling;
            if (body && body.classList.contains('accordion-body')) {
                body.classList.toggle('collapsed');
            }
        }

        // Sub-section toggle
        function toggleSubSection(header) {
            header.classList.toggle('collapsed');
            const content = header.nextElementSibling;
            if (content && content.classList.contains('collapsible-content')) {
                content.classList.toggle('collapsed');
            }
        }

        // Legacy collapsible toggle (for any remaining uses)
        document.querySelectorAll('.collapsible').forEach(el => {
            el.addEventListener('click', () => {
                el.classList.toggle('collapsed');
                const content = el.nextElementSibling;
                if (content && content.classList.contains('collapsible-content')) {
                    content.classList.toggle('collapsed');
                }
            });
        });
    </script>
</body>
</html>
''')
