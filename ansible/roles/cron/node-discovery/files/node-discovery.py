import copy
import json
import logging
import os

import requests

logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')

nomad_config_file = '/etc/nomad.d/nomad.json'
nomad_config_file_tmp = '/etc/nomad.d/nomad.json.tmp'

logging.info("Starting node discovery")


def discover_nomad_nodes():
    api_key = os.getenv('LINODE_API_KEY')
    api_url = "https://api.linode.com/v4/linode/instances"
    own_ip = os.popen('hostname --all-ip-addresses | awk \'{print $2}\'').read().strip()
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


def write_nomad_config_file(config):
    with open(nomad_config_file, 'w') as file:
        json.dump(config, file, indent=2)


def read_nomad_config_file():
    with open(nomad_config_file, 'r', encoding="utf8") as f:
        return json.load(f)


def update_nomad_configuration(nomad_nodes):
    try:
        config = read_nomad_config_file()
        config_backup = copy.deepcopy(config)
        servers = list(filter(lambda node: node['is_server'] is True, nomad_nodes))
        server_ips = list(map(lambda server: server['ip'], servers))
        config['server']['server_join']['retry_join'] = server_ips
        config['client']['server_join']['retry_join'] = server_ips
        if config_diff(config_backup, config):
            logging.info(f'Nomad configuration has changed')
            write_nomad_config_file(config)
            return True
        else:
            logging.info('No changes detected')
    except IOError as e:
        logging.error(f'Could not open file: {nomad_config_file}')
        logging.error(e)
    return False


def config_diff(old_config, new_config):
    return old_config != new_config


def service_action(service_name, action):
    if os.system(f'systemctl {action} {service_name}') == 0:
        logging.info(f'{service_name} service {action}')
    else:
        logging.error(f'Failed executing {action} on service {service_name}')


def i_am_the_only_node_and_have_errors(nodes):
    return len(nodes) == 1 and nodes[0]['is_self'] and nodes[0]['has_errors']


def self_heal(nodes):
    logging.info(f'Trying to self-heal...')
    service_action('nomad', 'stop')
    config = read_nomad_config_file()
    config['server']['server_join']['retry_join'] = [nodes[0]['ip']]
    config['client']['server_join']['retry_join'] = [nodes[0]['ip']]
    service_action('nomad', 'start')


def nomad_running_properly():
    return os.system('nomad agent-info > /dev/null 2>&1') == 0


def is_node_running_properly():
    try:
        req = requests.get(f'http://0.0.0.0:4646/v1/agent/self')
        if req.status_code == 200:
            return req.json()['member']['Status'] == "alive"
    except (Exception,):
        pass
    return False


def main():
    if not is_node_running_properly():
        nodes = discover_nomad_nodes()
        if i_am_the_only_node_and_have_errors(nodes):
            self_heal(nodes)
        else:
            if update_nomad_configuration(nodes):
                service_action('nomad', 'restart')
            elif not nomad_running_properly():
                self_heal(nodes)
    else:
        logging.debug('Node running properly, nothing to do')

main()
