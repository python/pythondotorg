.PHONY: fmt
fmt:
	@terraform fmt ./**/*.tf

.PHONY: check
check:
	@terraform validate

.PHONY: yolo
yolo:
	@echo "Wise, you are not..."
	@terraform apply -auto-approve