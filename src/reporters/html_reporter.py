from datetime import datetime


class HTMLReporter:
    def __init__(self):
        self.html_parts = []

    def _get_historical_data(self, trends_data):
        """Extract data from 7 and 30 days ago for comparison columns."""
        if not trends_data:
            return None

        from datetime import datetime, timedelta, timezone

        now = datetime.now(timezone.utc)
        seven_days_ago = now - timedelta(days=7)
        thirty_days_ago = now - timedelta(days=30)

        def find_closest_data_point(data_points, target_date):
            """Find the data point closest to the target date."""
            if not data_points:
                return None

            closest = None
            min_diff = None

            for point in data_points:
                try:
                    point_date = datetime.fromisoformat(point['timestamp'])
                    diff = abs((point_date - target_date).total_seconds())

                    if min_diff is None or diff < min_diff:
                        min_diff = diff
                        closest = point
                except (ValueError, KeyError):
                    continue

            # Only return if within 2 days of target
            if closest and min_diff is not None and min_diff <= (2 * 24 * 60 * 60):
                return closest
            return None

        historical = {
            'authentication': {
                '7_days': find_closest_data_point(trends_data.get('authentication', []), seven_days_ago),
                '30_days': find_closest_data_point(trends_data.get('authentication', []), thirty_days_ago)
            },
            'license': {
                '7_days': find_closest_data_point(trends_data.get('license', []), seven_days_ago),
                '30_days': find_closest_data_point(trends_data.get('license', []), thirty_days_ago)
            },
            'agents': {
                '7_days': find_closest_data_point(trends_data.get('agents', []), seven_days_ago),
                '30_days': find_closest_data_point(trends_data.get('agents', []), thirty_days_ago)
            },
            'scanners': {
                '7_days': find_closest_data_point(trends_data.get('scanners', []), seven_days_ago),
                '30_days': find_closest_data_point(trends_data.get('scanners', []), thirty_days_ago)
            },
            'connectors': {
                '7_days': find_closest_data_point(trends_data.get('connectors', []), seven_days_ago),
                '30_days': find_closest_data_point(trends_data.get('connectors', []), thirty_days_ago)
            },
            'users': {
                '7_days': find_closest_data_point(trends_data.get('users', []), seven_days_ago),
                '30_days': find_closest_data_point(trends_data.get('users', []), thirty_days_ago)
            }
        }

        return historical

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

        # Extract historical data (7 and 30 days ago)
        historical_data = self._get_historical_data(trends_data)

        self._add_header(formatted_timestamp)

        # Add Claude analysis at the top if available
        if claude_analysis and not claude_analysis.get('error'):
            self._add_claude_section(claude_analysis)

        # Add trend charts if data available
        if trends_data:
            self._add_trends_section(trends_data)

        self._add_scan_section(data.get('scans', {}), analysis_results.get('scans', {}))

        # Wrap the status sections in a 2-column grid
        self.html_parts.append('<div class="status-grid">')
        self._add_asset_section(data.get('assets', {}), analysis_results.get('assets', {}), analysis_results.get('license', {}), historical_data)
        self._add_agent_section(data.get('agents', {}), analysis_results.get('agents', {}), historical_data)
        self._add_scanner_section(data.get('scanners', {}), analysis_results.get('scanners', {}), historical_data)
        self._add_connector_section(data.get('connectors', {}), analysis_results.get('connectors', {}), historical_data)
        self._add_user_section(data.get('users', {}), analysis_results.get('users', {}), historical_data)
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
        inactive_scans = scan_data.get('inactive_scans', 0)

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
'''
            else:
                headers = '''
                            <th>Scan Name</th>
                            <th>Policy</th>
                            <th>Running</th>
                            <th>Completed</th>
                            <th>Incomplete</th>
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

                # Incomplete = stopped + failed
                total_stopped = stopped_runs + disabled_runs + canceled_runs + paused_runs
                total_incomplete = total_stopped + failed_runs

                # Success rate = successful / (total_runs - running)
                completed_runs_calc = total_runs - running_count
                success_rate = (successful_runs / completed_runs_calc * 100) if completed_runs_calc > 0 else 0

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
                        </tr>
''')
                else:
                    self.html_parts.append(f'''
                        <tr>
                            <td>{scan_name}</td>
                            <td>{policy_name if policy_name else 'N/A'}</td>
                            <td>{running_count}</td>
                            <td>{successful_runs}</td>
                            <td>{total_incomplete}</td>
                            <td>{success_rate:.1f}%</td>
                        </tr>
