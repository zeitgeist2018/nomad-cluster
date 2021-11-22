#!/bin/bash

exec >/root/provision-log 2>/root/provision-err

PUBLIC_IP="$(hostname --all-ip-addresses | awk '{print $1}')"
PRIVATE_IP="$(hostname --all-ip-addresses | awk '{print $2}')"

prepareSystem() {
  apt update -y
  apt upgrade -y
  apt install -y unzip
}

installAnsible() {
  apt-add-repository ppa:ansible/ansible -y
  apt install ansible -y
}

provision() {
  wget -O nomad-cluster.zip https://api.github.com/repos/zeitgeist2018/nomad-cluster/zipball/
  unzip nomad-cluster.zip
  rm nomad-cluster.zip
  cd zeitgeist2018*/ansible
  ansible-playbook main.yml
}


prepareSystem
installAnsible
provision

echo "Node provisioned" > /provision.txt

echo "Node provisioned successfully!"
