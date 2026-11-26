.PHONY: sql-console

sql-console:
	docker compose exec capper python -m sqlite3 /app/data/capper.db
