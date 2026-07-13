"""Glossário de termos técnicos do curso rl-ai-scientist."""

# Formato: termo_en -> (tradução_pt, descrição_curta)
GLOSSARIO: dict[str, tuple[str, str]] = {
    # ── Fundamentos ────────────────────────────────────────────────────────────
    "agent":               ("agente",               "Entidade que toma decisões no ambiente."),
    "environment":         ("ambiente",              "Sistema com o qual o agente interage."),
    "state":               ("estado",                "Representação atual do ambiente percebida pelo agente."),
    "action":              ("ação",                  "Decisão tomada pelo agente em cada passo."),
    "reward":              ("recompensa",            "Sinal escalar de feedback do ambiente ao agente."),
    "episode":             ("episódio",              "Sequência completa de interação do início ao estado terminal."),
    "trajectory":          ("trajetória",            "Sequência de estados, ações e recompensas de um episódio."),
    "discount factor":     ("fator de desconto",     "γ — pondera recompensas futuras em relação às imediatas."),
    "return":              ("retorno",               "Soma (descontada) de recompensas futuras a partir de um estado."),
    "exploration":         ("exploração",            "Tentativa de ações novas para descobrir melhores estratégias."),
    "exploitation":        ("explotação",            "Uso do conhecimento atual para maximizar recompensa imediata."),

    # ── Funções de valor ───────────────────────────────────────────────────────
    "value function":      ("função de valor",       "V(s) — retorno esperado a partir do estado s seguindo uma política."),
    "action-value function": ("função de ação-valor", "Q(s,a) — retorno esperado ao tomar ação a no estado s."),
    "advantage function":  ("função de vantagem",    "A(s,a) = Q(s,a) − V(s) — mede o ganho relativo de uma ação."),
    "Bellman equation":    ("equação de Bellman",    "Equação de recorrência que define V e Q em termos de si mesmas."),

    # ── Métodos tabulares ──────────────────────────────────────────────────────
    "dynamic programming": ("programação dinâmica",  "Família de métodos que usa o modelo do ambiente para resolver o MDP."),
    "Monte Carlo":         ("Monte Carlo",           "Estima valores a partir de episódios completos amostrados."),
    "temporal difference": ("diferença temporal",    "Atualiza estimativas usando a próxima estimativa (bootstrapping)."),
    "Q-Learning":          ("Q-Learning",            "Algoritmo off-policy que aprende a função Q ótima diretamente."),
    "SARSA":               ("SARSA",                 "Algoritmo on-policy de diferença temporal (State-Action-Reward-State-Action)."),
    "epsilon-greedy":      ("ε-greedy",              "Política de exploração: escolhe aleatório com prob. ε, melhor caso contrário."),

    # ── Deep RL ────────────────────────────────────────────────────────────────
    "DQN":                 ("DQN",                   "Deep Q-Network — aproxima Q com rede neural; usa replay buffer e target network."),
    "replay buffer":       ("buffer de replay",      "Memória que armazena transições para treinamento em mini-batches."),
    "target network":      ("rede-alvo",             "Cópia estável da rede principal usada para calcular alvos de treinamento."),

    # ── Policy-Based ──────────────────────────────────────────────────────────
    "policy":              ("política",              "π(a|s) — distribuição de probabilidade sobre ações dado o estado."),
    "policy gradient":     ("gradiente de política", "Família de métodos que otimiza diretamente os parâmetros da política."),
    "REINFORCE":           ("REINFORCE",             "Algoritmo policy gradient que usa retorno completo do episódio."),
    "baseline":            ("linha de base",         "Valor subtraído do retorno para reduzir variância do gradiente."),
    "actor-critic":        ("ator-crítico",          "Arquitetura com rede de política (ator) e de valor (crítico) simultâneas."),
    "PPO":                 ("PPO",                   "Proximal Policy Optimization — limita a atualização da política com clipping."),
    "DDPG":                ("DDPG",                  "Deep Deterministic Policy Gradient — política determinística para espaços contínuos."),
    "SAC":                 ("SAC",                   "Soft Actor-Critic — maximiza recompensa e entropia da política."),
    "entropy":             ("entropia",              "Medida de aleatoriedade da política; regulariza exploração no SAC."),

    # ── Métodos avançados ─────────────────────────────────────────────────────
    "model-based RL":      ("RL baseado em modelo",  "Aprendizado que usa um modelo do ambiente para planejamento."),
    "world model":         ("modelo do mundo",       "Representação aprendida da dinâmica do ambiente."),
    "offline RL":          ("RL offline",            "Aprendizado a partir de um dataset fixo sem interação nova com o ambiente."),
    "behavior cloning":    ("clonagem comportamental", "Imita um especialista via aprendizado supervisionado a partir de demonstrações."),
    "IRL":                 ("IRL",                   "Inverse RL — infere a função de recompensa a partir de demonstrações."),
    "MARL":                ("MARL",                  "Multi-Agent RL — múltiplos agentes aprendendo em um ambiente compartilhado."),
    "CTDE":                ("CTDE",                  "Centralized Training, Decentralized Execution — paradigma de treino centralizado."),
    "RLHF":                ("RLHF",                  "RL from Human Feedback — usa preferências humanas para aprender recompensa."),
    "reward hacking":      ("reward hacking",        "Exploração de brechas na função de recompensa sem atingir o objetivo real."),
    "alignment":           ("alinhamento",           "Garantia de que o agente persegue os objetivos pretendidos pelo designer."),
    "hierarchical RL":     ("RL hierárquico",        "Decomposição de tarefas em políticas de alto e baixo nível."),
    "option":              ("opção",                 "Subpolítica temporariamente estendida no RL hierárquico."),
}


def exibir_glossario(termos: list[str] | None = None) -> None:
    """Exibe o glossário formatado, completo ou para uma lista de termos.

    Parâmetros:
        termos: Lista de chaves em inglês a exibir. Se None, exibe tudo.
    """
    selecao = {k: v for k, v in GLOSSARIO.items() if termos is None or k in termos}
    if not selecao:
        print("Nenhum termo encontrado.")
        return
    col = max(len(k) for k in selecao) + 2
    print(f"{'Termo (EN)':<{col}} {'Tradução (PT)':<28} Descrição")
    print("-" * (col + 28 + 60))
    for termo_en, (traducao, descricao) in sorted(selecao.items()):
        print(f"{termo_en:<{col}} {traducao:<28} {descricao}")
