import json
import os

import requests

from logging_service import LoggingService

log = LoggingService()


class NodeService:
    def __init__(self):
        self.nomad_config_file = '/etc/nomad.d/nomad.json'
        self.nomad_config_file_tmp = '/etc/nomad.d/nomad.json.tmp'
        self.own_ip = os.popen('hostname --all-ip-addresses | awk \'{print $2}\'').read().strip()
        self.api_key = os.getenv('LINODE_API_KEY')

    def discover_nomad_nodes(self):
        api_url = "https://api.linode.com/v4/linode/instances"
        req = requests.get(url=api_url, headers={'Authorization': f'Bearer {self.api_key}'})

        if req.status_code == 200:
            data = req.json()['data']
            nodes = []
            for instance in data:
                label = instance['label']
                group = instance['group']
                status = instance['status']
                valid_ip_addresses = [ip for ip in instance['ipv4'] if ip.startswith('192')]
                if status == 'running' and group == 'Nomad' and len(valid_ip_addresses) == 1:
                    host_ip = valid_ip_addresses[0]
                    has_errors = False
                    is_server = False
                    try:
                        is_server = self.is_a_server(host_ip)
                        log.info(f'Discovered {"server" if is_server else "client"} node {label} with IP {host_ip}')
                    except (Exception,):
                        has_errors = True
                    nodes.append({
                        'label': label,
                        'ip': host_ip,
                        'is_server': is_server,
                        'has_errors': has_errors,
                        'is_self': host_ip == self.own_ip
                    })
            return nodes
        else:
            log.err(f'Error retrieving Linode instances. Code: {req.status_code}')
            return []

    def is_a_server(self, ip):
        try:
            req = requests.get(f'http://{ip}:4646/v1/agent/self')
            if req.status_code == 200:
                return req.json()['stats']['nomad']['server'] == "true"
        except (Exception,):
            log.err(f'Error retrieving agent information in {ip}')
        return False

    def read_nomad_config_file(self):
        with open(self.nomad_config_file, 'r', encoding="utf8") as f:
            return json.load(f)

    def join_cluster(self, nomad_nodes):
        servers = list(filter(lambda node: node['is_server'] is True, nomad_nodes))
        server_joined = False
        client_joined = False
        for server in servers:
            if not server['is_self'] and not server_joined:
                log.info(f"Trying to join server to {server['ip']}")
                server_joined = os.system(f"nomad server join {server['ip']}") == 0
                if server_joined:
                    log.info(f"Trying to join client to {server['ip']}")
                    client_joined = os.system(f"nomad node config -update-servers {server['ip']}") == 0
        return server_joined and client_joined

    def service_action(self, service_name, action):
        if os.system(f'systemctl {action} {service_name}') == 0:
            log.info(f'{service_name} service {action}')
        else:
            log.err(f'Failed executing {action} on service {service_name}')

    def is_node_connected_to_cluster(self, nodes):
        servers_connected = int(os.popen('nomad server members | grep alive | wc -l').read().replace('\n', ''))
        clients_connected = len(json.loads(os
                                       .popen('nomad agent-info -json')
                                       .read()
                                       .replace('\n', '')
                                       )["stats"]["client"]["known_servers"].split(','))
        return servers_connected >= len(nodes) and clients_connected >= len(nodes)

    def is_node_healthy(self, nodes):
        try:
            req = requests.get(f'http://0.0.0.0:4646/v1/agent/self')
            print(req.status_code)
            node_healthy = req.status_code == 200 and req.json()['member']['Status'] == "alive"
            connected_to_cluster = self.is_node_connected_to_cluster(nodes)
            log.info(f"connected_to_cluster: {connected_to_cluster}")
            return node_healthy and connected_to_cluster
        except (Exception,) as e:
            log.err(f'Error checking if node is healthy: {e}')
            pass
        return False
