from datetime import datetime


class HTMLReporter:
    def __init__(self):
        self.html_parts = []

    def generate(self, run_data, analysis_results, claude_analysis=None):
        timestamp = run_data.get('timestamp', 'Unknown')
        data = run_data.get('data', {})

        self._add_header(timestamp)

        # Add Claude analysis at the top if available
        if claude_analysis and not claude_analysis.get('error'):
            self._add_claude_section(claude_analysis)

        self._add_scan_section(data.get('scans', {}), analysis_results.get('scans', {}))
        self._add_asset_section(data.get('assets', {}), analysis_results.get('assets', {}))
        self._add_license_section(data.get('license', {}), analysis_results.get('license', {}))
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
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        .header h1 { font-size: 28px; margin-bottom: 10px; }
        .header .timestamp { font-size: 14px; opacity: 0.9; }
        .content { padding: 30px; }
        .section {
            margin-bottom: 40px;
            border-left: 4px solid #667eea;
            padding-left: 20px;
        }
        .section h2 {
            color: #667eea;
            font-size: 20px;
            margin-bottom: 15px;
        }
        .stat-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }
        .stat-card {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 6px;
            border-left: 3px solid #667eea;
        }
        .stat-card .label {
            font-size: 12px;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 5px;
        }
        .stat-card .value {
            font-size: 24px;
            font-weight: bold;
            color: #333;
        }
        .stat-card.warning { border-left-color: #ffa500; }
        .stat-card.warning .value { color: #ffa500; }
        .stat-card.success { border-left-color: #28a745; }
        .stat-card.success .value { color: #28a745; }
        .stat-card.danger { border-left-color: #dc3545; }
        .stat-card.danger .value { color: #dc3545; }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
            background: white;
        }
        th {
            background: #f8f9fa;
            padding: 12px;
            text-align: left;
            font-weight: 600;
            color: #495057;
            border-bottom: 2px solid #dee2e6;
        }
        td {
            padding: 12px;
            border-bottom: 1px solid #dee2e6;
        }
        tr:hover { background: #f8f9fa; }
        .badge {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
        }
        .badge.success { background: #d4edda; color: #155724; }
        .badge.warning { background: #fff3cd; color: #856404; }
        .badge.danger { background: #f8d7da; color: #721c24; }
        .change {
            display: inline-flex;
            align-items: center;
            gap: 5px;
            font-size: 14px;
            font-weight: 600;
        }
        .change.positive { color: #28a745; }
        .change.negative { color: #dc3545; }
        .change.neutral { color: #6c757d; }
        .alert {
            padding: 15px;
            border-radius: 6px;
            margin-top: 15px;
        }
        .alert.warning {
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            color: #856404;
        }
        .alert.info {
            background: #d1ecf1;
            border-left: 4px solid #17a2b8;
            color: #0c5460;
        }
        .footer {
            background: #f8f9fa;
            padding: 20px;
            text-align: center;
            color: #6c757d;
            font-size: 14px;
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
            'HEALTHY': '#28a745',
            'WARNING': '#ffc107',
            'CRITICAL': '#dc3545',
            'UNKNOWN': '#6c757d'
        }
        status_color = status_colors.get(status, '#6c757d')
        status_emojis = {
            'HEALTHY': '✓',
            'WARNING': '⚠️',
            'CRITICAL': '🚨',
            'UNKNOWN': '?'
        }
        status_emoji = status_emojis.get(status, '?')

        self.html_parts.append(f'''
            <div class="section" style="background: linear-gradient(135deg, #667eea22 0%, #764ba222 100%); padding: 25px; border-radius: 8px; border-left: 4px solid {status_color};">
                <h2>🧠 AI Executive Summary</h2>
                <div style="display: flex; align-items: center; gap: 15px; margin-bottom: 20px;">
                    <div style="font-size: 48px;">{status_emoji}</div>
                    <div>
                        <div style="font-size: 12px; color: #666; text-transform: uppercase; letter-spacing: 0.5px;">Overall Health Status</div>
                        <div style="font-size: 28px; font-weight: bold; color: {status_color};">{status}</div>
                    </div>
                </div>
''')

        if claude_analysis.get('executive_summary'):
            summary = claude_analysis['executive_summary'].replace('\n', '<br>')
            self.html_parts.append(f'''
                <div style="background: white; padding: 20px; border-radius: 6px; margin-bottom: 20px; border-left: 3px solid #667eea;">
                    <h3 style="color: #667eea; font-size: 16px; margin-bottom: 10px;">📋 Summary</h3>
                    <p style="line-height: 1.8; color: #333;">{summary}</p>
                </div>
''')

        if claude_analysis.get('key_concerns'):
            self.html_parts.append('''
                <div style="background: white; padding: 20px; border-radius: 6px; margin-bottom: 20px; border-left: 3px solid #dc3545;">
                    <h3 style="color: #dc3545; font-size: 16px; margin-bottom: 15px;">🚨 Key Concerns</h3>
                    <ul style="margin-left: 20px; line-height: 2;">
''')
            for concern in claude_analysis['key_concerns']:
                self.html_parts.append(f'                        <li style="color: #333;">{concern}</li>')
            self.html_parts.append('''
                    </ul>
                </div>
''')

        if claude_analysis.get('recommendations'):
            self.html_parts.append('''
                <div style="background: white; padding: 20px; border-radius: 6px; margin-bottom: 20px; border-left: 3px solid #ffc107;">
                    <h3 style="color: #ffc107; font-size: 16px; margin-bottom: 15px;">💡 Recommendations</h3>
''')
            for rec in claude_analysis['recommendations']:
                priority = rec.get('priority', 'medium').upper()
                priority_colors = {
                    'HIGH': '#dc3545',
                    'MEDIUM': '#ffc107',
                    'LOW': '#17a2b8'
                }
                priority_color = priority_colors.get(priority, '#6c757d')
                issue = rec.get('issue', 'N/A')
                action = rec.get('action', 'N/A')

                self.html_parts.append(f'''
                    <div style="margin-bottom: 15px; padding: 15px; background: #f8f9fa; border-radius: 6px; border-left: 3px solid {priority_color};">
                        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 8px;">
                            <span style="background: {priority_color}; color: white; padding: 4px 8px; border-radius: 4px; font-size: 11px; font-weight: bold;">{priority}</span>
                            <strong style="color: #333;">{issue}</strong>
                        </div>
                        <div style="color: #666; padding-left: 10px; border-left: 2px solid #dee2e6;">
                            → {action}
                        </div>
                    </div>
''')
            self.html_parts.append('''
                </div>
''')

        if claude_analysis.get('trends'):
            self.html_parts.append('''
                <div style="background: white; padding: 20px; border-radius: 6px; border-left: 3px solid #17a2b8;">
                    <h3 style="color: #17a2b8; font-size: 16px; margin-bottom: 15px;">📈 Trends to Monitor</h3>
                    <ul style="margin-left: 20px; line-height: 2;">
''')
            for trend in claude_analysis['trends']:
                self.html_parts.append(f'                        <li style="color: #333;">{trend}</li>')
            self.html_parts.append('''
                    </ul>
                </div>
''')

        self.html_parts.append('            </div>')

    def _add_scan_section(self, scan_data, analysis):
        total = scan_data.get('total_scans', 0)
        problems = len(scan_data.get('problem_scans', []))
        completed = len(scan_data.get('completed_scans', []))

        status_class = 'success' if problems == 0 else 'warning' if problems < 5 else 'danger'

        self.html_parts.append('''
            <div class="section">
                <h2>📊 Scan Health</h2>
                <div class="stat-grid">
                    <div class="stat-card">
                        <div class="label">Total Scans</div>
                        <div class="value">''' + str(total) + '''</div>
                    </div>
                    <div class="stat-card success">
                        <div class="label">Completed</div>
                        <div class="value">''' + str(completed) + '''</div>
                    </div>
                    <div class="stat-card ''' + status_class + '''">
                        <div class="label">Problem Scans</div>
                        <div class="value">''' + str(problems) + '''</div>
                    </div>
                </div>
''')

        if scan_data.get('problem_scans'):
            self.html_parts.append('''
                <table>
                    <thead>
                        <tr>
                            <th>Scan Name</th>
                            <th>Status</th>
                            <th>Last Modified</th>
                        </tr>
                    </thead>
                    <tbody>
''')
            for scan in scan_data['problem_scans']:
                status_badge = 'danger' if scan['status'] in ['aborted', 'stopped'] else 'warning'
                mod_date = datetime.fromtimestamp(scan['last_modification_date']).strftime('%Y-%m-%d %H:%M')
                self.html_parts.append(f'''
                        <tr>
                            <td>{scan['name']}</td>
                            <td><span class="badge {status_badge}">{scan['status']}</span></td>
                            <td>{mod_date}</td>
                        </tr>
''')
            self.html_parts.append('''
                    </tbody>
                </table>
''')

        if analysis.get('has_previous_data'):
            change = analysis.get('change', 0)
            change_class = 'positive' if change < 0 else 'negative' if change > 0 else 'neutral'
            arrow = '↓' if change < 0 else '↑' if change > 0 else '→'
            self.html_parts.append(f'''
                <div class="alert info">
                    <strong>Change from previous run:</strong>
                    <span class="change {change_class}">{arrow} {abs(change)} problem scans</span>
                </div>
''')

        self.html_parts.append('            </div>')

    def _add_asset_section(self, asset_data, analysis):
        total = asset_data.get('total_assets', 0)
        licensed = asset_data.get('licensed_assets', 0)
        auth_succeeded = asset_data.get('auth_succeeded', 0)
        auth_not_attempted = asset_data.get('auth_not_attempted', 0)
        auth_failed = asset_data.get('auth_failed', 0)
        success_pct = asset_data.get('auth_succeeded_percentage', 0)

        status_class = 'success' if success_pct >= 80 else 'warning' if success_pct >= 60 else 'danger'

        self.html_parts.append(f'''
            <div class="section">
                <h2>🔐 Asset Authentication Status</h2>
                <div class="stat-grid">
                    <div class="stat-card">
                        <div class="label">Total Assets</div>
                        <div class="value">{total}</div>
                    </div>
                    <div class="stat-card">
                        <div class="label">Licensed Assets (90d)</div>
                        <div class="value">{licensed}</div>
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

        if analysis.get('has_previous_data'):
            change_pct = analysis.get('change_percentage', 0)
            is_significant = analysis.get('is_significant_change', False)
            change_class = 'positive' if change_pct > 0 else 'negative' if change_pct < 0 else 'neutral'
            arrow = '↑' if change_pct > 0 else '↓' if change_pct < 0 else '→'

            alert_class = 'warning' if is_significant else 'info'
            self.html_parts.append(f'''
                <div class="alert {alert_class}">
                    <strong>Change from previous run:</strong>
                    <span class="change {change_class}">{arrow} {abs(change_pct):.2f}%</span>
''')
            if is_significant:
                self.html_parts.append(f'''
                    <br><strong>⚠️ SIGNIFICANT CHANGE detected</strong> (threshold: {analysis['threshold']}%)
''')
            self.html_parts.append('                </div>')

        self.html_parts.append('            </div>')

    def _add_license_section(self, license_data, analysis):
        total = license_data.get('total_assets', 0)
        licensed = license_data.get('total_licensed_assets', 0)
        unlicensed = license_data.get('unlicensed_assets', 0)

        self.html_parts.append(f'''
            <div class="section">
                <h2>📈 Licensed Asset Count</h2>
                <div class="stat-grid">
                    <div class="stat-card">
                        <div class="label">Total Assets</div>
                        <div class="value">{total}</div>
                    </div>
                    <div class="stat-card success">
                        <div class="label">Licensed Assets</div>
                        <div class="value">{licensed}</div>
                    </div>
                    <div class="stat-card">
                        <div class="label">Unlicensed</div>
                        <div class="value">{unlicensed}</div>
                    </div>
                </div>
''')

        if analysis.get('has_previous_data'):
            change = analysis.get('change_count', 0)
            change_pct = analysis.get('change_percentage', 0)
            is_significant = analysis.get('is_significant_change', False)
            change_class = 'positive' if change > 0 else 'negative' if change < 0 else 'neutral'
            arrow = '↑' if change > 0 else '↓' if change < 0 else '→'

            alert_class = 'warning' if is_significant else 'info'
            self.html_parts.append(f'''
                <div class="alert {alert_class}">
                    <strong>Change from previous run:</strong>
                    <span class="change {change_class}">{arrow} {abs(change)} licensed assets ({change_pct:+.2f}%)</span>
''')
            if is_significant:
                self.html_parts.append(f'''
                    <br><strong>⚠️ SIGNIFICANT CHANGE detected</strong> (threshold: {analysis['threshold']}%)
''')
            self.html_parts.append('                </div>')

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

    def _add_footer(self):
        self.html_parts.append('''
        </div>
        <div class="footer">
            Generated by Tenable Health Check Agent |
            <a href="https://github.com/d-zito/tenable-healthcheck-agent" style="color: #667eea; text-decoration: none;">GitHub</a>
        </div>
    </div>
</body>
</html>
''')
