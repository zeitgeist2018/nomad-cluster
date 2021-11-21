init: clean
	tfenv install
	terraform init

plan: init
	terraform plan -out plan.out -var-file=terraform.tfvars

apply:
	terraform apply -auto-approve out.plan

destroy:
	terraform destroy -var-file=terraform.tfvars

clean:
	@rm -fR terraform.*
	@rm -fR .terraform
