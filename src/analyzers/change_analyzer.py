class ChangeAnalyzer:
    def __init__(self, thresholds):
        self.thresholds = thresholds

    def analyze_scans(self, current_data, previous_data):
        """Analyze scan activity over the specified time period."""
        if not previous_data:
            return {
                'has_previous_data': False,
                'message': 'First run - no previous data to compare'
            }

        current_launches = current_data.get('total_launches', 0)
        prev_launches = previous_data.get('data', {}).get('scans', {}).get('total_launches', 0)

        current_running = current_data.get('currently_running', 0)
        prev_running = previous_data.get('data', {}).get('scans', {}).get('currently_running', 0)

        return {
            'has_previous_data': True,
            'current_launches': current_launches,
            'previous_launches': prev_launches,
            'launches_change': current_launches - prev_launches,
            'current_running': current_running,
            'previous_running': prev_running,
            'running_change': current_running - prev_running
        }

    def analyze_credentials(self, current_data, previous_data):
        if not previous_data:
            return {
                'has_previous_data': False,
                'message': 'First run - no previous data to compare'
            }

        current_pct = current_data.get('auth_succeeded_percentage', 0)
        prev_pct = previous_data.get('data', {}).get('assets', {}).get('auth_succeeded_percentage', 0)

        change_pct = current_pct - prev_pct
        threshold = self.thresholds.get('credential_scan_change_percent', 10)

        is_significant = abs(change_pct) >= threshold

        return {
            'has_previous_data': True,
            'current_percentage': current_pct,
            'previous_percentage': prev_pct,
            'change_percentage': round(change_pct, 2),
            'is_significant_change': is_significant,
            'threshold': threshold
        }

    def analyze_license(self, current_data, previous_data):
        """Analyze license usage from asset data (assets scanned in past 90 days)."""
        if not previous_data:
            return {
                'has_previous_data': False,
                'message': 'First run - no previous data to compare'
            }

        current_licensed = current_data.get('licensed_assets', 0)
        prev_licensed = previous_data.get('data', {}).get('assets', {}).get('licensed_assets', 0)

        change_count = current_licensed - prev_licensed

        if prev_licensed > 0:
            change_pct = (change_count / prev_licensed) * 100
        else:
            change_pct = 0

        threshold = self.thresholds.get('license_change_percent', 5)
        is_significant = abs(change_pct) >= threshold

        return {
            'has_previous_data': True,
            'current_licensed': current_licensed,
            'previous_licensed': prev_licensed,
            'change_count': change_count,
            'change_percentage': round(change_pct, 2),
            'is_significant_change': is_significant,
            'threshold': threshold
        }

    def analyze_agents(self, current_data, previous_data):
        if not previous_data:
            return {
                'has_previous_data': False,
                'message': 'First run - no previous data to compare'
            }

        current_offline = current_data.get('offline_agents', 0)
        current_long_offline = current_data.get('long_offline_agents', 0)

        prev_offline = previous_data.get('data', {}).get('agents', {}).get('offline_agents', 0)
        prev_long_offline = previous_data.get('data', {}).get('agents', {}).get('long_offline_agents', 0)

        # Analyze health state changes
        current_health_states = current_data.get('health_states', {})
        prev_health_states = previous_data.get('data', {}).get('agents', {}).get('health_states', {})
        health_state_changes = self._analyze_distribution_changes(current_health_states, prev_health_states)

        # Analyze version changes
        current_versions = current_data.get('core_versions', {})
        prev_versions = previous_data.get('data', {}).get('agents', {}).get('core_versions', {})
        version_changes = self._analyze_distribution_changes(current_versions, prev_versions)

        # Analyze profile changes
        current_profiles = current_data.get('profiles', {})
        prev_profiles = previous_data.get('data', {}).get('agents', {}).get('profiles', {})
        profile_changes = self._analyze_distribution_changes(current_profiles, prev_profiles)

        return {
            'has_previous_data': True,
            'current_offline': current_offline,
            'previous_offline': prev_offline,
            'offline_change': current_offline - prev_offline,
            'current_long_offline': current_long_offline,
            'previous_long_offline': prev_long_offline,
            'long_offline_change': current_long_offline - prev_long_offline,
            'health_state_changes': health_state_changes,
            'version_changes': version_changes,
            'profile_changes': profile_changes
        }

    def _analyze_distribution_changes(self, current_dist, prev_dist):
        """Analyze changes in a distribution (health states, versions, profiles)."""
        all_keys = set(current_dist.keys()) | set(prev_dist.keys())

        changes = {
            'new_items': [],      # Items that appeared
            'removed_items': [],  # Items that disappeared
            'increased': [],      # Items with increased count
            'decreased': []       # Items with decreased count
        }

        for key in all_keys:
            current_count = current_dist.get(key, 0)
            prev_count = prev_dist.get(key, 0)

            if prev_count == 0 and current_count > 0:
                changes['new_items'].append({'name': key, 'count': current_count})
            elif current_count == 0 and prev_count > 0:
                changes['removed_items'].append({'name': key, 'count': prev_count})
            elif current_count > prev_count:
                changes['increased'].append({
                    'name': key,
                    'current': current_count,
                    'previous': prev_count,
                    'change': current_count - prev_count
                })
            elif current_count < prev_count:
                changes['decreased'].append({
                    'name': key,
                    'current': current_count,
                    'previous': prev_count,
                    'change': prev_count - current_count
                })

        return changes

    def analyze_scanners(self, current_data, previous_data):
        if not previous_data:
            return {
                'has_previous_data': False,
                'message': 'First run - no previous data to compare',
                'new_problem_scanners': current_data.get('problem_scanner_list', []),
                'recovered_scanners': []
            }

        current_problems = current_data.get('problem_scanner_list', [])
        prev_problems = previous_data.get('data', {}).get('scanners', {}).get('problem_scanner_list', [])

        current_problem_ids = {s['id'] for s in current_problems}
        prev_problem_ids = {s['id'] for s in prev_problems}

        new_problems = [s for s in current_problems if s['id'] not in prev_problem_ids]
        recovered = [s for s in prev_problems if s['id'] not in current_problem_ids]

        return {
            'has_previous_data': True,
            'current_problem_count': len(current_problems),
            'previous_problem_count': len(prev_problems),
            'new_problem_scanners': new_problems,
            'recovered_scanners': recovered,
            'ongoing_problem_scanners': [s for s in current_problems if s['id'] in prev_problem_ids]
        }

    def analyze_connectors(self, current_data, previous_data):
        if not previous_data:
            return {
                'has_previous_data': False,
                'message': 'First run - no previous data to compare',
                'new_problem_connectors': current_data.get('problem_connector_list', []),
                'recovered_connectors': []
            }

        current_problems = current_data.get('problem_connector_list', [])
        prev_problems = previous_data.get('data', {}).get('connectors', {}).get('problem_connector_list', [])

        current_problem_ids = {c['id'] for c in current_problems}
        prev_problem_ids = {c['id'] for c in prev_problems}

        new_problems = [c for c in current_problems if c['id'] not in prev_problem_ids]
        recovered = [c for c in prev_problems if c['id'] not in current_problem_ids]

        return {
            'has_previous_data': True,
            'current_problem_count': len(current_problems),
            'previous_problem_count': len(prev_problems),
            'new_problem_connectors': new_problems,
            'recovered_connectors': recovered,
            'ongoing_problem_connectors': [c for c in current_problems if c['id'] in prev_problem_ids]
        }

    def analyze_users(self, current_data, previous_data):
        if not previous_data:
            return {
                'has_previous_data': False,
                'message': 'First run - no previous data to compare'
            }

        current_total = current_data.get('total_users', 0)
        current_enabled = current_data.get('enabled_users', 0)
        current_disabled = current_data.get('disabled_users', 0)
        current_new = current_data.get('new_users_30_days', 0)
        current_no_login = current_data.get('enabled_no_login_30_days', 0)

        prev_total = previous_data.get('data', {}).get('users', {}).get('total_users', 0)
        prev_enabled = previous_data.get('data', {}).get('users', {}).get('enabled_users', 0)
        prev_disabled = previous_data.get('data', {}).get('users', {}).get('disabled_users', 0)
        prev_no_login = previous_data.get('data', {}).get('users', {}).get('enabled_no_login_30_days', 0)

        return {
            'has_previous_data': True,
            'current_total': current_total,
            'previous_total': prev_total,
            'total_change': current_total - prev_total,
            'current_enabled': current_enabled,
            'previous_enabled': prev_enabled,
            'enabled_change': current_enabled - prev_enabled,
            'current_disabled': current_disabled,
            'previous_disabled': prev_disabled,
            'disabled_change': current_disabled - prev_disabled,
            'current_no_login': current_no_login,
            'previous_no_login': prev_no_login,
            'no_login_change': current_no_login - prev_no_login
        }
