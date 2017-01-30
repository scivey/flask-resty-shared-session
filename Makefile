clean:
	./scripts/clean.sh

release:
	./scripts/release.sh

test:
	./scripts/run-tests.sh

.PHONY: clean release test

