
.PHONY: fmt
fmt:
	@tf fmt ../**/*.tf
	@tf fmt ../**/*.tfvars
	@tf fmt ../**/*.tftest.hcl

.PHONY: check
check:
	@tf validate

.PHONY: yolo
yolo:
	@echo "Wise, you are not..."
	@tf apply -auto-approve
