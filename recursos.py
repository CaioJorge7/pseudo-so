"""
Módulo de Recursos (Gerenciador de E/S).

Recursos disponíveis: 1 scanner, 2 impressoras, 1 modem e 2 discos SATA.
Cada tipo de recurso é controlado por um semáforo contador, o que garante
que cada unidade seja usada por um único processo por vez.

Para evitar deadlock, a alocação é "tudo ou nada": o processo só recebe
os recursos se TODOS os que ele pediu estiverem livres. Não há preempção
de recursos: eles só são devolvidos quando o processo termina.
"""

import threading
from typing import Dict, List

from processo import Processo

QUANTIDADE_RECURSOS = {
    "impressora": 2,
    "scanner": 1,
    "modem": 1,
    "sata": 2,
}


class GerenciadorRecursos:
    """Aloca e libera os dispositivos de E/S com semáforos."""

    def __init__(self):
        self.semaforos: Dict[str, threading.Semaphore] = {
            nome: threading.Semaphore(quantidade)
            for nome, quantidade in QUANTIDADE_RECURSOS.items()
        }
        self.recursos_do_processo: Dict[int, List[str]] = {}

    @staticmethod
    def recursos_pedidos(processo: Processo) -> List[str]:
        """Lista os recursos que o processo pediu (valor diferente de 0)."""
        pedidos = {
            "impressora": processo.impressora,
            "scanner": processo.scanner,
            "modem": processo.modem,
            "sata": processo.disco_sata,
        }
        return [nome for nome, valor in pedidos.items() if valor != 0]

    def alocar(self, processo: Processo) -> bool:
        """Tenta pegar todos os recursos (wait/P). Se faltar um, desfaz."""
        obtidos: List[str] = []
        for nome in self.recursos_pedidos(processo):
            if not self.semaforos[nome].acquire(blocking=False):
                self._devolver(obtidos)
                return False
            obtidos.append(nome)
        self.recursos_do_processo[processo.pid] = obtidos
        return True

    def liberar(self, processo: Processo) -> None:
        """Devolve os recursos do processo que terminou (signal/V)."""
        self._devolver(self.recursos_do_processo.pop(processo.pid, []))

    def _devolver(self, nomes: List[str]) -> None:
        for nome in nomes:
            self.semaforos[nome].release()
