.PHONY: dev up down logs shell db-shell clean

# Desarrollo: levanta con logs visibles
dev:
	docker-compose up --build

# Levantar en background
up:
	docker-compose up -d --build

# Detener
down:
	docker-compose down

# Ver logs
logs:
	docker-compose logs -f

# Entrar al contenedor API
shell:
	docker-compose exec api /bin/bash

# Entrar a MariaDB
db-shell:
	docker-compose exec db mariadb -u pliegorag_user -p pliegorag

# Limpiar todo (incluye volúmenes)
clean:
	docker-compose down -v