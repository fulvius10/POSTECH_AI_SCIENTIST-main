"""Funções de visualização padronizadas com paleta acessível para daltonismo."""

from typing import Optional, List

# Paleta Wong — validada para os três tipos mais comuns de daltonismo
PALETA_ACESSIVEL = {
    "azul":       "#0072B2",
    "laranja":    "#E69F00",
    "verde":      "#009E73",
    "amarelo":    "#F0E442",
    "ceu":        "#56B4E9",
    "vermelho":   "#D55E00",
    "roxo":       "#CC79A7",
    "preto":      "#000000",
}

_CICLO_CORES = [
    PALETA_ACESSIVEL["azul"],
    PALETA_ACESSIVEL["laranja"],
    PALETA_ACESSIVEL["verde"],
    PALETA_ACESSIVEL["ceu"],
    PALETA_ACESSIVEL["vermelho"],
    PALETA_ACESSIVEL["roxo"],
    PALETA_ACESSIVEL["amarelo"],
]


def media_movel(x, janela: int = 100):
    """Média móvel simples por convolução. Retorna x inalterado se len(x) < janela."""
    import numpy as np
    arr = np.asarray(x, dtype=float)
    if len(arr) < janela:
        return arr
    return np.convolve(arr, np.ones(janela) / janela, mode="valid")


def configurar_matplotlib() -> None:
    """Aplica paleta acessível, tamanho de fonte e grid padrão ao matplotlib."""
    try:
        import matplotlib.pyplot as plt
        import matplotlib as mpl

        mpl.rcParams.update({
            "axes.prop_cycle": mpl.cycler(color=_CICLO_CORES),
            "font.size": 12,
            "axes.titlesize": 13,
            "axes.labelsize": 12,
            "legend.fontsize": 11,
            "axes.grid": True,
            "grid.alpha": 0.4,
            "figure.dpi": 100,
            "figure.figsize": (9, 4),
        })
    except ImportError:
        print("matplotlib não encontrado.")


def plotar_curva_recompensa(
    historico: List[float],
    titulo: str = "Curva de recompensa",
    rotulo_eixo_x: str = "Episódio",
    rotulo_eixo_y: str = "Recompensa total",
    janela_media: int = 10,
    cor: Optional[str] = None,
    referencia: Optional[float] = None,
    rotulo_referencia: Optional[str] = None,
) -> None:
    """Plota curva de recompensa com média móvel e linha de referência opcional.

    Parâmetros:
        historico:         Lista de recompensas por episódio.
        titulo:            Título do gráfico.
        rotulo_eixo_x:     Rótulo do eixo horizontal.
        rotulo_eixo_y:     Rótulo do eixo vertical.
        janela_media:      Tamanho da janela para a média móvel.
        cor:               Cor principal (usa paleta padrão se None).
        referencia:        Valor de referência da literatura (linha horizontal).
        rotulo_referencia: Texto da linha de referência.
    """
    try:
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError:
        print("matplotlib ou numpy não encontrado.")
        return

    cor_principal = cor or PALETA_ACESSIVEL["azul"]

    episodios = list(range(1, len(historico) + 1))
    media_movel = np.convolve(
        historico, np.ones(janela_media) / janela_media, mode="valid"
    )
    offset = janela_media - 1

    fig, ax = plt.subplots()
    ax.plot(episodios, historico, alpha=0.3, color=cor_principal, label="Recompensa bruta")
    ax.plot(
        episodios[offset:],
        media_movel,
        color=cor_principal,
        linewidth=2,
        label=f"Média móvel ({janela_media} ep.)",
    )

    if referencia is not None:
        ax.axhline(
            referencia,
            linestyle="--",
            color=PALETA_ACESSIVEL["vermelho"],
            linewidth=1.5,
            label=rotulo_referencia or f"Referência: {referencia}",
        )

    ax.set_title(titulo)
    ax.set_xlabel(rotulo_eixo_x)
    ax.set_ylabel(rotulo_eixo_y)
    ax.legend()
    plt.tight_layout()
    plt.show()
