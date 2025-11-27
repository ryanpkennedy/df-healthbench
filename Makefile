.PHONY: db-start db-stop db-restart db-logs db-clean

# Start the database
db-start:
	docker-compose up -d postgres

# Stop the database
db-stop:
	docker-compose down

# Restart the database
db-restart:
	docker-compose restart postgres

# View database logs
db-logs:
	docker-compose logs -f postgres

# Stop database and remove volumes (WARNING: destroys all data)
db-clean:
	docker-compose down -v

