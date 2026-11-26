"""
Módulo de Filas.

Mantém a fila global (processos que chegaram e aguardam memória/recursos),
a fila de tempo real (FIFO, sem preempção) e as três filas de usuário
(múltiplas filas com realimentação, quantum de 1 ms e aging).
"""

from collections import deque
from typing import Deque, Dict, Optional

from processo import (
    Processo,
    MAIOR_PRIORIDADE_USUARIO,
    MENOR_PRIORIDADE_USUARIO,
)

MAX_PROCESSOS = 1000     # capacidade máxima somando todas as filas
QUANTUM_MS = 1           # quantum dos processos de usuário
LIMITE_AGING_MS = 10     # tempo de espera para o processo subir um nível


class FilaCheiaError(Exception):
    """Lançada quando se tenta passar de 1000 processos nas filas."""


class GerenciadorFilas:
    """Controla todas as filas de processos do pseudo-SO."""

    def __init__(self):
        self.fila_global: Deque[Processo] = deque()
        self.fila_tempo_real: Deque[Processo] = deque()
        self.filas_usuario: Dict[int, Deque[Processo]] = {
            nivel: deque()
            for nivel in range(MAIOR_PRIORIDADE_USUARIO, MENOR_PRIORIDADE_USUARIO + 1)
        }

    # ------------------------------------------------------------------
    # Fila global
    # ------------------------------------------------------------------
    def total_processos(self) -> int:
        """Quantidade de processos em todas as filas."""
        total_usuario = sum(len(fila) for fila in self.filas_usuario.values())
        return len(self.fila_global) + len(self.fila_tempo_real) + total_usuario

    def adicionar_fila_global(self, processo: Processo) -> None:
        """Coloca um processo recém-chegado na fila global."""
        if self.total_processos() >= MAX_PROCESSOS:
            raise FilaCheiaError(f"limite de {MAX_PROCESSOS} processos atingido")
        self.fila_global.append(processo)

    def remover_fila_global(self, processo: Processo) -> None:
        self.fila_global.remove(processo)

    # ------------------------------------------------------------------
    # Filas de prontos
    # ------------------------------------------------------------------
    def inserir_pronto(self, processo: Processo) -> None:
        """Classifica o processo pelo tipo e o coloca na fila correta."""
        processo.tempo_espera = 0
        if processo.eh_tempo_real():
            self.fila_tempo_real.append(processo)
        else:
            self.filas_usuario[processo.prioridade_atual].append(processo)

    def proximo_processo(self) -> Optional[Processo]:
        """Retira o próximo a executar: tempo real primeiro, depois usuário."""
        if self.fila_tempo_real:
            return self.fila_tempo_real.popleft()
        for nivel in sorted(self.filas_usuario):
            if self.filas_usuario[nivel]:
                return self.filas_usuario[nivel].popleft()
        return None

    def realimentar(self, processo: Processo) -> None:
        """
        Processo de usuário que usou o quantum inteiro perde um nível de
        prioridade (realimentação) e volta para o fim da fila.
        """
        processo.prioridade_atual = min(processo.prioridade_atual + 1,
                                        MENOR_PRIORIDADE_USUARIO)
        self.inserir_pronto(processo)

    def envelhecer(self) -> None:
        """
        Aging: cada processo de usuário que espera LIMITE_AGING_MS sobe um
        nível de prioridade. Isso evita starvation.
        """
        for nivel in range(MAIOR_PRIORIDADE_USUARIO + 1, MENOR_PRIORIDADE_USUARIO + 1):
            for processo in list(self.filas_usuario[nivel]):
                processo.tempo_espera += 1
                if processo.tempo_espera >= LIMITE_AGING_MS:
                    self._promover(processo, nivel)

    def _promover(self, processo: Processo, nivel_atual: int) -> None:
        self.filas_usuario[nivel_atual].remove(processo)
        processo.prioridade_atual = nivel_atual - 1
        self.inserir_pronto(processo)
