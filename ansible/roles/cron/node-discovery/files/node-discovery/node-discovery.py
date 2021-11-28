import json
import logging
import os
import requests
from slack_service import SlackService

log_level = os.environ.get('LOG_LEVEL', 'INFO').upper()
logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=log_level,
    datefmt='%Y-%m-%d %H:%M:%S')

nomad_config_file = '/etc/nomad.d/nomad.json'
nomad_config_file_tmp = '/etc/nomad.d/nomad.json.tmp'
own_ip = os.popen('hostname --all-ip-addresses | awk \'{print $2}\'').read().strip()

slack = SlackService()
logging.info("Starting node discovery")


def discover_nomad_nodes():
    api_key = os.getenv('LINODE_API_KEY')
    api_url = "https://api.linode.com/v4/linode/instances"
    req = requests.get(url=api_url, headers={'Authorization': f'Bearer {api_key}'})

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
                    is_server = is_a_server(host_ip)
                    logging.info(f'Discovered {"server" if is_server else "client"} node {label} with IP {host_ip}')
                except (Exception,):
                    has_errors = True
                nodes.append({
                    'label': label,
                    'ip': host_ip,
                    'is_server': is_server,
                    'has_errors': has_errors,
                    'is_self': host_ip == own_ip
                })
        return nodes
    else:
        logging.error(f'Error retrieving Linode instances. Code: {req.status_code}')
        return []


def is_a_server(ip):
    try:
        req = requests.get(f'http://{ip}:4646/v1/agent/self')
        if req.status_code == 200:
            return req.json()['stats']['nomad']['server'] == "true"
    except (Exception,):
        logging.error(f'Error retrieving agent information in {ip}')
    return False


def read_nomad_config_file():
    with open(nomad_config_file, 'r', encoding="utf8") as f:
        return json.load(f)


def join_cluster(nomad_nodes):
    servers = list(filter(lambda node: node['is_server'] is True, nomad_nodes))
    joined = False
    for server in servers:
        if not server['is_self'] and not joined:
            logging.info(f"Trying to join server on {server['ip']}")
            joined = os.system(f"nomad server join {server['ip']}") == 0
    return joined


def service_action(service_name, action):
    if os.system(f'systemctl {action} {service_name}') == 0:
        logging.info(f'{service_name} service {action}')
    else:
        logging.error(f'Failed executing {action} on service {service_name}')


def nomad_running_properly():
    return os.system('nomad agent-info > /dev/null 2>&1') == 0


def is_node_connected_to_cluster(nodes):
    connected_members = os.popen('nomad server members | grep alive').read()
    logging.debug(f'Connected members: {connected_members}')
    return connected_members >= len(nodes)


def is_node_healthy(nodes):
    try:
        req = requests.get(f'http://0.0.0.0:4646/v1/agent/self')
        node_healthy = req.status_code == 200 and req.json()['member']['Status'] == "alive"
        connected_to_cluster = is_node_connected_to_cluster(nodes)
        return node_healthy and connected_to_cluster
    except (Exception,):
        pass
    return False


def main():
    nodes = discover_nomad_nodes()
    if not is_node_healthy(nodes): # TODO: Fix is_node_healthy logic
        if join_cluster(nodes):
            logging.info('Joined cluster successfully!')
            slack.send_message(f':green_heart:Node {own_ip} joined the cluster successfully')
        else:
            logging.error('Could not join cluster')
            slack.send_message(f':fire::fire:Error joining the cluster from {own_ip}')
            pass
    else:
        logging.debug('Node running properly, nothing to do')


main()
