import json
import os
import requests
from slack_service import SlackService as Slack
from logging_service import LoggingService
from node_service import NodeService

log = LoggingService()

log.info("Starting node discovery")
_node_service = NodeService()
_slack = Slack()

nodes = _node_service.discover_nomad_nodes()

if not _node_service.is_node_healthy(nodes):
    if _node_service.join_cluster(nodes):
        log.info('Joined cluster successfully!')
        _slack.send_message(f':green_heart: Node {_node_service.own_ip} joined the cluster successfully')
    else:
        log.err('Error joining the cluster')
        _slack.send_message(f':fire: Error joining the cluster from {_node_service.own_ip}')
        pass
else:
    log.debug('Node running properly, nothing to do')
