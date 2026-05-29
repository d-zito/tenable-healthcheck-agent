from datetime import datetime
from tabulate import tabulate


class ConsoleReporter:
    def __init__(self):
        self.width = 80

    def print_header(self):
        print("=" * self.width)
        print("TENABLE ONE HEALTH CHECK REPORT".center(self.width))
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}".center(self.width))
        print("=" * self.width)
        print()

    def print_section(self, title):
        print(f"\n{title}")
        print("-" * len(title))

    def print_scans(self, scan_data, analysis):
        self.print_section("SCAN HEALTH")

        print(f"Total scans checked: {scan_data['total_scans']}")
        print(f"Problem scans: {len(scan_data['problem_scans'])}")
        print(f"Completed scans: {len(scan_data['completed_scans'])}")

        if scan_data['problem_scans']:
            print("\nProblem Scans:")
            table_data = [
                [s['name'], s['status'], datetime.fromtimestamp(s['last_modification_date']).strftime('%Y-%m-%d %H:%M')]
                for s in scan_data['problem_scans']
            ]
            print(tabulate(table_data, headers=['Name', 'Status', 'Last Modified'], tablefmt='simple'))

        if analysis.get('has_previous_data'):
            print(f"\nChange from previous run: {analysis['change']:+d} problem scans")
            if analysis.get('new_problem_scans'):
                print(f"New problem scans: {len(analysis['new_problem_scans'])}")

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
        print(f"Licensed assets: {license_data['total_licensed_assets']}")
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

        if agent_data['long_offline_agent_list']:
            print(f"\nAgents offline > {agent_data['offline_threshold_days']} days:")
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
            print(f"\nChange from previous run:")
            print(f"  Offline agents: {analysis['offline_change']:+d}")
            print(f"  Long-term offline: {analysis['long_offline_change']:+d}")

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
