from datetime import datetime


class HTMLReporter:
    def __init__(self):
        self.html_parts = []

    def generate(self, run_data, analysis_results, claude_analysis=None, trends_data=None):
        timestamp = run_data.get('timestamp', 'Unknown')
        data = run_data.get('data', {})

        # Format timestamp for human readability
        if timestamp != 'Unknown':
            try:
                dt = datetime.fromisoformat(timestamp)
                formatted_timestamp = dt.strftime('%B %d, %Y at %I:%M %p UTC')
            except (ValueError, AttributeError):
                formatted_timestamp = timestamp
        else:
            formatted_timestamp = timestamp

        self._add_header(formatted_timestamp)

        # Add Claude analysis at the top if available
        if claude_analysis and not claude_analysis.get('error'):
            self._add_claude_section(claude_analysis)

        # Add trend charts if data available
        if trends_data:
            self._add_trends_section(trends_data)

        self._add_scan_section(data.get('scans', {}), analysis_results.get('scans', {}))
        self._add_asset_section(data.get('assets', {}), analysis_results.get('assets', {}), analysis_results.get('license', {}))
        self._add_agent_section(data.get('agents', {}), analysis_results.get('agents', {}))
        self._add_scanner_section(data.get('scanners', {}), analysis_results.get('scanners', {}))
        self._add_connector_section(data.get('connectors', {}), analysis_results.get('connectors', {}))
        self._add_footer()

        return '\n'.join(self.html_parts)

    def _add_header(self, timestamp):
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
            margin-bottom: 25px;
            border-left: 3px solid #E7FF00;
            padding-left: 15px;
        }
        .section h2 {
            color: #1E2426;
            font-size: 16px;
            margin-bottom: 10px;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 8px;
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
        .stat-card.warning { border-left-color: #E7FF00; }
        .stat-card.warning .value { color: #1E2426; }
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
        th:first-child {
            text-align: left;
        }
        td {
            padding: 6px 10px;
            border-bottom: 1px solid #e0e0e0;
            text-align: center;
        }
        td:first-child {
            text-align: left;
        }
        tr:nth-child(even) { background: #fafafa; }
        tr:hover { background: #f5f5f5; }
        .badge {
            display: inline-block;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 10px;
            font-weight: 600;
            text-transform: uppercase;
        }
        .badge.success { background: #00c853; color: white; }
        .badge.warning { background: #E7FF00; color: #1E2426; }
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
            border-left: 3px solid #E7FF00;
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
        .footer a:hover {
            text-decoration: underline;
        }
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
        .collapsible {
            cursor: pointer;
            user-select: none;
        }
        .collapsible:after {
            content: ' ▼';
            font-size: 10px;
            color: #E7FF00;
        }
        .collapsible.collapsed:after {
            content: ' ▶';
        }
        .collapsible-content {
            max-height: 2000px;
            overflow: hidden;
            transition: max-height 0.3s ease;
        }
        .collapsible-content.collapsed {
            max-height: 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔒 Tenable Health Check Report</h1>
            <div class="timestamp">Generated: ''' + timestamp + '''</div>
        </div>
        <div class="content">
''')

    def _add_claude_section(self, claude_analysis):
        status = claude_analysis.get('health_status', 'unknown').upper()
        status_colors = {
            'HEALTHY': '#00c853',
            'WARNING': '#E7FF00',
            'CRITICAL': '#ff1744',
            'UNKNOWN': '#666'
        }
        status_color = status_colors.get(status, '#666')
        status_text_colors = {
            'HEALTHY': '#00c853',
            'WARNING': '#1E2426',
            'CRITICAL': '#ff1744',
            'UNKNOWN': '#666'
        }
        status_text_color = status_text_colors.get(status, '#666')
        status_emojis = {
            'HEALTHY': '✓',
            'WARNING': '⚠️',
            'CRITICAL': '🚨',
            'UNKNOWN': '?'
        }
        status_emoji = status_emojis.get(status, '?')

        self.html_parts.append(f'''
            <div class="section" style="background: #fafafa; padding: 15px; border-radius: 4px; border-left: 4px solid {status_color};">
                <h2 style="margin-bottom: 12px;">🧠 AI Executive Summary</h2>
                <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 15px; background: white; padding: 12px; border-radius: 4px; border: 2px solid {status_color};">
                    <div style="font-size: 32px;">{status_emoji}</div>
                    <div>
                        <div style="font-size: 10px; color: #666; text-transform: uppercase; letter-spacing: 0.5px;">Overall Health Status</div>
                        <div style="font-size: 20px; font-weight: bold; color: {status_text_color};">{status}</div>
                    </div>
                </div>
''')

        if claude_analysis.get('executive_summary'):
            summary = claude_analysis['executive_summary'].replace('\n', '<br>')
            self.html_parts.append(f'''
                <div style="background: white; padding: 12px; border-radius: 4px; margin-bottom: 10px; border-left: 3px solid #1E2426;">
                    <h3 style="color: #1E2426; font-size: 13px; margin-bottom: 8px; font-weight: 600;">📋 Summary</h3>
                    <p style="line-height: 1.6; color: #333; font-size: 13px;">{summary}</p>
                </div>
''')

        if claude_analysis.get('key_concerns'):
            self.html_parts.append('''
                <div style="background: white; padding: 12px; border-radius: 4px; margin-bottom: 10px; border-left: 3px solid #ff1744;">
                    <h3 style="color: #ff1744; font-size: 13px; margin-bottom: 8px; font-weight: 600;">🚨 Key Concerns</h3>
                    <ul style="margin-left: 18px; line-height: 1.6; font-size: 13px;">
''')
            for concern in claude_analysis['key_concerns']:
                self.html_parts.append(f'                        <li style="color: #333; margin-bottom: 4px;">{concern}</li>')
            self.html_parts.append('''
                    </ul>
                </div>
''')

        if claude_analysis.get('recommendations'):
            self.html_parts.append('''
                <div style="background: white; padding: 12px; border-radius: 4px; margin-bottom: 10px; border-left: 3px solid #E7FF00;">
                    <h3 style="color: #1E2426; font-size: 13px; margin-bottom: 8px; font-weight: 600;">💡 Recommendations</h3>
''')
            for rec in claude_analysis['recommendations']:
                priority = rec.get('priority', 'medium').upper()
                priority_colors = {
                    'HIGH': '#ff1744',
                    'MEDIUM': '#E7FF00',
                    'LOW': '#1E2426'
                }
                priority_text_colors = {
                    'HIGH': 'white',
                    'MEDIUM': '#1E2426',
                    'LOW': 'white'
                }
                priority_color = priority_colors.get(priority, '#666')
                priority_text_color = priority_text_colors.get(priority, 'white')
                issue = rec.get('issue', 'N/A')
                action = rec.get('action', 'N/A')

                self.html_parts.append(f'''
                    <div style="margin-bottom: 8px; padding: 10px; background: #fafafa; border-radius: 4px; border-left: 3px solid {priority_color};">
                        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px;">
                            <span style="background: {priority_color}; color: {priority_text_color}; padding: 2px 6px; border-radius: 3px; font-size: 10px; font-weight: bold;">{priority}</span>
                            <strong style="color: #1E2426; font-size: 12px;">{issue}</strong>
                        </div>
                        <div style="color: #666; padding-left: 8px; border-left: 2px solid #e0e0e0; font-size: 12px;">
                            → {action}
                        </div>
                    </div>
''')
            self.html_parts.append('''
                </div>
''')

        if claude_analysis.get('trends'):
            self.html_parts.append('''
                <div style="background: white; padding: 12px; border-radius: 4px; border-left: 3px solid #1E2426;">
                    <h3 style="color: #1E2426; font-size: 13px; margin-bottom: 8px; font-weight: 600;">📈 Trends to Monitor</h3>
                    <ul style="margin-left: 18px; line-height: 1.6; font-size: 13px;">
''')
            for trend in claude_analysis['trends']:
                self.html_parts.append(f'                        <li style="color: #333; margin-bottom: 4px;">{trend}</li>')
            self.html_parts.append('''
                    </ul>
                </div>
''')

        self.html_parts.append('            </div>')

    def _add_scan_section(self, scan_data, analysis):
        days_back = scan_data.get('days_back', 7)
        total_launches = scan_data.get('total_launches', 0)
        currently_running = scan_data.get('currently_running', 0)
        unique_scans = scan_data.get('unique_scans', 0)
        scan_summary = scan_data.get('scan_summary', {})

        # Calculate total failures across all scans
        total_failures = sum(details['failed_runs'] for details in scan_summary.values())
        status_class = 'success' if total_failures == 0 else 'warning' if total_failures < 5 else 'danger'

        self.html_parts.append(f'''
            <div class="section">
                <h2>📊 Scan Health (Past {days_back} Days)</h2>
                <div class="stat-grid">
                    <div class="stat-card">
                        <div class="label">Total Launches</div>
                        <div class="value">{total_launches}</div>
                    </div>
                    <div class="stat-card success">
                        <div class="label">Currently Running</div>
                        <div class="value">{currently_running}</div>
                    </div>
                    <div class="stat-card">
                        <div class="label">Unique Scans</div>
                        <div class="value">{unique_scans}</div>
                    </div>
                    <div class="stat-card {status_class}">
                        <div class="label">Total Failed Runs</div>
                        <div class="value">{total_failures}</div>
                    </div>
                </div>
''')

        if scan_summary:
            # Sort by total runs descending
            sorted_scans = sorted(
                scan_summary.items(),
                key=lambda x: x[1]['total_runs'],
                reverse=True
            )

            self.html_parts.append('''
                <table>
                    <thead>
                        <tr>
                            <th>Scan Name</th>
                            <th>Policy</th>
                            <th>Enabled</th>
                            <th>Total Runs</th>
                            <th>Running</th>
                            <th>Successful</th>
                            <th>Stopped</th>
                            <th>Failed</th>
                            <th>Success Rate</th>
                        </tr>
                    </thead>
                    <tbody>
''')
            for scan_name, details in sorted_scans:
                total_runs = details['total_runs']
                successful_runs = details.get('completed_runs', details.get('success_runs', 0))
                failed_runs = details['failed_runs']
                stopped_runs = details.get('stopped_runs', 0)
                disabled_runs = details.get('disabled_runs', 0)
                canceled_runs = details.get('canceled_runs', 0)
                paused_runs = details.get('paused_runs', 0)
                running_count = details.get('running_count', 0)
                is_enabled = details.get('is_enabled', True)
                policy_name = details.get('policy', 'N/A')

                # Stopped = all intentional user actions (stopped, disabled, canceled, paused)
                total_stopped = stopped_runs + disabled_runs + canceled_runs + paused_runs

                # Success rate = successful / (total_runs - running)
                completed_runs = total_runs - running_count
                success_rate = (successful_runs / completed_runs * 100) if completed_runs > 0 else 0

                # Build enabled cell with checkmark or X
                if is_enabled:
                    enabled_cell = '<span style="color: #00c853; font-size: 18px; font-weight: bold;">✓</span>'
                else:
                    enabled_cell = '<span style="color: #ff1744; font-size: 18px; font-weight: bold;">✗</span>'

                self.html_parts.append(f'''
                        <tr>
                            <td>{scan_name}</td>
                            <td>{policy_name if policy_name else 'N/A'}</td>
                            <td>{enabled_cell}</td>
                            <td>{total_runs}</td>
                            <td>{running_count}</td>
                            <td>{successful_runs}</td>
                            <td>{total_stopped}</td>
                            <td>{failed_runs}</td>
                            <td>{success_rate:.1f}%</td>
                        </tr>
''')
            self.html_parts.append('''
                    </tbody>
                </table>
''')

        if analysis.get('has_previous_data'):
            launches_change = analysis.get('launches_change', 0)
            running_change = analysis.get('running_change', 0)

            launches_class = 'positive' if launches_change > 0 else 'negative' if launches_change < 0 else 'neutral'
            launches_arrow = '↑' if launches_change > 0 else '↓' if launches_change < 0 else '→'

            running_class = 'neutral'
            running_arrow = '↑' if running_change > 0 else '↓' if running_change < 0 else '→'

            self.html_parts.append(f'''
                <div class="alert info">
                    <strong>Change from previous run:</strong><br>
                    Total launches: <span class="change {launches_class}">{launches_arrow} {abs(launches_change)}</span><br>
                    Currently running: <span class="change {running_class}">{running_arrow} {abs(running_change)}</span>
                </div>
''')

        self.html_parts.append('            </div>')

    def _add_asset_section(self, asset_data, analysis, license_analysis):
        total = asset_data.get('total_assets', 0)
        licensed = asset_data.get('licensed_assets', 0)
        unlicensed = asset_data.get('unlicensed_assets', 0)
        auth_succeeded = asset_data.get('auth_succeeded', 0)
        auth_not_attempted = asset_data.get('auth_not_attempted', 0)
        auth_failed = asset_data.get('auth_failed', 0)
        success_pct = asset_data.get('auth_succeeded_percentage', 0)

        status_class = 'success' if success_pct >= 80 else 'warning' if success_pct >= 60 else 'danger'

        self.html_parts.append(f'''
            <div class="section">
                <h2>🔐 Asset & License Status</h2>
                <div class="stat-grid">
                    <div class="stat-card">
                        <div class="label">Total Assets</div>
                        <div class="value">{total}</div>
                    </div>
                    <div class="stat-card success">
                        <div class="label">Licensed Assets (90d)</div>
                        <div class="value">{licensed}</div>
                    </div>
                    <div class="stat-card">
                        <div class="label">Unlicensed Assets</div>
                        <div class="value">{unlicensed}</div>
                    </div>
                    <div class="stat-card {status_class}">
                        <div class="label">Auth Succeeded</div>
                        <div class="value">{auth_succeeded} ({success_pct}%)</div>
                    </div>
                    <div class="stat-card warning">
                        <div class="label">Auth Not Attempted</div>
                        <div class="value">{auth_not_attempted}</div>
                    </div>
                    <div class="stat-card danger">
                        <div class="label">Auth Failed</div>
                        <div class="value">{auth_failed}</div>
                    </div>
                </div>
''')

        # Show changes from previous run
        if analysis.get('has_previous_data') or license_analysis.get('has_previous_data'):
            self.html_parts.append('<div class="alert info"><strong>Changes from previous run:</strong><br>')

            # Authentication change
            if analysis.get('has_previous_data'):
                change_pct = analysis.get('change_percentage', 0)
                is_significant = analysis.get('is_significant_change', False)
                change_class = 'positive' if change_pct > 0 else 'negative' if change_pct < 0 else 'neutral'
                arrow = '↑' if change_pct > 0 else '↓' if change_pct < 0 else '→'

                self.html_parts.append(f'''
                    Authentication Success Rate: <span class="change {change_class}">{arrow} {abs(change_pct):.2f}%</span>
                ''')

                if is_significant:
                    self.html_parts.append(f''' <strong>⚠️ SIGNIFICANT CHANGE</strong> (threshold: {analysis['threshold']}%)''')

                self.html_parts.append('<br>')

            # License change
            if license_analysis.get('has_previous_data'):
                license_change = license_analysis.get('change_count', 0)
                license_change_pct = license_analysis.get('change_percentage', 0)
                is_significant_license = license_analysis.get('is_significant_change', False)
                change_class = 'positive' if license_change > 0 else 'negative' if license_change < 0 else 'neutral'
                arrow = '↑' if license_change > 0 else '↓' if license_change < 0 else '→'

                self.html_parts.append(f'''
                    Licensed Assets: <span class="change {change_class}">{arrow} {abs(license_change)} assets ({license_change_pct:+.2f}%)</span>
                ''')

                if is_significant_license:
                    self.html_parts.append(f''' <strong>⚠️ SIGNIFICANT CHANGE</strong> (threshold: {license_analysis['threshold']}%)''')

            self.html_parts.append('</div>')

        self.html_parts.append('            </div>')

    def _add_agent_section(self, agent_data, analysis):
        total = agent_data.get('total_agents', 0)
        online = agent_data.get('online_agents', 0)
        offline = agent_data.get('offline_agents', 0)
        long_offline = agent_data.get('long_offline_agents', 0)
        threshold_days = agent_data.get('offline_threshold_days', 14)

        status_class = 'success' if offline == 0 else 'warning' if offline < 10 else 'danger'

        self.html_parts.append(f'''
            <div class="section">
                <h2>🤖 Agent Status</h2>
                <div class="stat-grid">
                    <div class="stat-card">
                        <div class="label">Total Agents</div>
                        <div class="value">{total}</div>
                    </div>
                    <div class="stat-card success">
                        <div class="label">Online</div>
                        <div class="value">{online}</div>
                    </div>
                    <div class="stat-card {status_class}">
                        <div class="label">Offline</div>
                        <div class="value">{offline}</div>
                    </div>
                    <div class="stat-card danger">
                        <div class="label">Offline > {threshold_days} days</div>
                        <div class="value">{long_offline}</div>
                    </div>
                </div>
''')

        if agent_data.get('long_offline_agent_list'):
            self.html_parts.append(f'''
                <table>
                    <thead>
                        <tr>
                            <th>Agent Name</th>
                            <th>Status</th>
                            <th>Last Connect</th>
                        </tr>
                    </thead>
                    <tbody>
''')
            for agent in agent_data['long_offline_agent_list']:
                last_connect = datetime.fromtimestamp(agent['last_connect']).strftime('%Y-%m-%d') if agent.get('last_connect') else 'Never'
                self.html_parts.append(f'''
                        <tr>
                            <td>{agent['name']}</td>
                            <td><span class="badge danger">{agent['status']}</span></td>
                            <td>{last_connect}</td>
                        </tr>
''')
            self.html_parts.append('''
                    </tbody>
                </table>
''')

        if analysis.get('has_previous_data'):
            offline_change = analysis.get('offline_change', 0)
            long_change = analysis.get('long_offline_change', 0)
            self.html_parts.append(f'''
                <div class="alert info">
                    <strong>Change from previous run:</strong><br>
                    Offline agents: {offline_change:+d}<br>
                    Long-term offline: {long_change:+d}
                </div>
''')

        self.html_parts.append('            </div>')

    def _add_scanner_section(self, scanner_data, analysis):
        total = scanner_data.get('total_scanners', 0)
        working = scanner_data.get('working_scanners', 0)
        problems = scanner_data.get('problem_scanners', 0)

        status_class = 'success' if problems == 0 else 'warning' if problems < 3 else 'danger'

        self.html_parts.append(f'''
            <div class="section">
                <h2>🖥️ Scanner Status</h2>
                <div class="stat-grid">
                    <div class="stat-card">
                        <div class="label">Total Scanners</div>
                        <div class="value">{total}</div>
                    </div>
                    <div class="stat-card success">
                        <div class="label">Working</div>
                        <div class="value">{working}</div>
                    </div>
                    <div class="stat-card {status_class}">
                        <div class="label">Problems</div>
                        <div class="value">{problems}</div>
                    </div>
                </div>
''')

        if scanner_data.get('problem_scanner_list'):
            self.html_parts.append('''
                <table>
                    <thead>
                        <tr>
                            <th>Scanner Name</th>
                            <th>Status</th>
                            <th>Type</th>
                            <th>Scans</th>
                        </tr>
                    </thead>
                    <tbody>
''')
            for scanner in scanner_data['problem_scanner_list']:
                self.html_parts.append(f'''
                        <tr>
                            <td>{scanner['name']}</td>
                            <td><span class="badge danger">{scanner['status']}</span></td>
                            <td>{scanner.get('type', 'N/A')}</td>
                            <td>{scanner.get('scan_count', 0)}</td>
                        </tr>
''')
            self.html_parts.append('''
                    </tbody>
                </table>
''')

        if analysis.get('has_previous_data'):
            new_problems = analysis.get('new_problem_scanners', [])
            recovered = analysis.get('recovered_scanners', [])

            if new_problems or recovered:
                self.html_parts.append('<div class="alert warning">')
                if new_problems:
                    self.html_parts.append(f'<strong>⚠️ NEW problem scanners:</strong> {len(new_problems)}<br>')
                if recovered:
                    self.html_parts.append(f'<strong>✓ Recovered scanners:</strong> {len(recovered)}')
                self.html_parts.append('</div>')

        self.html_parts.append('            </div>')

    def _add_connector_section(self, connector_data, analysis):
        total = connector_data.get('total_connectors', 0)
        working = connector_data.get('working_connectors', 0)
        problems = connector_data.get('problem_connectors', 0)

        status_class = 'success' if problems == 0 else 'warning' if problems < 3 else 'danger'

        self.html_parts.append(f'''
            <div class="section">
                <h2>🔌 Connector Status</h2>
                <div class="stat-grid">
                    <div class="stat-card">
                        <div class="label">Total Connectors</div>
                        <div class="value">{total}</div>
                    </div>
                    <div class="stat-card success">
                        <div class="label">Working</div>
                        <div class="value">{working}</div>
                    </div>
                    <div class="stat-card {status_class}">
                        <div class="label">Problems</div>
                        <div class="value">{problems}</div>
                    </div>
                </div>
''')

        if connector_data.get('problem_connector_list'):
            self.html_parts.append('''
                <table>
                    <thead>
                        <tr>
                            <th>Connector Name</th>
                            <th>Status</th>
                            <th>Type</th>
                        </tr>
                    </thead>
                    <tbody>
''')
            for connector in connector_data['problem_connector_list']:
                self.html_parts.append(f'''
                        <tr>
                            <td>{connector['name']}</td>
                            <td><span class="badge danger">{connector['status']}</span></td>
                            <td>{connector.get('type', 'N/A')}</td>
                        </tr>
''')
            self.html_parts.append('''
                    </tbody>
                </table>
''')

        if analysis.get('has_previous_data'):
            new_problems = analysis.get('new_problem_connectors', [])
            recovered = analysis.get('recovered_connectors', [])

            if new_problems or recovered:
                self.html_parts.append('<div class="alert warning">')
                if new_problems:
                    self.html_parts.append(f'<strong>⚠️ NEW problem connectors:</strong> {len(new_problems)}<br>')
                if recovered:
                    self.html_parts.append(f'<strong>✓ Recovered connectors:</strong> {len(recovered)}')
                self.html_parts.append('</div>')

        self.html_parts.append('            </div>')

    def _add_trends_section(self, trends_data):
        """Add trend charts section with historical data visualization."""
        import json

        # Check if we have enough data points for meaningful charts
        auth_data = trends_data.get('authentication', [])
        if len(auth_data) < 2:
            return  # Need at least 2 data points for a trend

        self.html_parts.append('''
            <div class="section">
                <h2>📈 Historical Trends</h2>
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
                        <h3>Scan Health Over Time</h3>
                        <div class="chart-container">
                            <canvas id="scanChart"></canvas>
                        </div>
                    </div>
                </div>
            </div>

            <script>
                const trendsData = ''' + json.dumps(trends_data) + ''';

                // Helper to format dates
                function formatDate(timestamp) {
                    const date = new Date(timestamp);
                    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
                }

                // Chart defaults for Tenable branding
                Chart.defaults.font.family = "'Work Sans', sans-serif";
                Chart.defaults.font.size = 11;

                // Authentication Success Rate Chart
                const authData = trendsData.authentication || [];
                const authLabels = authData.map(d => formatDate(d.timestamp));
                const authChart = new Chart(document.getElementById('authChart'), {
                    type: 'line',
                    data: {
                        labels: authLabels,
                        datasets: [{
                            label: 'Authentication Success %',
                            data: authData.map(d => d.auth_succeeded_pct),
                            borderColor: '#1E2426',
                            backgroundColor: 'rgba(30, 36, 38, 0.1)',
                            tension: 0.3,
                            fill: true,
                            borderWidth: 2,
                            pointBackgroundColor: '#E7FF00',
                            pointBorderColor: '#1E2426',
                            pointRadius: 4
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: { display: false }
                        },
                        scales: {
                            y: {
                                beginAtZero: true,
                                max: 100,
                                ticks: { callback: value => value + '%' },
                                grid: { color: '#e0e0e0' }
                            },
                            x: { grid: { display: false } }
                        }
                    }
                });

                // License Usage Chart
                const licenseData = trendsData.license || [];
                const licenseLabels = licenseData.map(d => formatDate(d.timestamp));
                const licenseChart = new Chart(document.getElementById('licenseChart'), {
                    type: 'line',
                    data: {
                        labels: licenseLabels,
                        datasets: [{
                            label: 'Licensed Assets',
                            data: licenseData.map(d => d.total_licensed_assets),
                            borderColor: '#1E2426',
                            backgroundColor: 'rgba(30, 36, 38, 0.1)',
                            tension: 0.3,
                            fill: true,
                            borderWidth: 2,
                            pointBackgroundColor: '#E7FF00',
                            pointBorderColor: '#1E2426',
                            pointRadius: 4
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: { display: false }
                        },
                        scales: {
                            y: {
                                beginAtZero: true,
                                grid: { color: '#e0e0e0' }
                            },
                            x: { grid: { display: false } }
                        }
                    }
                });

                // Agent Status Chart
                const agentData = trendsData.agents || [];
                const agentLabels = agentData.map(d => formatDate(d.timestamp));
                const agentChart = new Chart(document.getElementById('agentChart'), {
                    type: 'line',
                    data: {
                        labels: agentLabels,
                        datasets: [
                            {
                                label: 'Online Agents',
                                data: agentData.map(d => d.online_agents),
                                borderColor: '#1E2426',
                                backgroundColor: 'rgba(30, 36, 38, 0.1)',
                                tension: 0.3,
                                borderWidth: 2,
                                pointBackgroundColor: '#1E2426',
                                pointRadius: 3
                            },
                            {
                                label: 'Offline Agents',
                                data: agentData.map(d => d.offline_agents),
                                borderColor: '#E7FF00',
                                backgroundColor: 'rgba(231, 255, 0, 0.2)',
                                tension: 0.3,
                                borderWidth: 2,
                                pointBackgroundColor: '#E7FF00',
                                pointBorderColor: '#1E2426',
                                pointRadius: 3
                            }
                        ]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: { display: true, position: 'bottom', labels: { padding: 10, boxWidth: 12 } }
                        },
                        scales: {
                            y: {
                                beginAtZero: true,
                                grid: { color: '#e0e0e0' }
                            },
                            x: { grid: { display: false } }
                        }
                    }
                });

                // Scan Health Chart
                const scanData = trendsData.scans || [];
                const scanLabels = scanData.map(d => formatDate(d.timestamp));
                const scanChart = new Chart(document.getElementById('scanChart'), {
                    type: 'bar',
                    data: {
                        labels: scanLabels,
                        datasets: [
                            {
                                label: 'Completed Scans',
                                data: scanData.map(d => d.completed_scans),
                                backgroundColor: '#1E2426'
                            },
                            {
                                label: 'Problem Scans',
                                data: scanData.map(d => d.problem_scans),
                                backgroundColor: '#E7FF00'
                            }
                        ]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: { display: true, position: 'bottom', labels: { padding: 10, boxWidth: 12 } }
                        },
                        scales: {
                            y: {
                                beginAtZero: true,
                                stacked: false,
                                grid: { color: '#e0e0e0' }
                            },
                            x: { grid: { display: false } }
                        }
                    }
                });
            </script>
''')

    def _add_footer(self):
        self.html_parts.append('''
        </div>
        <div class="footer">
            Generated by Tenable Health Check Agent | <a href="https://github.com/d-zito/tenable-healthcheck-agent">View on GitHub</a>
        </div>
    </div>
</body>
</html>
''')
