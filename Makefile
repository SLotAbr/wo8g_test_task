
apply-first-migrations-and-run:
	docker compose up postgresql -d
	sleep 1
	docker compose run web alembic upgrade head
	docker compose up web -d --remove-orphans

up:
	docker compose up -d
stop:
	docker compose stop

test:
	@docker exec -it application-backend pytest -p no:warnings -vv --cache-clear ./

message ?= Initial migration
generate-migration-with-message:
	docker exec -it application-backend alembic revision --autogenerate -m "$(message)"

migrate:
	docker exec -it application-backend alembic upgrade head
downgrade:
	docker exec -it application-backend alembic downgrade -1
full-downgrade:
	docker exec -it application-backend alembic downgrade base

