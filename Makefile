.PHONY: help install start test docker-up docker-down clean

help:
	@echo "TrustNet-SDN Platform Makefile"
	@echo "--------------------------------"
	@echo "make install      : Install Python backend requirements"
	@echo "make start        : Run backend API and WebSocket server"
	@echo "make test         : Run automated test suite"
	@echo "make docker-up    : Launch full stack in Docker containers"
	@echo "make docker-down  : Stop Docker containers"
	@echo "make clean        : Clean cached files"

install:
	pip install -r backend/requirements.txt

start:
	PYTHONPATH=. python3 -m backend.app.main

test:
	python3 -m unittest discover tests -v

docker-up:
	docker-compose up --build -d

docker-down:
	docker-compose down

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