''')
            self.html_parts.append('''
                    </tbody>
                </table>
''')

            # Add inactive scans message if applicable
            if show_overview and inactive_scans > 0:
                self.html_parts.append(f'''
                <div style="margin-top: 10px; padding: 10px; background: #f9f9f9; border-left: 3px solid #666; font-size: 13px;">
                    <strong>{inactive_scans}</strong> additional scan(s) are configured but have not launched in the past {days_back} days
                </div>
''')

            self.html_parts.append('''
                </div>
''')

        # Render network scans first (with overview), then agent scans
        if network_scans:
            render_scan_table(network_scans, f"Network Scans (Past {days_back} Days)", is_agent_table=False, show_overview=True)

        if agent_scans:
            # Split agent scans into enabled and disabled
            enabled_agent_scans = {name: details for name, details in agent_scans.items() if details.get('is_enabled', True)}
            disabled_agent_scans = {name: details for name, details in agent_scans.items() if not details.get('is_enabled', True)}

            if enabled_agent_scans:
                render_scan_table(enabled_agent_scans, "Agent Scans - Enabled", is_agent_table=True, show_overview=False)
            if disabled_agent_scans:
                render_scan_table(disabled_agent_scans, "Agent Scans - Disabled", is_agent_table=True, show_overview=False)

    def _add_asset_section(self, asset_data, analysis, license_analysis, historical_data=None):
        total = asset_data.get('total_assets', 0)
        licensed = asset_data.get('licensed_assets', 0)
        unlicensed = asset_data.get('unlicensed_assets', 0)
        auth_succeeded = asset_data.get('auth_succeeded', 0)
        auth_not_attempted = asset_data.get('auth_not_attempted', 0)
        auth_failed = asset_data.get('auth_failed', 0)
        success_pct = asset_data.get('auth_succeeded_percentage', 0)

        # Extract historical data if available
        license_7d = historical_data.get('license', {}).get('7_days') if historical_data else None
        license_30d = historical_data.get('license', {}).get('30_days') if historical_data else None
        auth_7d = historical_data.get('authentication', {}).get('7_days') if historical_data else None
        auth_30d = historical_data.get('authentication', {}).get('30_days') if historical_data else None

        self.html_parts.append(f'''
            <div class="section">
                <h2>Assets & Licensing</h2>
                <table style="margin-bottom: 15px;">
                    <thead>
                        <tr>
                            <th></th>
                            <th style="text-align: center;">Current</th>
                            <th style="text-align: center;">7d Ago</th>
                            <th style="text-align: center;">30d Ago</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>Licensed (90d)</td>
                            <td style="text-align: center;">{licensed}</td>
                            <td style="text-align: center;">{license_7d.get('total_licensed_assets', '-') if license_7d else '-'}</td>
                            <td style="text-align: center;">{license_30d.get('total_licensed_assets', '-') if license_30d else '-'}</td>
                        </tr>
                        <tr>
                            <td>Unlicensed</td>
                            <td style="text-align: center;">{unlicensed}</td>
                            <td style="text-align: center;">{license_7d.get('unlicensed_assets', '-') if license_7d else '-'}</td>
                            <td style="text-align: center;">{license_30d.get('unlicensed_assets', '-') if license_30d else '-'}</td>
                        </tr>
                        <tr style="border-top: 2px solid #1E2426;">
                            <td>Total Assets</td>
                            <td style="text-align: center;">{total}</td>
                            <td style="text-align: center;">{license_7d.get('total_assets', '-') if license_7d else '-'}</td>
                            <td style="text-align: center;">{license_30d.get('total_assets', '-') if license_30d else '-'}</td>
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
                            <th style="text-align: center;">Current</th>
                            <th style="text-align: center;">7d Ago</th>
                            <th style="text-align: center;">30d Ago</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>Auth Not Attempted</td>
                            <td style="text-align: center;">{auth_not_attempted}</td>
                            <td style="text-align: center;">{auth_7d.get('auth_not_attempted', '-') if auth_7d else '-'}</td>
                            <td style="text-align: center;">{auth_30d.get('auth_not_attempted', '-') if auth_30d else '-'}</td>
                        </tr>
                        <tr>
                            <td>Auth Failed</td>
                            <td style="text-align: center;">{auth_failed}</td>
                            <td style="text-align: center;">{auth_7d.get('auth_failed', '-') if auth_7d else '-'}</td>
                            <td style="text-align: center;">{auth_30d.get('auth_failed', '-') if auth_30d else '-'}</td>
                        </tr>
                        <tr>
                            <td>Auth Succeeded</td>
                            <td style="text-align: center;">{auth_succeeded}</td>
                            <td style="text-align: center;">{auth_7d.get('auth_succeeded', '-') if auth_7d else '-'}</td>
                            <td style="text-align: center;">{auth_30d.get('auth_succeeded', '-') if auth_30d else '-'}</td>
                        </tr>
                        <tr>
                            <td>Auth Succeeded %</td>
                            <td style="text-align: center;">{success_pct}%</td>
                            <td style="text-align: center;">{f"{auth_7d.get('auth_succeeded_pct', 0):.1f}%" if auth_7d else '-'}</td>
                            <td style="text-align: center;">{f"{auth_30d.get('auth_succeeded_pct', 0):.1f}%" if auth_30d else '-'}</td>
                        </tr>
                    </tbody>
                </table>
            </div>
