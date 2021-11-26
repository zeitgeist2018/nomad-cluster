## Requirements
You need to install `Terraform` and [tfenv](https://github.com/tfutils/tfenv) 

## Preparations
You need to create an API key in Linode, and provide it in a file
called `terraform.tfvars`, inside `terraform` folder.
The key needs to have write access for the following services:
- Linodes
- IP's
- StackScripts

## Available commands

* Deploy cluster: `make tf-apply`
* Destroy cluster: `make tf-destroy`
* SSH into a node: `NODE=${node number} make ssh-node`

## Provisioning
The nodes will provision themselves. It will take some minutes.
You will know it's finished when the file `/provision.txt` is created
in the node.
You can also see the progress by executing `tail -f /var/log/provision/provision.log`.
