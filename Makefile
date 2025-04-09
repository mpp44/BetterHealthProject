run:
	docker compose up

migrate:
	docker compose exec web python manage.py migrate

shell:
	docker compose exec web python manage.py shell