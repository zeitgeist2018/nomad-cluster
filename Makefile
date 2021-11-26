NODE?=0
NODE_IP := $(shell cat "./terraform/output/nomad-node-ip-${NODE}.txt")

tf-plan:
	@make -C terraform plan

tf-apply: tf-plan
	@make -C terraform apply

tf-destroy:
	@make -C terraform destroy
	@rm -r ./terraform/output

ssh-node:
	@ssh -i ./terraform/output/key -o StrictHostKeychecking=no -o IdentitiesOnly=yes "root@${NODE_IP}"
