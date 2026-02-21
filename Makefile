run:
	@docker compose up -d --build

debug:
	@docker compose up --build --no-deps

# Local LAN testing with port 8000 exposed via dev override, without Traefik
debugdev:
	@DOMAIN=localhost ACME_EMAIL=dev@example.invalid \
		docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build --no-deps db  web 

stop:
	@docker compose down

clean:
	# @find . -path "*/migrations" -type d -exec rm -rf {} +
	@find . -path "*/__pycache__" -type d -exec rm -rf {} +
	@docker compose down
	@docker system prune -f
	@docker network prune -f
	@docker image prune -f
	@docker container prune -f

test:
	@docker compose run --rm

restart: stop debug

cleandb:
	@docker volume rm $(shell docker volume ls -q)

fclean: clean
	@docker rmi -f $(shell docker images -q)
	@docker volume rm $(shell docker volume ls -q)
