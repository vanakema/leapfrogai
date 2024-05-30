SHELL := /bin/bash

install:
	python -m pip install ../../src/leapfrogai_sdk
	python -m pip install -e .

dev:
	python -m uvicorn main:app --port 3000 --reload

test-integration:
	cd ../../ && python -m pytest tests/integration/api

setup-env:
	@echo "Running supabase status..."
	$(eval SUPABASE_ANON_KEY := $(shell supabase status | grep -oP '(?<=anon key: ).*'))
	$(eval SUPABASE_URL := $(shell supabase status | grep -oP '(?<=API URL: ).*'))
	@echo "export SUPABASE_ANON_KEY=$(SUPABASE_ANON_KEY)" > .jwt
	@echo "export SUPABASE_URL=$(SUPABASE_URL)" >> .jwt

# Create a new local admin user in supabase
supabase-user: setup-env
	@read -s -p "Enter your Supabase password: " SUPABASE_PASS; echo; \
	echo "Creating new supabase user on ${SUPABASE_URL}..."; \
	TOKEN_RESPONSE=$$(curl -s -X POST "${SUPABASE_URL}/auth/v1/signup" \
	-H "apikey: ${SUPABASE_ANON_KEY}" \
	-H "Content-Type: application/json" \
	-d '{ "email": "admin@localhost", "password": "$$SUPABASE_PASS", "confirmPassword": "$$SUPABASE_PASS"}'); \
	echo "Signup response received..."; \
	JWT=$$(echo $$TOKEN_RESPONSE | grep -oP '(?<="access_token":")[^"]*'); \
	echo "export SUPABASE_USER_JWT=$$JWT" >> .jwt
	
# Gets a new JWT token for local admin user
supabase-jwt-token: setup-env
	@read -s -p "Enter your Supabase password: " SUPABASE_PASS; echo; \
	echo "Getting access token from ${SUPABASE_URL}..."; \
	TOKEN_RESPONSE=$$(curl -s -X POST "${SUPABASE_URL}/auth/v1/token?grant_type=password" \
	-H "apikey: ${SUPABASE_ANON_KEY}" \
	-H "Content-Type: application/json" \
	-d '{ "email": "admin@localhost", "password": "$$SUPABASE_PASS"}'); \
	echo "Extracting token from $$TOKEN_RESPONSE..."; \
	JWT=$$(echo $$TOKEN_RESPONSE | grep -oP '(?<="access_token":")[^"]*'); \
	echo "export SUPABASE_USER_JWT=$$JWT" >> .jwt
	@source .jwt; echo $(SUPABASE_USER_JWT)

