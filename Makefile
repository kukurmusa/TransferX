up:
	docker compose up --build

down:
	docker compose down -v

dev:
	python src/manage.py runserver 0.0.0.0:8000

migrate:
	python src/manage.py migrate

makemigrations:
	python src/manage.py makemigrations

test:
	pytest

lint:
	ruff check .

fmt:
	ruff format .

fmt-check:
	ruff format . --check
