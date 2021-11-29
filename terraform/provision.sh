#!/bin/bash

mkdir -p /var/log/provision
exec >/var/log/provision/provision.log 2>/var/log/provision/provision-error.log

LINODE_TOKEN="${linode_token}"
SLACK_TOKEN="${slack_token}"
NOMAD_SERVER_COUNT="${nomad_server_count}"

echo "LINODE_TOKEN=\"$LINODE_TOKEN\"" >> /etc/environment
echo "SLACK_TOKEN=\"$SLACK_TOKEN\"" >> /etc/environment
echo "NOMAD_SERVER_COUNT=\"$NOMAD_SERVER_COUNT\"" >> /etc/environment

addAlias(){
  echo "alias $1=\"$2\"" >> /etc/environment
}

prepareSystem() {
  echo $'\e[1;33m'Preparing system$'\e[0m'
  apt update -y
  apt upgrade -y
  apt install -y unzip
  for app in "nomad" "consul"
  do
      addAlias "$app-restart" "systemctl restart $app"
      addAlias "$app-stop" "systemctl stop $app"
      addAlias "$app-logs" "journalctl -u $app -f"
      addAlias "$app-config" "nano /etc/$app.d/$app.json"
  done
}

installAnsible() {
  echo $'\e[1;33m'Installing Ansible$'\e[0m'
  apt-add-repository ppa:ansible/ansible -y
  apt install ansible -y
}

provision() {
  TAG=$(curl -s https://api.github.com/repos/zeitgeist2018/nomad-cluster/releases/latest | jq -r '.tag_name')
  echo $'\e[1;33m'Downloading provisioning assets \("$TAG"\)$'\e[0m'
  wget -O nomad-cluster.zip "https://api.github.com/repos/zeitgeist2018/nomad-cluster/zipball/$TAG"
  unzip nomad-cluster.zip
  rm nomad-cluster.zip
  cd zeitgeist2018*/ansible
  echo $'\e[1;33m'Running Ansible playbook$'\e[0m'
  ansible-playbook main.yml
}


prepareSystem
installAnsible
provision

echo "Node provisioned" > /provision.txt

echo $'\e[1;32m'Node provisioned successfully!$'\e[0m'
