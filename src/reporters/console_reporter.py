from datetime import datetime, timezone
from tabulate import tabulate


class ConsoleReporter:
    def __init__(self):
        self.width = 80

    def print_header(self):
        print("=" * self.width)
        print("TENABLE ONE HEALTH CHECK REPORT".center(self.width))
        # Use UTC timestamp for consistency
        now_utc = datetime.now(timezone.utc)
        print(f"Generated: {now_utc.strftime('%Y-%m-%d %H:%M:%S UTC')}".center(self.width))
        print("=" * self.width)
        print()

    def print_section(self, title):
        print(f"\n{title}")
        print("-" * len(title))

    def print_scans(self, scan_data, analysis):
        days_back = scan_data.get('days_back', 30)
        scan_summary = scan_data.get('scan_summary', {})
        inactive_scans = scan_data.get('inactive_scans', 0)
        total_scans = scan_data.get('total_scans', 0)

        # Split scans by type
        # Agent scans: scan_type is None or 'agent'
        # Remote scans: all other scan types
        agent_scans = {name: details for name, details in scan_summary.items()
                       if details.get('scan_type') in [None, 'agent']}
        network_scans = {name: details for name, details in scan_summary.items()
                         if details.get('scan_type') not in [None, 'agent']}

        # Helper function to print a scan table
        def print_scan_table(scans_dict, title, is_agent_table=False, show_overview=False):
            if not scans_dict:
                return

            self.print_section(title)

            # Show overview for network scans
            if show_overview:
                total_launches = sum(s['total_runs'] for s in scans_dict.values())
                total_failures = sum(s['failed_runs'] for s in scans_dict.values())
                currently_running = sum(1 for s in scans_dict.values() if s.get('running_count', 0) > 0)

                print(f"Total launches: {total_launches}")
                print(f"Currently running: {currently_running}")
                print(f"Scans with activity: {len(scans_dict)}")
                print(f"Total failed runs: {total_failures}")
                if inactive_scans > 0:
                    print(f"Scans configured but not launched in past {days_back} days: {inactive_scans}")
                print()

            sorted_scans = sorted(
                scans_dict.items(),
                key=lambda x: x[1]['total_runs'],
                reverse=True
            )

            table_data = []
            for name, details in sorted_scans:
                is_enabled = details.get('is_enabled', True)
                enabled_str = "✓" if is_enabled else "✗"
                policy_name = details.get('policy', 'N/A')

                total_runs = details['total_runs']
                successful_runs = details.get('completed_runs', details.get('success_runs', 0))
                failed_runs = details['failed_runs']
                running_count = details.get('running_count', 0)

                # Stopped = all intentional user actions
                stopped_runs = details.get('stopped_runs', 0)
                disabled_runs = details.get('disabled_runs', 0)
                canceled_runs = details.get('canceled_runs', 0)
                paused_runs = details.get('paused_runs', 0)
                total_stopped = stopped_runs + disabled_runs + canceled_runs + paused_runs

                # Success rate = successful / (total_runs - running)
                completed_runs = total_runs - running_count
                success_rate = (successful_runs / completed_runs * 100) if completed_runs > 0 else 0

                if is_agent_table:
                    # For agent scans: if agent_scan_launch_type is None or empty, it's scheduled
                    launch_type = details.get('agent_scan_launch_type')
                    if not launch_type:
                        launch_type = 'scheduled'
                    table_data.append([
                        name,
                        policy_name if policy_name else 'N/A',
                        launch_type
                    ])
                else:
                    table_data.append([
                        name,
                        policy_name if policy_name else 'N/A',
                        enabled_str,
                        total_runs,
                        running_count,
                        successful_runs,
                        total_stopped,
                        failed_runs,
                        f"{success_rate:.1f}%"
                    ])

            if is_agent_table:
                headers = ['Scan Name', 'Policy', 'Launch Type']
            else:
                headers = ['Scan Name', 'Policy', 'Enabled', 'Total Runs', 'Running', 'Successful', 'Stopped', 'Failed', 'Success Rate']

            print(tabulate(
                table_data,
                headers=headers,
                tablefmt='simple'
            ))

        # Print network scans first (with overview), then agent scans
        if network_scans:
            print_scan_table(network_scans, f"NETWORK SCANS (Past {days_back} Days)", is_agent_table=False, show_overview=True)

        if agent_scans:
            print_scan_table(agent_scans, "AGENT SCANS", is_agent_table=True, show_overview=False)

    def print_assets(self, asset_data, analysis):
        self.print_section("ASSET AUTHENTICATION STATUS")

        print(f"Total assets: {asset_data['total_assets']}")
        print(f"Licensed assets (scanned in past 90 days): {asset_data['licensed_assets']}")
        print(f"Unlicensed assets: {asset_data['unlicensed_assets']}")

        print(f"\n--- Authentication Analysis (Licensed Assets Only) ---")
        print(f"Authentication succeeded: {asset_data['auth_succeeded']} ({asset_data['auth_succeeded_percentage']}%)")
        print(f"Authentication not attempted: {asset_data['auth_not_attempted']} ({asset_data['auth_not_attempted_percentage']}%)")
        print(f"Authentication attempted but failed: {asset_data['auth_failed']} ({asset_data['auth_failed_percentage']}%)")

        if analysis.get('has_previous_data'):
            change = analysis['change_percentage']
            symbol = "↑" if change > 0 else "↓" if change < 0 else "→"
            print(f"\nChange in successful authentication from previous run: {symbol} {abs(change):.2f}%")

            if analysis.get('is_significant_change'):
                print(f"⚠️  SIGNIFICANT CHANGE detected (threshold: {analysis['threshold']}%)")

    def print_license(self, license_data, analysis):
        self.print_section("LICENSED ASSET COUNT")

        print(f"Total assets: {license_data['total_assets']}")
        print(f"Licensed assets (scanned in past 90 days): {license_data['licensed_assets']}")
        print(f"Unlicensed assets: {license_data['unlicensed_assets']}")

        if analysis.get('has_previous_data'):
            change = analysis['change_count']
            symbol = "↑" if change > 0 else "↓" if change < 0 else "→"
            print(f"\nChange from previous run: {symbol} {abs(change)} licensed assets ({analysis['change_percentage']:+.2f}%)")

            if analysis.get('is_significant_change'):
                print(f"⚠️  SIGNIFICANT CHANGE detected (threshold: {analysis['threshold']}%)")

    def print_agents(self, agent_data, analysis):
        self.print_section("AGENT STATUS")

        print(f"Total agents: {agent_data['total_agents']}")
        print(f"Online: {agent_data['online_agents']}")
        print(f"Offline: {agent_data['offline_agents']}")
        print(f"Offline > {agent_data['offline_threshold_days']} days: {agent_data['long_offline_agents']}")

        # Print health state distribution
        if agent_data.get('health_states'):
            print(f"\n--- Health State Distribution ---")
            health_data = []
            for state, count in sorted(agent_data['health_states'].items(), key=lambda x: x[1], reverse=True):
                health_data.append([state, count])
            print(tabulate(health_data, headers=['Health State', 'Count'], tablefmt='simple'))

        # Print version distribution
        if agent_data.get('core_versions'):
            print(f"\n--- Agent Version Distribution ---")
            version_data = []
            for version, count in sorted(agent_data['core_versions'].items(), key=lambda x: x[1], reverse=True):
                version_data.append([version, count])
            print(tabulate(version_data, headers=['Core Version', 'Count'], tablefmt='simple'))

        # Print profile distribution
        if agent_data.get('profiles'):
            print(f"\n--- Agent Profile Distribution ---")
            profile_data = []
            for profile, count in sorted(agent_data['profiles'].items(), key=lambda x: x[1], reverse=True):
                profile_data.append([profile, count])
            print(tabulate(profile_data, headers=['Profile Name', 'Count'], tablefmt='simple'))

        if agent_data['long_offline_agent_list']:
            print(f"\n--- Agents Offline > {agent_data['offline_threshold_days']} Days ---")
            table_data = [
                [
                    a['name'],
                    a['status'],
                    datetime.fromtimestamp(a['last_connect']).strftime('%Y-%m-%d') if a['last_connect'] else 'Never'
                ]
                for a in agent_data['long_offline_agent_list']
            ]
            print(tabulate(table_data, headers=['Name', 'Status', 'Last Connect'], tablefmt='simple'))

        if analysis.get('has_previous_data'):
            print(f"\n--- Changes from Previous Run ---")
            print(f"Offline agents: {analysis['offline_change']:+d}")
            print(f"Long-term offline: {analysis['long_offline_change']:+d}")

            # Print health state changes
            health_changes = analysis.get('health_state_changes', {})
            if any(health_changes.get(k) for k in ['new_items', 'removed_items', 'increased', 'decreased']):
                print(f"\nHealth State Changes:")
                for item in health_changes.get('new_items', []):
                    print(f"  ✓ New: {item['name']} ({item['count']} agents)")
                for item in health_changes.get('removed_items', []):
                    print(f"  ✗ Removed: {item['name']} (was {item['count']} agents)")
                for item in health_changes.get('increased', []):
                    print(f"  ↑ {item['name']}: {item['previous']} → {item['current']} (+{item['change']})")
                for item in health_changes.get('decreased', []):
                    print(f"  ↓ {item['name']}: {item['previous']} → {item['current']} (-{item['change']})")

            # Print version changes
            version_changes = analysis.get('version_changes', {})
            if any(version_changes.get(k) for k in ['new_items', 'removed_items', 'increased', 'decreased']):
                print(f"\nVersion Changes:")
                for item in version_changes.get('new_items', []):
                    print(f"  ✓ New: {item['name']} ({item['count']} agents)")
                for item in version_changes.get('removed_items', []):
                    print(f"  ✗ Removed: {item['name']} (was {item['count']} agents)")
                for item in version_changes.get('increased', []):
                    print(f"  ↑ {item['name']}: {item['previous']} → {item['current']} (+{item['change']})")
                for item in version_changes.get('decreased', []):
                    print(f"  ↓ {item['name']}: {item['previous']} → {item['current']} (-{item['change']})")

            # Print profile changes
            profile_changes = analysis.get('profile_changes', {})
            if any(profile_changes.get(k) for k in ['new_items', 'removed_items', 'increased', 'decreased']):
                print(f"\nProfile Changes:")
                for item in profile_changes.get('new_items', []):
                    print(f"  ✓ New: {item['name']} ({item['count']} agents)")
                for item in profile_changes.get('removed_items', []):
                    print(f"  ✗ Removed: {item['name']} (was {item['count']} agents)")
                for item in profile_changes.get('increased', []):
                    print(f"  ↑ {item['name']}: {item['previous']} → {item['current']} (+{item['change']})")
                for item in profile_changes.get('decreased', []):
                    print(f"  ↓ {item['name']}: {item['previous']} → {item['current']} (-{item['change']})")

    def print_scanners(self, scanner_data, analysis):
        self.print_section("SCANNER STATUS")

        print(f"Total scanners: {scanner_data['total_scanners']}")
        print(f"Working: {scanner_data['working_scanners']}")
        print(f"Problem scanners: {scanner_data['problem_scanners']}")

        if scanner_data['problem_scanner_list']:
            print("\nProblem Scanners:")
            table_data = [
                [s['name'], s['status'], s['type'], s['scan_count']]
                for s in scanner_data['problem_scanner_list']
            ]
            print(tabulate(table_data, headers=['Name', 'Status', 'Type', 'Scans'], tablefmt='simple'))

        if analysis.get('has_previous_data'):
            if analysis.get('new_problem_scanners'):
                print(f"\n⚠️  NEW problem scanners: {len(analysis['new_problem_scanners'])}")
                for s in analysis['new_problem_scanners']:
                    print(f"  - {s['name']} ({s['status']})")

            if analysis.get('recovered_scanners'):
                print(f"\n✓ Recovered scanners: {len(analysis['recovered_scanners'])}")
                for s in analysis['recovered_scanners']:
                    print(f"  - {s['name']}")

            if analysis.get('ongoing_problem_scanners'):
                print(f"\nOngoing issues: {len(analysis['ongoing_problem_scanners'])} scanners")

    def print_connectors(self, connector_data, analysis):
        self.print_section("CONNECTOR STATUS")

        print(f"Total connectors: {connector_data['total_connectors']}")
        print(f"Working: {connector_data['working_connectors']}")
        print(f"Problem connectors: {connector_data['problem_connectors']}")

        if connector_data['problem_connector_list']:
            print("\nProblem Connectors:")
            table_data = [
                [c['name'], c['status'], c['type']]
                for c in connector_data['problem_connector_list']
            ]
            print(tabulate(table_data, headers=['Name', 'Status', 'Type'], tablefmt='simple'))

        if analysis.get('has_previous_data'):
            if analysis.get('new_problem_connectors'):
                print(f"\n⚠️  NEW problem connectors: {len(analysis['new_problem_connectors'])}")
                for c in analysis['new_problem_connectors']:
                    print(f"  - {c['name']} ({c['status']})")

            if analysis.get('recovered_connectors'):
                print(f"\n✓ Recovered connectors: {len(analysis['recovered_connectors'])}")
                for c in analysis['recovered_connectors']:
                    print(f"  - {c['name']}")

            if analysis.get('ongoing_problem_connectors'):
                print(f"\nOngoing issues: {len(analysis['ongoing_problem_connectors'])} connectors")

    def print_users(self, user_data, analysis):
        self.print_section("USER ACCOUNTS")

        print(f"Total users: {user_data['total_users']}")
        print(f"Enabled users: {user_data['enabled_users']}")
        print(f"Disabled users: {user_data['disabled_users']}")
        print(f"Enabled users with no login in 30+ days: {user_data['enabled_no_login_30_days']}")

        # Show role breakdown
        if user_data['role_counts']:
            print(f"\n--- User Roles ---")
            role_data = []
            for role, count in sorted(user_data['role_counts'].items(), key=lambda x: x[1], reverse=True):
                role_data.append([role, count])
            print(tabulate(role_data, headers=['Role', 'Count'], tablefmt='simple'))

        # Show users with no recent login (limit to top 10)
        if user_data['enabled_no_login_list']:
            print(f"\n--- Enabled Users - No Login in 30+ Days (Top 10) ---")
            limited_list = user_data['enabled_no_login_list'][:10]
            table_data = [
                [u['username'], u['name'], u['last_login']]
                for u in limited_list
            ]
            print(tabulate(table_data, headers=['Username', 'Name', 'Last Login'], tablefmt='simple'))

            if len(user_data['enabled_no_login_list']) > 10:
                print(f"\n... and {len(user_data['enabled_no_login_list']) - 10} more")

        if analysis.get('has_previous_data'):
            print(f"\nChange from previous run:")
            print(f"  Total users: {analysis['total_change']:+d}")
            print(f"  Enabled: {analysis['enabled_change']:+d}")
            print(f"  Disabled: {analysis['disabled_change']:+d}")
            print(f"  No login 30+ days: {analysis['no_login_change']:+d}")

    def print_claude_analysis(self, claude_results):
        self.print_section("AI ANALYSIS (Claude)")

        if 'error' in claude_results:
            print(f"⚠️  {claude_results['error']}")
            if 'help' in claude_results:
                print(f"   {claude_results['help']}")
            return

        status = claude_results.get('health_status', 'unknown').upper()
        status_emoji = {
            'HEALTHY': '✓',
            'WARNING': '⚠️',
            'CRITICAL': '🚨',
            'UNKNOWN': '?'
        }
        print(f"Health Status: {status_emoji.get(status, '?')} {status}")

        if claude_results.get('executive_summary'):
            print(f"\nExecutive Summary:")
            print(claude_results['executive_summary'])

        if claude_results.get('key_concerns'):
            print(f"\nKey Concerns:")
            for concern in claude_results['key_concerns']:
                print(f"  • {concern}")

        if claude_results.get('recommendations'):
            print(f"\nRecommendations:")
            for rec in claude_results['recommendations']:
                priority = rec.get('priority', 'medium').upper()
                print(f"  [{priority}] {rec.get('issue', 'N/A')}")
                print(f"          → {rec.get('action', 'N/A')}")

        if claude_results.get('trends'):
            print(f"\nTrends to Monitor:")
            for trend in claude_results['trends']:
                print(f"  • {trend}")

    def print_footer(self):
        print("\n" + "=" * self.width)
        print("End of Report".center(self.width))
        print("=" * self.width)
