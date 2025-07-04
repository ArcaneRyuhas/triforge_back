# alembic/env.py
from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
import os
import sys
from dotenv import load_dotenv

# ✅ AGREGAR ESTAS LÍNEAS PARA SOLUCIONAR EL ERROR
# Agregar el directorio raíz del proyecto al PYTHONPATH
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)  # Un nivel arriba desde alembic/
sys.path.insert(0, project_root)

# Cargar variables de entorno
load_dotenv()

# Ahora puedes importar tus modelos
try:
    from src.database.base import Base
    from src.database.models.project import ProjectModel
    from src.database.models.conversation_memory import ConversationMemoryModel
    print("✅ Modelos importados correctamente")
except ImportError as e:
    print(f"❌ Error importando modelos: {e}")
    # Crear Base vacía para que Alembic no falle
    from sqlalchemy import MetaData
    from sqlalchemy.ext.declarative import declarative_base
    Base = declarative_base()

# this is the Alembic Config object
config = context.config

# Set the DATABASE_URL from environment variable
database_url = os.getenv("DATABASE_URL")
if database_url:
    config.set_main_option("sqlalchemy.url", database_url)
else:
    print("⚠️ Warning: DATABASE_URL no encontrada en variables de entorno")

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here for 'autogenerate' support
target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()