''')

    def _add_agent_section(self, agent_data, analysis, historical_data=None):
        total = agent_data.get('total_agents', 0)
        online = agent_data.get('online_agents', 0)
        offline = agent_data.get('offline_agents', 0)
        long_offline = agent_data.get('long_offline_agents', 0)
        threshold_days = agent_data.get('offline_threshold_days', 14)

        # Extract historical data if available
        agents_7d = historical_data.get('agents', {}).get('7_days') if historical_data else None
        agents_30d = historical_data.get('agents', {}).get('30_days') if historical_data else None

        self.html_parts.append(f'''
            <div class="section">
                <h2>Agents</h2>
                <table style="margin-bottom: 15px;">
                    <thead>
                        <tr>
                            <th></th>
                            <th style="text-align: center;">Current</th>
                            <th style="text-align: center;">7d Ago</th>
                            <th style="text-align: center;">30d Ago</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>Online</td>
                            <td style="text-align: center;">{online}</td>
                            <td style="text-align: center;">{agents_7d.get('online_agents', '-') if agents_7d else '-'}</td>
                            <td style="text-align: center;">{agents_30d.get('online_agents', '-') if agents_30d else '-'}</td>
                        </tr>
                        <tr>
                            <td>Offline</td>
                            <td style="text-align: center;">{offline}</td>
                            <td style="text-align: center;">{agents_7d.get('offline_agents', '-') if agents_7d else '-'}</td>
                            <td style="text-align: center;">{agents_30d.get('offline_agents', '-') if agents_30d else '-'}</td>
                        </tr>
                        <tr>
                            <td>Offline &gt; {threshold_days} days</td>
                            <td style="text-align: center;">{long_offline}</td>
                            <td style="text-align: center;">{agents_7d.get('long_offline_agents', '-') if agents_7d else '-'}</td>
                            <td style="text-align: center;">{agents_30d.get('long_offline_agents', '-') if agents_30d else '-'}</td>
                        </tr>
                        <tr style="border-top: 2px solid #1E2426;">
                            <td>Total Agents</td>
                            <td style="text-align: center;">{total}</td>
                            <td style="text-align: center;">{agents_7d.get('total_agents', '-') if agents_7d else '-'}</td>
                            <td style="text-align: center;">{agents_30d.get('total_agents', '-') if agents_30d else '-'}</td>
                        </tr>
                    </tbody>
                </table>
''')

        # Add health state distribution
        health_states = agent_data.get('health_states', {})
        if health_states:
            self.html_parts.append('''
                <h3 style="font-size: 13px; margin-top: 15px; margin-bottom: 8px; color: #666;">Health State Distribution</h3>
                <table style="margin-bottom: 15px;">
                    <thead>
                        <tr>
                            <th>Health State</th>
                            <th style="text-align: center;">Agent Count</th>
                        </tr>
                    </thead>
                    <tbody>
''')
            for state, count in sorted(health_states.items(), key=lambda x: x[1], reverse=True):
                self.html_parts.append(f'''
                        <tr>
                            <td>{state}</td>
                            <td style="text-align: center;">{count}</td>
                        </tr>
''')
            self.html_parts.append('''
                    </tbody>
                </table>
