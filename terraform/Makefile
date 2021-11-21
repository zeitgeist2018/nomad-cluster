clean:
	@rm -fR terraform.*
	@rm -fR .terraform

init:
	tfenv install
	terraform init

plan: init
	terraform plan -out plan.out -var-file=terraform.tfvars

apply:
	terraform apply plan.out

destroy:
	terraform destroy -var-file=terraform.tfvars

