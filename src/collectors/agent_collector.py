from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from tenable_client import TenableClient


class AgentCollector:
    def __init__(self, tenable_client: TenableClient, offline_threshold_days: int = 14) -> None:
        self.client = tenable_client
        self.offline_threshold_days = offline_threshold_days

    def collect(self) -> dict[str, Any]:
        agents = self.client.list_agents()

        total_agents = len(agents)
        offline_agents: list[dict[str, Any]] = []
        long_offline_agents: list[dict[str, Any]] = []
        online_agents = 0

        health_states: dict[str, int] = {}
        core_versions: dict[str, int] = {}
        profiles: dict[str, int] = {}
        plugin_feed_ids: dict[str, int] = {}

        threshold_timestamp = datetime.now(timezone.utc) - timedelta(days=self.offline_threshold_days)

        for agent in agents:
            status = agent.get('status', '').lower()
            last_connect = agent.get('last_connect')

            health_state = agent.get('health_state_name', 'unknown')
            health_states[health_state] = health_states.get(health_state, 0) + 1

            core_version = agent.get('core_version', 'unknown')
            core_versions[core_version] = core_versions.get(core_version, 0) + 1

            profile_name = agent.get('profile_name', 'unassigned')
            profiles[profile_name] = profiles.get(profile_name, 0) + 1

            plugin_feed_id = agent.get('plugin_feed_id', 'unknown')
            plugin_feed_ids[plugin_feed_id] = plugin_feed_ids.get(plugin_feed_id, 0) + 1

            if status in ('on', 'online'):
                online_agents += 1
            else:
                agent_info: dict[str, Any] = {
                    'id': agent.get('id'),
                    'name': agent.get('name'),
                    'status': status,
                    'last_connect': last_connect,
                }

                offline_agents.append(agent_info)

                if last_connect:
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
            'profiles': profiles,
            'plugin_feed_ids': plugin_feed_ids,
        }
