NODE?=0
NODE_IP := $(shell cat "./terraform/output/nomad-node-ip-${NODE}.txt")

tf-plan:
	make -C terraform plan

tf-apply: tf-plan
	make -C terraform apply

tf-destroy:
	make -C terraform destroy

ssh-node:
	ssh -i ./terraform/output/private-key.pem "root@${NODE_IP}"
