"""Utilitários compartilhados do curso rl-ai-scientist (FIAP Pós-Graduação)."""

from rl_utils.setup import definir_seeds, obter_dispositivo, info_versoes
from rl_utils.visualizacao import (
    PALETA_ACESSIVEL,
    configurar_matplotlib,
    media_movel,
    plotar_curva_recompensa,
)
from rl_utils.glossario import GLOSSARIO, exibir_glossario

__all__ = [
    "definir_seeds",
    "obter_dispositivo",
    "info_versoes",
    "PALETA_ACESSIVEL",
    "configurar_matplotlib",
    "media_movel",
    "plotar_curva_recompensa",
    "GLOSSARIO",
    "exibir_glossario",
]
