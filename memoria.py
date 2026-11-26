"""
Módulo de Memória.

Simula uma memória principal de 20 frames de 1 KB:
  - frames 0 a 7  -> reservados para processos de tempo real;
  - frames 8 a 19 -> reservados para processos de usuário.

Cada processo recebe um conjunto fixo de frames (working set). Um processo
só pode acessar os frames que são dele (proteção de memória).
A substituição de páginas usa LRU com escopo local e pré-carga de 1 página.
"""

from collections import OrderedDict
from typing import List, Optional

from processo import Processo

TOTAL_FRAMES = 20
TAMANHO_FRAME_KB = 1
FRAMES_TEMPO_REAL = 8
FRAMES_USUARIO = TOTAL_FRAMES - FRAMES_TEMPO_REAL


class ViolacaoMemoriaError(Exception):
    """Lançada quando um processo tenta acessar um frame de outro processo."""


class GerenciadorMemoria:
    """Aloca, libera e protege os frames da memória principal."""

    def __init__(self):
        # dono_frame[i] = PID do processo que ocupa o frame i (None = livre)
        self.dono_frame: List[Optional[int]] = [None] * TOTAL_FRAMES

    # ------------------------------------------------------------------
    # Partições
    # ------------------------------------------------------------------
    @staticmethod
    def _particao(processo: Processo) -> range:
        """Faixa de frames que o tipo do processo pode usar."""
        if processo.eh_tempo_real():
            return range(0, FRAMES_TEMPO_REAL)
        return range(FRAMES_TEMPO_REAL, TOTAL_FRAMES)

    def cabe_na_particao(self, processo: Processo) -> bool:
        """Diz se o working set pedido cabe na área reservada ao tipo."""
        return processo.max_frames <= len(self._particao(processo))

    # ------------------------------------------------------------------
    # Alocação e liberação
    # ------------------------------------------------------------------
    def alocar(self, processo: Processo) -> bool:
        """Reserva max_frames frames livres da partição do processo."""
        livres = [f for f in self._particao(processo) if self.dono_frame[f] is None]
        if len(livres) < processo.max_frames:
            return False
        processo.frames = livres[:processo.max_frames]
        for frame in processo.frames:
            self.dono_frame[frame] = processo.pid
        return True

    def liberar(self, processo: Processo) -> None:
        """Devolve os frames do processo para a memória livre."""
        for frame in processo.frames:
            self.dono_frame[frame] = None
        processo.frames = []

    def acessar(self, processo: Processo, frame: int) -> None:
        """Garante que o processo só toque nos frames dele."""
        if self.dono_frame[frame] != processo.pid:
            raise ViolacaoMemoriaError(
                f"P{processo.pid} tentou acessar o frame {frame}, que não é dele")

    # ------------------------------------------------------------------
    # Paginação (LRU local)
    # ------------------------------------------------------------------
    def simular_paginacao(self, processo: Processo) -> int:
        """
        Percorre a string de referência do processo e conta as faltas de
        página. A primeira página já está carregada (pré-carga de 1 página).
        """
        referencias = processo.string_referencia
        if not referencias:
            return 0

        frames_livres = list(processo.frames)
        # tabela de páginas: página -> frame. A ordem do OrderedDict guarda a
        # recência de uso: o primeiro item é o menos recentemente usado.
        tabela_paginas: "OrderedDict[int, int]" = OrderedDict()
        tabela_paginas[referencias[0]] = frames_livres.pop(0)   # pré-carga

        faltas = 0
        for pagina in referencias:
            if pagina in tabela_paginas:
                tabela_paginas.move_to_end(pagina)          # acerto: vira a mais recente
                continue
            faltas += 1
            frame = self._escolher_frame(tabela_paginas, frames_livres)
            self.acessar(processo, frame)
            tabela_paginas[pagina] = frame

        processo.faltas_pagina = faltas
        return faltas

    @staticmethod
    def _escolher_frame(tabela_paginas: "OrderedDict[int, int]",
                        frames_livres: List[int]) -> int:
        """Usa um frame livre do processo ou retira a página LRU."""
        if frames_livres:
            return frames_livres.pop(0)
        _pagina_vitima, frame = tabela_paginas.popitem(last=False)
        return frame
