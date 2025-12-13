#!/usr/bin/env python
"""Script para marcar migraciones como aplicadas"""
from alembic.config import Config
from alembic import command

# Configurar Alembic
cfg = Config("alembic.ini")

# Marcar todas las migraciones como aplicadas
print("Marcando todas las migraciones como aplicadas...")
command.stamp(cfg, "head")

print("Migraciones marcadas!")
