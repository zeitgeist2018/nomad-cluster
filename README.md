## Requirements
You need to install the following:
* [tfenv](https://github.com/tfutils/tfenv)

## Preparations
* Create the file `terraform/terraform.tfvars`, and provide the following content:
   ```
   linode_token = "Your Linode API key. It needs to have write access for Linodes and StackScripts"
   slack_token = "Your Slack token. It needs to have the scopes chat:write and chat:write.public"
   ```
* In your Slack workspace, create the channel `#infrastructure-events`

## Available commands

* `make tf-plan`: Calculate Terraform plan
* `make tf-apply`: Deploy the cluster in Linode
* `make tf-destroy`: 🔥Destroy the whole cluster🔥
* `NODE=${node number} make ssh-node`: SSH into a node

## Provisioning
The nodes will provision themselves, it will take some minutes.
They will send a message to the Slack channel to inform you about important events.
Also, you can `ssh` into a node, and see provisioning logs with `tail -f /var/log/provision/provision.log`.
