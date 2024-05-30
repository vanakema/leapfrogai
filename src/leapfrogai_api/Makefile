SHELL := /bin/bash

SUPABASE_URL = $(shell supabase status | grep -oP '(?<=API URL: ).*')
SUPABASE_ANON_KEY = $(shell supabase status | grep -oP '(?<=anon key: ).*')

install:
	python -m pip install ../../src/leapfrogai_sdk
	python -m pip install -e .


dev:
	python -m uvicorn main:app --port 3000 --reload --log-level info

test-integration:
	cd ../../ && python -m pytest tests/integration/api

# Create a new local admin user in supabase
supabase-user:
	@read -s -p "Enter your Supabase password: " SUPABASE_PASS; echo; \
	echo "Creating new supabase user on ${SUPABASE_URL}..."; \
	TOKEN_RESPONSE=$$(curl -s -X POST "${SUPABASE_URL}/auth/v1/signup" \
	-H "apikey: ${SUPABASE_ANON_KEY}" \
	-H "Content-Type: application/json" \
	-d '{ "email": "admin@localhost", "password": "$$SUPABASE_PASS", "confirmPassword": "$$SUPABASE_PASS"}'); \
	echo "Signup response received..."; \
	JWT=$$(echo $$TOKEN_RESPONSE | grep -oP '(?<="access_token":")[^"]*'); \
	echo -n "$$JWT" | xclip -selection clipboard
	@echo "DONE - JWT token copied to clipboard"
	
# Gets a new JWT token for local admin user
supabase-jwt-token:
	@read -s -p "Enter your Supabase password: " SUPABASE_PASS; echo; \
	echo "Getting access token from ${SUPABASE_URL}..."; \
	TOKEN_RESPONSE=$$(curl -s -X POST "${SUPABASE_URL}/auth/v1/token?grant_type=password" \
	-H "apikey: ${SUPABASE_ANON_KEY}" \
	-H "Content-Type: application/json" \
	-d '{ "email": "admin@localhost", "password": "$$SUPABASE_PASS"}'); \
	echo "Extracting token..."; \
	JWT=$$(echo $$TOKEN_RESPONSE | grep -oP '(?<="access_token":")[^"]*'); \
	echo -n "$$JWT" | xclip -selection clipboard
	@echo "DONE - JWT token copied to clipboard"


