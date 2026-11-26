"""
Módulo de Processos.

Define a estrutura de dados que representa um processo do pseudo-SO
(equivalente ao PCB - Process Control Block). Guarda os dados lidos do
arquivo de entrada e o estado do processo durante a simulação.
"""

from dataclasses import dataclass, field
from typing import List

# Quanto menor o número, maior a prioridade.
PRIORIDADE_TEMPO_REAL = 0
MAIOR_PRIORIDADE_USUARIO = 1
MENOR_PRIORIDADE_USUARIO = 3


@dataclass
class Processo:
    """Bloco de controle de um processo (PCB)."""

    # ---- Dados lidos do arquivo processes.txt ----
    pid: int
    tempo_inicializacao: int
    prioridade: int
    tempo_processador: int
    max_frames: int          # tamanho máximo do conjunto de trabalho
    impressora: int
    scanner: int
    modem: int
    disco_sata: int

    # ---- Dado lido do arquivo string.txt ----
    string_referencia: List[int] = field(default_factory=list)

    # ---- Estado durante a simulação ----
    prioridade_atual: int = 0        # muda com realimentação e aging
    instrucoes_executadas: int = 0
    tempo_espera: int = 0            # ms esperando na fila (usado no aging)
    iniciado: bool = False
    finalizado: bool = False
    frames: List[int] = field(default_factory=list)   # frames que pertencem ao processo
    faltas_pagina: int = 0

    def __post_init__(self):
        self.prioridade_atual = self.prioridade

    def eh_tempo_real(self) -> bool:
        """Processos de prioridade 0 são de tempo real."""
        return self.prioridade == PRIORIDADE_TEMPO_REAL

    def executar_instrucao(self) -> int:
        """Executa uma instrução (1 ms de CPU) e devolve o número dela."""
        self.instrucoes_executadas += 1
        return self.instrucoes_executadas

    def terminou(self) -> bool:
        """O processo termina quando usou todo o seu tempo de processador."""
        return self.instrucoes_executadas >= self.tempo_processador
