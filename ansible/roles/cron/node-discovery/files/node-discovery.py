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
                is_server = is_a_server(host_ip)
                logging.info(f'Discovered {"server" if is_server else "client"} node {label} with IP {host_ip}')
                nodes.append({
                    'label': label,
                    'ip': host_ip,
                    'is_server': is_server,
                    'is_self': host_ip == own_ip
                })
        return nodes
    else:
        logging.error(f'Error retrieving Linode instances. Code: {req.status_code}')
        return []


def is_a_server(ip):
    req = requests.get(f'http://{ip}:4646/v1/agent/self')
    if req.status_code == 200:
        return req.json()['stats']['nomad']['server'] == "true"
    return False


def update_nomad_configuration(nomad_nodes):
    try:
        f = open(nomad_config_file, 'r', encoding="utf8")
        with f:
            config = json.load(f)
            config_backup = copy.deepcopy(config)
            servers = list(filter(lambda node: node['is_server'] is True, nomad_nodes))
            server_ips = list(map(lambda server: server['ip'], servers))
            config['server']['bootstrap_expect'] = len(servers)
            config['server']['server_join']['retry_join'] = server_ips
            config['client']['server_join']['retry_join'] = server_ips
            if config_diff(config_backup, config):
                logging.info(f'Nomad configuration has changed')
                with open(nomad_config_file_tmp, 'w') as tmp_file:
                    json.dump(config, tmp_file, indent=2)
                    service_action('nomad', 'stop')
                    os.system(f'cp {nomad_config_file_tmp} {nomad_config_file}')
                    service_action('nomad', 'start')
                    return True
            else:
                logging.info('No changes detected')
                print(config_backup)
                print(config)
    except IOError as e:
        logging.error(f'Could not open file: {nomad_config_file}')
        logging.error(e)
        return False


def config_diff(old_config, new_config):
    return old_config != new_config


def service_action(service_name, action):
    if os.system(f'systemctl {action} {service_name}'):
        logging.info(f'{service_name} service {action}')


nodes = discover_nomad_nodes()
config_changed = update_nomad_configuration(nodes)
if config_changed:
    restart_nomad()
