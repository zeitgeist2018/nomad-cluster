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
  filename = "${local.output_folder}/private-key.pem"
}

resource local_file public_key_file {
  content  = tls_private_key.ssh_key.public_key_pem
  filename = "${local.output_folder}/public-key.pem"
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

resource linode_instance nomad-nodes {
  count           = 2
  image           = "linode/ubuntu21.10"
  label           = "nomad-node-${count.index}"
  group           = "Nomad"
  region          = "ca-central"
  type            = "g6-nanode-1"
  authorized_keys = [chomp(tls_private_key.ssh_key.public_key_openssh)]
  root_pass       = random_password.root_password.result
}
