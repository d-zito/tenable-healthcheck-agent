from datetime import datetime, timedelta, timezone


class AgentCollector:
    def __init__(self, tenable_client, offline_threshold_days=14):
        self.client = tenable_client
        self.offline_threshold_days = offline_threshold_days

    def collect(self):
        agents = self.client.list_agents()

        total_agents = len(agents)
        offline_agents = []
        long_offline_agents = []
        online_agents = 0

        # Track health states, versions, and profiles
        health_states = {}
        core_versions = {}
        profiles = {}

        # Use UTC for consistent timestamp comparisons
        threshold_timestamp = datetime.now(timezone.utc) - timedelta(days=self.offline_threshold_days)

        for agent in agents:
            status = agent.get('status', '').lower()
            last_connect = agent.get('last_connect')

            # Track health state
            health_state = agent.get('health_state_name', 'unknown')
            health_states[health_state] = health_states.get(health_state, 0) + 1

            # Track core version
            core_version = agent.get('core_version', 'unknown')
            core_versions[core_version] = core_versions.get(core_version, 0) + 1

            # Track profile
            profile_name = agent.get('profile_name', 'unassigned')
            profiles[profile_name] = profiles.get(profile_name, 0) + 1

            if status == 'on' or status == 'online':
                online_agents += 1
            else:
                agent_info = {
                    'id': agent.get('id'),
                    'name': agent.get('name'),
                    'status': status,
                    'last_connect': last_connect
                }

                offline_agents.append(agent_info)

                if last_connect:
                    # Convert Unix timestamp to UTC datetime
                    last_connect_dt = datetime.fromtimestamp(last_connect, tz=timezone.utc)
                    if last_connect_dt < threshold_timestamp:
                        long_offline_agents.append(agent_info)

        return {
            'total_agents': total_agents,
            'online_agents': online_agents,
            'offline_agents': len(offline_agents),
            'offline_agent_list': offline_agents,
            'long_offline_agents': len(long_offline_agents),
            'long_offline_agent_list': long_offline_agents,
            'offline_threshold_days': self.offline_threshold_days,
            'health_states': health_states,
            'core_versions': core_versions,
            'profiles': profiles
        }
