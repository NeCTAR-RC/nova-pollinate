PROJECT=nova-pollinate
REPO=registry.rc.nectar.org.au/nectar

DESCRIBE=$(shell git describe --tags --always)
IMAGE_TAG := $(if $(TAG),$(TAG),$(DESCRIBE))
VERSION=$(shell echo $(DESCRIBE) | sed -e 's/-[[:digit:]]\+-g/+/')
IMAGE=$(REPO)/$(PROJECT):$(IMAGE_TAG)
BUILDER=docker
BUILDER_ARGS=


build:
	@echo "Image tag: $(IMAGE_TAG)"
	$(BUILDER) build -f docker/Dockerfile --build-arg VERSION=$(VERSION) $(BUILDER_ARGS) -t $(IMAGE) .

push:
	$(BUILDER) push $(IMAGE)

.PHONY: build push
