# Makefile

# --- Development ---
up:
	docker compose -f docker-compose.dev.yml up --build

down:
	docker compose -f docker-compose.dev.yml down

bash:
	docker exec -it web-dev bash

# --- Production ---
up-prod:
	docker compose -f docker-compose.prod.yml up --build -d

down-prod:
	docker compose -f docker-compose.prod.yml down

logs-prod:
	docker compose -f docker-compose.prod.yml logs -f app

bash-prod:
	docker exec -it web-prod bash

# --- Common ---
clean:
	docker system prune -a --volumes -f