locals {
  output_folder = "output"
}

# SSH key

resource tls_private_key ssh_key {
  algorithm = "RSA"
  rsa_bits  = 4096
}

resource local_file private_key_file {
  content  = tls_private_key.ssh_key.private_key_pem
  filename = "${local.output_folder}/key"
  file_permission = "600"
}

resource local_file public_key_file {
  content  = tls_private_key.ssh_key.public_key_openssh
  filename = "${local.output_folder}/key.pub"
  file_permission = "600"
}

# Root password

resource random_password root_password {
  length           = 16
  special          = true
  override_special = "_%@"
}

resource local_file root_password_file {
  content  = random_password.root_password.result
  filename = "${local.output_folder}/root_password.txt"
}

# Instances

resource linode_stackscript init_script {
  label = "nomad-node-provision"
  description = "Provisions a Nomad node"
  script = templatefile("provision.sh", {
    linode_token = var.linode_token,
    slack_token = var.slack_token,
    nomad_server_count = length(linode_instance.nomad-nodes)
  })
  images = ["linode/ubuntu21.10"]
}

resource linode_instance nomad-nodes {
  count           = 2
  image           = "linode/ubuntu21.10"
  label           = "nomad-node-${count.index}"
  group           = "Nomad"
  tags = ["nomad-node"]
  region          = "ca-central"
  type            = "g6-nanode-1"
  backups_enabled = false
  private_ip = true
  stackscript_id = linode_stackscript.init_script.id
  authorized_keys = [chomp(tls_private_key.ssh_key.public_key_openssh)]
  root_pass       = random_password.root_password.result
}

resource local_file ips_file {
  count = length(linode_instance.nomad-nodes)
  content = linode_instance.nomad-nodes[count.index].ip_address
  filename = "${local.output_folder}/nomad-node-ip-${count.index}.txt"
}
