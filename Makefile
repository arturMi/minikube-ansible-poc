# Short commands for the demo. Every target is a thin wrapper around one command,
# so you can always copy that command and run it yourself.
#
#   make deploy                  build + deploy (starts Minikube if needed)
#   make deploy VERSION=1.1.0    roll out a new version
#   make deploy REPLICAS=5       scale to 5 pods

.DEFAULT_GOAL := help

# Keep these in sync with ansible/group_vars/all.yml
APP       := hello-app
NAMESPACE := demo
KUBECTL   := kubectl --context=minikube --namespace=$(NAMESPACE)

# Hand VERSION / REPLICAS over to Ansible only if they were given
ANSIBLE_VARS :=
ifdef VERSION
  ANSIBLE_VARS += -e app_version=$(VERSION)
endif
ifdef REPLICAS
  ANSIBLE_VARS += -e app_replicas=$(REPLICAS)
endif

.PHONY: help deploy open status logs test destroy stop

help: ## Show all commands
	@awk 'BEGIN {FS = ":.*## "} /^[a-z]+:.*## / {printf "  make %-8s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

deploy: ## Build the image and deploy it to Minikube (optional: VERSION=... REPLICAS=...)
	ansible-playbook -i ansible/inventory.ini ansible/deploy.yml $(ANSIBLE_VARS)

open: ## Open the app in your browser
	minikube service $(APP) --namespace=$(NAMESPACE)

status: ## Show the deployment, the pods and the service
	$(KUBECTL) get deployment,pods,service -o wide

logs: ## Show the latest log lines of every pod
	$(KUBECTL) logs --selector=app=$(APP) --prefix --tail=20

test: ## Run the unit tests of the app
	python3 -m pytest app

destroy: ## Remove the app from Minikube (Minikube keeps running)
	ansible-playbook -i ansible/inventory.ini ansible/destroy.yml

stop: ## Stop Minikube (make deploy starts it again)
	minikube stop
