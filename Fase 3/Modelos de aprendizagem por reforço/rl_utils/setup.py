"""Funções de configuração de reprodutibilidade e ambiente."""

import random
import importlib


def definir_seeds(seed: int = 42, env=None) -> None:
    """Fixa seeds globais para reprodutibilidade.

    Parâmetros:
        seed: Valor da seed a ser aplicado em todos os geradores.
        env:  Instância de gymnasium.Env opcional; se fornecida, chama env.reset(seed=seed).
    """
    random.seed(seed)

    try:
        import numpy as np
        np.random.seed(seed)
    except ImportError:
        pass

    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False
    except ImportError:
        pass

    if env is not None:
        env.reset(seed=seed)


def obter_dispositivo(usar_gpu: bool = True):
    """Retorna o dispositivo PyTorch adequado ao ambiente de execução.

    Parâmetros:
        usar_gpu: Se True, usa CUDA quando disponível; caso contrário, força CPU.

    Retorno:
        torch.device — 'cuda' ou 'cpu'.
    """
    try:
        import torch
        if usar_gpu and torch.cuda.is_available():
            dispositivo = torch.device("cuda")
        else:
            dispositivo = torch.device("cpu")
        print(f"Dispositivo em uso: {dispositivo}")
        return dispositivo
    except ImportError:
        print("PyTorch não encontrado — dispositivo não disponível.")
        return None


def info_versoes() -> None:
    """Imprime tabela com as versões das bibliotecas principais do curso."""
    bibliotecas = [
        ("gymnasium", "gymnasium"),
        ("torch", "torch"),
        ("numpy", "numpy"),
        ("matplotlib", "matplotlib"),
        ("pandas", "pandas"),
        ("scikit-learn", "sklearn"),
    ]

    print(f"{'Biblioteca':<20} {'Versão'}")
    print("-" * 32)
    for nome_exibicao, nome_modulo in bibliotecas:
        try:
            mod = importlib.import_module(nome_modulo)
            versao = getattr(mod, "__version__", "?")
        except ImportError:
            versao = "não instalado"
        print(f"{nome_exibicao:<20} {versao}")
