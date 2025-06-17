# This is a dummy script to create the initial tables in Postgres
# Run it from the terminal if you are in dev mode with this command
# python -m src.database.create_initial_db
from src.database.session import engine, Base
Base.metadata.create_all(bind=engine)
