"""
Módulo de Arquivos.

Simula um disco dividido em blocos, com alocação contígua e first-fit
(a busca sempre começa no bloco 0). Regras de permissão:
  - processo de tempo real: cria (se houver espaço) e deleta qualquer arquivo;
  - processo de usuário: cria quantos quiser, mas só deleta o que ele criou.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from processo import Processo

BLOCO_LIVRE = "0"
OPERACAO_CRIAR = 0
OPERACAO_DELETAR = 1


@dataclass
class Arquivo:
    nome: str
    primeiro_bloco: int
    quantidade_blocos: int
    criador: Optional[int]      # PID do criador (None = já estava no disco)

    def blocos(self) -> List[int]:
        return list(range(self.primeiro_bloco,
                          self.primeiro_bloco + self.quantidade_blocos))


@dataclass
class OperacaoArquivo:
    pid: int
    codigo: int
    nome_arquivo: str
    quantidade_blocos: int = 0


def formatar_blocos(blocos: List[int]) -> str:
    """[0, 1, 2] -> 'blocos 0, 1 e 2'; [4] -> 'bloco 4'."""
    if len(blocos) == 1:
        return f"bloco {blocos[0]}"
    inicio = ", ".join(str(b) for b in blocos[:-1])
    return f"blocos {inicio} e {blocos[-1]}"


class SistemaArquivos:
    """Disco com alocação contígua e first-fit."""

    def __init__(self, total_blocos: int):
        self.blocos: List[Optional[str]] = [None] * total_blocos
        self.arquivos: Dict[str, Arquivo] = {}

    # ------------------------------------------------------------------
    # Gravação inicial (segmentos já ocupados no arquivo files.txt)
    # ------------------------------------------------------------------
    def gravar_existente(self, nome: str, primeiro_bloco: int, quantidade: int) -> None:
        arquivo = Arquivo(nome, primeiro_bloco, quantidade, criador=None)
        if arquivo.blocos()[-1] >= len(self.blocos) or primeiro_bloco < 0:
            raise ValueError(f"arquivo {nome} passa do tamanho do disco")
        self._ocupar(arquivo)

    # ------------------------------------------------------------------
    # Operações
    # ------------------------------------------------------------------
    def criar(self, processo: Processo, nome: str, quantidade: int) -> Tuple[bool, str]:
        pid = processo.pid
        if nome in self.arquivos:
            return False, f"O processo {pid} não pode criar o arquivo {nome} porque ele já existe."
        if quantidade <= 0:
            return False, f"O processo {pid} não pode criar o arquivo {nome} (tamanho inválido)."
        inicio = self._first_fit(quantidade)
        if inicio is None:
            return False, f"O processo {pid} não pode criar o arquivo {nome} (falta de espaço)."
        arquivo = Arquivo(nome, inicio, quantidade, criador=pid)
        self._ocupar(arquivo)
        return True, f"O processo {pid} criou o arquivo {nome} ({formatar_blocos(arquivo.blocos())})."

    def deletar(self, processo: Processo, nome: str) -> Tuple[bool, str]:
        pid = processo.pid
        arquivo = self.arquivos.get(nome)
        if arquivo is None:
            return False, f"O processo {pid} não pode deletar o arquivo {nome} porque ele não existe."
        if not processo.eh_tempo_real() and arquivo.criador != pid:
            return False, (f"O processo {pid} não pode deletar o arquivo {nome} "
                           f"porque não foi criado por ele.")
        self._desocupar(arquivo)
        return True, f"O processo {pid} deletou o arquivo {nome}."

    # ------------------------------------------------------------------
    # Auxiliares
    # ------------------------------------------------------------------
    def _first_fit(self, quantidade: int) -> Optional[int]:
        """Primeiro trecho contíguo livre com 'quantidade' blocos."""
        livres_seguidos = 0
        for indice, ocupante in enumerate(self.blocos):
            livres_seguidos = livres_seguidos + 1 if ocupante is None else 0
            if livres_seguidos == quantidade:
                return indice - quantidade + 1
        return None

    def _ocupar(self, arquivo: Arquivo) -> None:
        for bloco in arquivo.blocos():
            if self.blocos[bloco] is not None:
                raise ValueError(f"bloco {bloco} já está ocupado")
            self.blocos[bloco] = arquivo.nome
        self.arquivos[arquivo.nome] = arquivo

    def _desocupar(self, arquivo: Arquivo) -> None:
        for bloco in arquivo.blocos():
            self.blocos[bloco] = None
        del self.arquivos[arquivo.nome]

    def mapa_ocupacao(self) -> str:
        """Mapa do disco: nome do arquivo em cada bloco, 0 para bloco vazio."""
        return " ".join(nome if nome is not None else BLOCO_LIVRE for nome in self.blocos)
