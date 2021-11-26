#!/bin/bash

exec >/var/log/provision/provision.log 2>/var/log/provision/provision-error.log

PUBLIC_IP="$(hostname --all-ip-addresses | awk '{print $1}')"
PRIVATE_IP="$(hostname --all-ip-addresses | awk '{print $2}')"
LINODE_API_KEY="${linode_api_key}"

echo "LINODE_API_KEY=\"$LINODE_API_KEY\"" >> /etc/environment

prepareSystem() {
  echo $'\e[1;33m'Preparing system$'\e[0m'
  apt update -y
  apt upgrade -y
  apt install -y unzip
}

installAnsible() {
  echo $'\e[1;33m'Installing Ansible$'\e[0m'
  apt-add-repository ppa:ansible/ansible -y
  apt install ansible -y
}

provision() {
  echo $'\e[1;33m'Downloading provisioning assets$'\e[0m'
  wget -O nomad-cluster.zip https://api.github.com/repos/zeitgeist2018/nomad-cluster/zipball/
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
