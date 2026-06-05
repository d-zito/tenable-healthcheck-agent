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

        # Wrap the 4 status sections in a 2-column grid
        self.html_parts.append('<div class="status-grid">')
        self._add_asset_section(data.get('assets', {}), analysis_results.get('assets', {}), analysis_results.get('license', {}))
        self._add_agent_section(data.get('agents', {}), analysis_results.get('agents', {}))
        self._add_scanner_section(data.get('scanners', {}), analysis_results.get('scanners', {}))
        self._add_connector_section(data.get('connectors', {}), analysis_results.get('connectors', {}))
        self.html_parts.append('</div>')

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
        .status-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 20px;
            margin: 20px 0;
        }
        .status-grid .section {
            margin-bottom: 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Tenable Health Check Report</h1>
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
                <h2 style="margin-bottom: 12px;">AI Executive Summary</h2>
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
                self.html_parts.append(f'                        <li style="color: #333; margin-bottom: 4px;">{concern}</li>')
            self.html_parts.append('''
                    </ul>
                </div>
''')

        if claude_analysis.get('recommendations'):
            self.html_parts.append('''
                <div style="background: white; padding: 12px; border-radius: 4px; margin-bottom: 10px; border-left: 3px solid #E7FF00;">
                    <h3 style="color: #1E2426; font-size: 13px; margin-bottom: 8px; font-weight: 600;">Recommendations</h3>
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
                    <h3 style="color: #1E2426; font-size: 13px; margin-bottom: 8px; font-weight: 600;">Trends to Monitor</h3>
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
        scan_summary = scan_data.get('scan_summary', {})

        # Split scans by type
        # Agent scans: scan_type is None or 'agent'
        # Remote scans: all other scan types
        agent_scans = {name: details for name, details in scan_summary.items()
                       if details.get('scan_type') in [None, 'agent']}
        network_scans = {name: details for name, details in scan_summary.items()
                         if details.get('scan_type') not in [None, 'agent']}

        # Helper function to render a scan table
        def render_scan_table(scans_dict, title, is_agent_table=False, show_overview=False):
            if not scans_dict:
                return

            sorted_scans = sorted(
                scans_dict.items(),
                key=lambda x: x[1]['total_runs'],
                reverse=True
            )

            total_runs_section = sum(s['total_runs'] for s in scans_dict.values())
            total_failures_section = sum(s['failed_runs'] for s in scans_dict.values())
            currently_running = sum(1 for s in scans_dict.values() if s.get('running_count', 0) > 0)

            # Headers differ for agent vs network scans
            if is_agent_table:
                headers = '''
                            <th>Scan Name</th>
                            <th>Policy</th>
                            <th>Launch Type</th>
                            <th>Enabled</th>
'''
            else:
                headers = '''
                            <th>Scan Name</th>
                            <th>Policy</th>
                            <th>Enabled</th>
                            <th>Total Runs</th>
                            <th>Running</th>
                            <th>Successful</th>
                            <th>Stopped</th>
                            <th>Failed</th>
                            <th>Success Rate</th>
'''

            self.html_parts.append(f'''
                <div class="section">
                    <h2>{title}</h2>
''')

            self.html_parts.append(f'''
                <table>
                    <thead>
                        <tr>{headers}
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

                # Build row with or without launch type column
                if is_agent_table:
                    # For agent scans: if agent_scan_launch_type is None or empty, it's scheduled
                    launch_type = details.get('agent_scan_launch_type')
                    if not launch_type:
                        launch_type = 'scheduled'
                    self.html_parts.append(f'''
                        <tr>
                            <td>{scan_name}</td>
                            <td>{policy_name if policy_name else 'N/A'}</td>
                            <td>{launch_type}</td>
                            <td>{enabled_cell}</td>
                        </tr>
''')
                else:
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
                </div>
''')

        # Render network scans first (with overview), then agent scans
        if network_scans:
            render_scan_table(network_scans, f"Network Scans (Past {days_back} Days)", is_agent_table=False, show_overview=True)

        if agent_scans:
            render_scan_table(agent_scans, "Agent Scans", is_agent_table=True, show_overview=False)

    def _add_asset_section(self, asset_data, analysis, license_analysis):
        total = asset_data.get('total_assets', 0)
        licensed = asset_data.get('licensed_assets', 0)
        unlicensed = asset_data.get('unlicensed_assets', 0)
        auth_succeeded = asset_data.get('auth_succeeded', 0)
        auth_not_attempted = asset_data.get('auth_not_attempted', 0)
        auth_failed = asset_data.get('auth_failed', 0)
        success_pct = asset_data.get('auth_succeeded_percentage', 0)

        self.html_parts.append(f'''
            <div class="section">
                <h2>Assets & Licensing</h2>
                <table style="margin-bottom: 15px;">
                    <thead>
                        <tr>
                            <th></th>
                            <th style="text-align: right;">Count</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>Total Assets</td>
                            <td style="text-align: right;"><strong>{total}</strong></td>
                        </tr>
                        <tr>
                            <td>Licensed (90d)</td>
                            <td style="text-align: right;">{licensed}</td>
                        </tr>
                        <tr>
                            <td>Unlicensed</td>
                            <td style="text-align: right;">{unlicensed}</td>
                        </tr>
                    </tbody>
                </table>
            </div>

            <div class="section">
                <h2>Authentication</h2>
                <table style="margin-bottom: 15px;">
                    <thead>
                        <tr>
                            <th></th>
                            <th style="text-align: right;">Count</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>Auth Succeeded</td>
                            <td style="text-align: right;">{auth_succeeded} ({success_pct}%)</td>
                        </tr>
                        <tr>
                            <td>Auth Not Attempted</td>
                            <td style="text-align: right;">{auth_not_attempted}</td>
                        </tr>
                        <tr>
                            <td>Auth Failed</td>
                            <td style="text-align: right;">{auth_failed}</td>
                        </tr>
                    </tbody>
                </table>
            </div>
''')

    def _add_agent_section(self, agent_data, analysis):
        total = agent_data.get('total_agents', 0)
        online = agent_data.get('online_agents', 0)
        offline = agent_data.get('offline_agents', 0)
        long_offline = agent_data.get('long_offline_agents', 0)
        threshold_days = agent_data.get('offline_threshold_days', 14)

        self.html_parts.append(f'''
            <div class="section">
                <h2>Agents</h2>
                <table style="margin-bottom: 15px;">
                    <thead>
                        <tr>
                            <th></th>
                            <th style="text-align: right;">Count</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>Total Agents</td>
                            <td style="text-align: right;"><strong>{total}</strong></td>
                        </tr>
                        <tr>
                            <td>Online</td>
                            <td style="text-align: right;">{online}</td>
                        </tr>
                        <tr>
                            <td>Offline</td>
                            <td style="text-align: right;">{offline}</td>
                        </tr>
                        <tr>
                            <td>Offline &gt; {threshold_days} days</td>
                            <td style="text-align: right;">{long_offline}</td>
                        </tr>
                    </tbody>
                </table>
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

        self.html_parts.append('            </div>')

    def _add_scanner_section(self, scanner_data, analysis):
        total = scanner_data.get('total_scanners', 0)
        working = scanner_data.get('working_scanners', 0)
        problems = scanner_data.get('problem_scanners', 0)

        self.html_parts.append(f'''
            <div class="section">
                <h2>Scanners</h2>
                <table style="margin-bottom: 15px;">
                    <thead>
                        <tr>
                            <th></th>
                            <th style="text-align: right;">Count</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>Total Scanners</td>
                            <td style="text-align: right;"><strong>{total}</strong></td>
                        </tr>
                        <tr>
                            <td>Working</td>
                            <td style="text-align: right;">{working}</td>
                        </tr>
                        <tr>
                            <td>Problems</td>
                            <td style="text-align: right;">{problems}</td>
                        </tr>
                    </tbody>
                </table>
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

        self.html_parts.append(f'''
            <div class="section">
                <h2>Connectors</h2>
                <table style="margin-bottom: 15px;">
                    <thead>
                        <tr>
                            <th></th>
                            <th style="text-align: right;">Count</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>Total Connectors</td>
                            <td style="text-align: right;"><strong>{total}</strong></td>
                        </tr>
                        <tr>
                            <td>Working</td>
                            <td style="text-align: right;">{working}</td>
                        </tr>
                        <tr>
                            <td>Problems</td>
                            <td style="text-align: right;">{problems}</td>
                        </tr>
                    </tbody>
                </table>
''')

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

                // Scanner Status Chart
                const scannerData = trendsData.scanners || [];
                const scannerLabels = scannerData.map(d => formatDate(d.timestamp));
                const scannerChart = new Chart(document.getElementById('scannerChart'), {
                    type: 'line',
                    data: {
                        labels: scannerLabels,
                        datasets: [
                            {
                                label: 'Working Scanners',
                                data: scannerData.map(d => d.working_scanners),
                                borderColor: '#1E2426',
                                backgroundColor: 'rgba(30, 36, 38, 0.1)',
                                tension: 0.3,
                                borderWidth: 2,
                                pointBackgroundColor: '#1E2426',
                                pointRadius: 3
                            },
                            {
                                label: 'Problem Scanners',
                                data: scannerData.map(d => d.problem_scanners),
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