''')

        # Add version distribution
        core_versions = agent_data.get('core_versions', {})
        if core_versions:
            self.html_parts.append('''
                <h3 style="font-size: 13px; margin-top: 15px; margin-bottom: 8px; color: #666;">Agent Version Distribution</h3>
                <table style="margin-bottom: 15px;">
                    <thead>
                        <tr>
                            <th>Core Version</th>
                            <th style="text-align: center;">Agent Count</th>
                        </tr>
                    </thead>
                    <tbody>
''')
            for version, count in sorted(core_versions.items(), key=lambda x: x[1], reverse=True):
                self.html_parts.append(f'''
                        <tr>
                            <td>{version}</td>
                            <td style="text-align: center;">{count}</td>
                        </tr>
''')
            self.html_parts.append('''
                    </tbody>
                </table>
''')

        # Add profile distribution
        profiles = agent_data.get('profiles', {})
        if profiles:
            self.html_parts.append('''
                <h3 style="font-size: 13px; margin-top: 15px; margin-bottom: 8px; color: #666;">Agent Profile Distribution</h3>
                <table style="margin-bottom: 15px;">
                    <thead>
                        <tr>
                            <th>Profile Name</th>
                            <th style="text-align: center;">Agent Count</th>
                        </tr>
                    </thead>
                    <tbody>
''')
            for profile, count in sorted(profiles.items(), key=lambda x: x[1], reverse=True):
                self.html_parts.append(f'''
                        <tr>
                            <td>{profile}</td>
                            <td style="text-align: center;">{count}</td>
                        </tr>
