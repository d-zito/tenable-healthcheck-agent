from datetime import datetime, timedelta


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

        threshold_timestamp = datetime.now() - timedelta(days=self.offline_threshold_days)

        for agent in agents:
            status = agent.get('status', '').lower()
            last_connect = agent.get('last_connect')

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
                    last_connect_dt = datetime.fromtimestamp(last_connect)
                    if last_connect_dt < threshold_timestamp:
                        long_offline_agents.append(agent_info)

        return {
            'total_agents': total_agents,
            'online_agents': online_agents,
            'offline_agents': len(offline_agents),
            'offline_agent_list': offline_agents,
            'long_offline_agents': len(long_offline_agents),
            'long_offline_agent_list': long_offline_agents,
            'offline_threshold_days': self.offline_threshold_days
        }
