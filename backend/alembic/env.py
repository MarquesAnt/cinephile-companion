from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool, text  # <--- CORRECTION 1 : Ajout de l'import text
from alembic import context
import os, sys

# --- CONFIGURATION PATH ---
sys.path.append(os.getcwd())

# --- IMPORTS MODÈLES ---
from app.models.movie import Movie
from sqlmodel import SQLModel

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = SQLModel.metadata

def run_migrations_offline() -> None:
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
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )
        
        # --- CORRECTION 2 : Utilisation correcte de text() ---
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        # -----------------------------------------------------

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()