''')
            self.html_parts.append('''
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

    def _add_scanner_section(self, scanner_data, analysis, historical_data=None):
        total = scanner_data.get('total_scanners', 0)
        working = scanner_data.get('working_scanners', 0)
        problems = scanner_data.get('problem_scanners', 0)

        # Extract historical data if available
        scanners_7d = historical_data.get('scanners', {}).get('7_days') if historical_data else None
        scanners_30d = historical_data.get('scanners', {}).get('30_days') if historical_data else None

        self.html_parts.append(f'''
            <div class="section">
                <h2>Scanners</h2>
                <table style="margin-bottom: 15px;">
                    <thead>
                        <tr>
                            <th></th>
                            <th style="text-align: center;">Current</th>
                            <th style="text-align: center;">7d Ago</th>
                            <th style="text-align: center;">30d Ago</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>Working</td>
                            <td style="text-align: center;">{working}</td>
                            <td style="text-align: center;">{scanners_7d.get('working_scanners', '-') if scanners_7d else '-'}</td>
                            <td style="text-align: center;">{scanners_30d.get('working_scanners', '-') if scanners_30d else '-'}</td>
                        </tr>
                        <tr>
                            <td>Problems</td>
                            <td style="text-align: center;">{problems}</td>
                            <td style="text-align: center;">{scanners_7d.get('problem_scanners', '-') if scanners_7d else '-'}</td>
                            <td style="text-align: center;">{scanners_30d.get('problem_scanners', '-') if scanners_30d else '-'}</td>
                        </tr>
                        <tr style="border-top: 2px solid #1E2426;">
                            <td>Total Scanners</td>
                            <td style="text-align: center;">{total}</td>
                            <td style="text-align: center;">{scanners_7d.get('total_scanners', '-') if scanners_7d else '-'}</td>
                            <td style="text-align: center;">{scanners_30d.get('total_scanners', '-') if scanners_30d else '-'}</td>
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

    def _add_connector_section(self, connector_data, analysis, historical_data=None):
        total = connector_data.get('total_connectors', 0)
        working = connector_data.get('working_connectors', 0)
        problems = connector_data.get('problem_connectors', 0)

        # Extract historical data if available
        connectors_7d = historical_data.get('connectors', {}).get('7_days') if historical_data else None
        connectors_30d = historical_data.get('connectors', {}).get('30_days') if historical_data else None

        self.html_parts.append(f'''
            <div class="section">
                <h2>Connectors</h2>
                <table style="margin-bottom: 15px;">
                    <thead>
                        <tr>
                            <th></th>
                            <th style="text-align: center;">Current</th>
                            <th style="text-align: center;">7d Ago</th>
                            <th style="text-align: center;">30d Ago</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>Working</td>
                            <td style="text-align: center;">{working}</td>
                            <td style="text-align: center;">{connectors_7d.get('working_connectors', '-') if connectors_7d else '-'}</td>
                            <td style="text-align: center;">{connectors_30d.get('working_connectors', '-') if connectors_30d else '-'}</td>
                        </tr>
                        <tr>
                            <td>Problems</td>
                            <td style="text-align: center;">{problems}</td>
                            <td style="text-align: center;">{connectors_7d.get('problem_connectors', '-') if connectors_7d else '-'}</td>
                            <td style="text-align: center;">{connectors_30d.get('problem_connectors', '-') if connectors_30d else '-'}</td>
                        </tr>
                        <tr style="border-top: 2px solid #1E2426;">
                            <td>Total Connectors</td>
                            <td style="text-align: center;">{total}</td>
                            <td style="text-align: center;">{connectors_7d.get('total_connectors', '-') if connectors_7d else '-'}</td>
                            <td style="text-align: center;">{connectors_30d.get('total_connectors', '-') if connectors_30d else '-'}</td>
                        </tr>
                    </tbody>
                </table>
''')

        self.html_parts.append('            </div>')

    def _add_user_section(self, user_data, analysis, historical_data=None):
        total = user_data.get('total_users', 0)
        enabled = user_data.get('enabled_users', 0)
        disabled = user_data.get('disabled_users', 0)
        no_login = user_data.get('enabled_no_login_30_days', 0)
        role_counts = user_data.get('role_counts', {})
        no_login_list = user_data.get('enabled_no_login_list', [])

        # Extract historical data if available
        users_7d = historical_data.get('users', {}).get('7_days') if historical_data else None
        users_30d = historical_data.get('users', {}).get('30_days') if historical_data else None

        self.html_parts.append(f'''
            <div class="section">
                <h2>User Accounts</h2>
                <table style="margin-bottom: 15px;">
                    <thead>
                        <tr>
                            <th></th>
                            <th style="text-align: center;">Current</th>
                            <th style="text-align: center;">7d Ago</th>
                            <th style="text-align: center;">30d Ago</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>Enabled Users</td>
                            <td style="text-align: center;">{enabled}</td>
                            <td style="text-align: center;">{users_7d.get('enabled_users', '-') if users_7d else '-'}</td>
                            <td style="text-align: center;">{users_30d.get('enabled_users', '-') if users_30d else '-'}</td>
                        </tr>
                        <tr>
                            <td>Disabled Users</td>
                            <td style="text-align: center;">{disabled}</td>
                            <td style="text-align: center;">{users_7d.get('disabled_users', '-') if users_7d else '-'}</td>
                            <td style="text-align: center;">{users_30d.get('disabled_users', '-') if users_30d else '-'}</td>
                        </tr>
                        <tr>
                            <td>No Login 30+ Days</td>
                            <td style="text-align: center;">{no_login}</td>
                            <td style="text-align: center;">{users_7d.get('enabled_no_login_30_days', '-') if users_7d else '-'}</td>
                            <td style="text-align: center;">{users_30d.get('enabled_no_login_30_days', '-') if users_30d else '-'}</td>
                        </tr>
                        <tr style="border-top: 2px solid #1E2426;">
                            <td>Total Users</td>
                            <td style="text-align: center;">{total}</td>
                            <td style="text-align: center;">{users_7d.get('total_users', '-') if users_7d else '-'}</td>
                            <td style="text-align: center;">{users_30d.get('total_users', '-') if users_30d else '-'}</td>
                        </tr>
                    </tbody>
                </table>
''')

        # Add role breakdown if we have roles
        if role_counts:
            self.html_parts.append('''
                <div style="margin-top: 15px;">
                    <h3 style="font-size: 13px; margin-bottom: 8px; color: #1E2426;">Users by Role</h3>
                    <table>
                        <thead>
                            <tr>
                                <th>Role</th>
                                <th style="text-align: center;">Count</th>
                            </tr>
                        </thead>
                        <tbody>
''')
            # Sort roles by count descending
            sorted_roles = sorted(role_counts.items(), key=lambda x: x[1], reverse=True)
            for role, count in sorted_roles:
                self.html_parts.append(f'''
                            <tr>
                                <td>{role}</td>
                                <td style="text-align: center;">{count}</td>
                            </tr>
''')
            self.html_parts.append('''
                        </tbody>
                    </table>
                </div>
''')

        # Add users with no recent login (limited to top 10)
        if no_login_list:
            limited_list = no_login_list[:10]
            self.html_parts.append(f'''
                <div style="margin-top: 15px;">
                    <h3 style="font-size: 13px; margin-bottom: 8px; color: #1E2426;">Enabled Users - No Login in 30+ Days (Top 10)</h3>
                    <table>
                        <thead>
                            <tr>
                                <th>Username</th>
                                <th>Name</th>
                                <th style="text-align: center;">Last Login</th>
                            </tr>
                        </thead>
                        <tbody>
''')
            for user in limited_list:
                self.html_parts.append(f'''
                            <tr>
                                <td>{user['username']}</td>
                                <td>{user['name']}</td>
                                <td style="text-align: center;">{user['last_login']}</td>
                            </tr>
''')
            self.html_parts.append('''
                        </tbody>
                    </table>
''')
            if len(no_login_list) > 10:
                self.html_parts.append(f'''
                    <div style="margin-top: 8px; font-size: 12px; color: #666;">
                        ... and {len(no_login_list) - 10} more users
                    </div>
''')
            self.html_parts.append('                </div>')

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

                // Helper to fill in missing days for 30-day chart
                function fillLast30Days(data, valueKeys) {
                    if (!data || data.length === 0) return { labels: [], datasets: {} };

                    const today = new Date();
                    today.setHours(0, 0, 0, 0);
                    const thirtyDaysAgo = new Date(today);
                    thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);

                    // Create a map of existing data by date
                    const dataMap = {};
                    data.forEach(point => {
                        const date = new Date(point.timestamp);
                        date.setHours(0, 0, 0, 0);
                        const dateKey = date.toISOString().split('T')[0];
                        dataMap[dateKey] = point;
                    });

                    // Fill in all 30 days
                    const labels = [];
                    const datasets = {};
                    valueKeys.forEach(key => datasets[key] = []);

                    let lastValues = {};
                    valueKeys.forEach(key => lastValues[key] = 0);

                    for (let i = 0; i <= 30; i++) {
                        const currentDate = new Date(thirtyDaysAgo);
                        currentDate.setDate(currentDate.getDate() + i);
                        const dateKey = currentDate.toISOString().split('T')[0];

                        labels.push(formatDate(currentDate.toISOString()));

                        if (dataMap[dateKey]) {
                            // Use actual data
                            valueKeys.forEach(key => {
                                const value = dataMap[dateKey][key] || 0;
                                datasets[key].push(value);
                                lastValues[key] = value;
                            });
                        } else {
                            // Use last known value
                            valueKeys.forEach(key => {
                                datasets[key].push(lastValues[key]);
                            });
                        }
                    }

                    return { labels, datasets };
                }

                // Chart defaults for Tenable branding
                Chart.defaults.font.family = "'Work Sans', sans-serif";
                Chart.defaults.font.size = 11;

                // Authentication Success Rate Chart
                const authDataRaw = trendsData.authentication || [];
                const authFilled = fillLast30Days(authDataRaw, ['auth_succeeded_pct']);
                const authChart = new Chart(document.getElementById('authChart'), {
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
                const licenseDataRaw = trendsData.license || [];
                const licenseFilled = fillLast30Days(licenseDataRaw, ['total_licensed_assets']);
                const licenseChart = new Chart(document.getElementById('licenseChart'), {
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
                const agentDataRaw = trendsData.agents || [];
                const agentFilled = fillLast30Days(agentDataRaw, ['online_agents', 'offline_agents']);
                const agentChart = new Chart(document.getElementById('agentChart'), {
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
                                pointBackgroundColor: '#1E2426',
                                pointRadius: 3
                            },
                            {
                                label: 'Offline Agents',
                                data: agentFilled.datasets.offline_agents,
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
                                ticks: {
                                    stepSize: 1,
                                    callback: value => Math.floor(value)
                                },
                                grid: { color: '#e0e0e0' }
                            },
                            x: { grid: { display: false } }
                        }
                    }
                });

                // Scanner Status Chart
                const scannerDataRaw = trendsData.scanners || [];
                const scannerFilled = fillLast30Days(scannerDataRaw, ['working_scanners', 'problem_scanners']);
                const scannerChart = new Chart(document.getElementById('scannerChart'), {
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
                                pointBackgroundColor: '#1E2426',
                                pointRadius: 3
                            },
                            {
                                label: 'Problem Scanners',
                                data: scannerFilled.datasets.problem_scanners,
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
                                ticks: {
                                    stepSize: 1,
                                    callback: value => Math.floor(value)
                                },
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
