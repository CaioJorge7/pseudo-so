"""
Pseudo-SO multiprogramado - processo despachante (programa principal).

Uso:
    python dispatcher.py processes.txt files.txt string.txt

O despachante é o primeiro processo do sistema. Ele:
  1. lê os arquivos de entrada;
  2. coloca cada processo na fila global no seu tempo de inicialização;
  3. cria o processo quando há memória e recursos (mostrando os dados dele);
  4. escalona a CPU (tempo real FIFO; usuário com realimentação, quantum 1 ms);
  5. executa as operações do sistema de arquivos e mostra o mapa do disco;
  6. mostra a quantidade de faltas de página de cada processo.

O tempo é simulado em "ticks" de 1 ms: a cada tick uma instrução é executada.
"""

import sys
from typing import Dict, List, Optional

from arquivos import OPERACAO_CRIAR, OperacaoArquivo, SistemaArquivos
from entrada import ErroEntrada, ler_processos, ler_sistema_arquivos, ler_strings_referencia
from filas import FilaCheiaError, GerenciadorFilas
from memoria import GerenciadorMemoria
from processo import Processo
from recursos import GerenciadorRecursos


class Despachante:
    """Coordena os gerenciadores de filas, memória e recursos."""

    def __init__(self, processos: List[Processo]):
        self.processos = processos
        self.filas = GerenciadorFilas()
        self.memoria = GerenciadorMemoria()
        self.recursos = GerenciadorRecursos()
        self.tempo_atual = 0
        self.processo_em_execucao: Optional[Processo] = None
        self.ultimo_a_executar: Optional[Processo] = None

    # ==================================================================
    # Laço principal do escalonador
    # ==================================================================
    def executar(self) -> None:
        chegadas = sorted(self.processos, key=lambda p: (p.tempo_inicializacao, p.pid))
        while not all(p.finalizado for p in self.processos):
            self._receber_chegadas(chegadas)
            self._criar_processos_da_fila_global()
            processo = self._escolher_processo()
            if processo is not None:
                self._executar_um_quantum(processo)
            self.tempo_atual += 1
            self.filas.envelhecer()

    def _receber_chegadas(self, chegadas: List[Processo]) -> None:
        """Move para a fila global os processos cujo tempo de início chegou."""
        while chegadas and chegadas[0].tempo_inicializacao <= self.tempo_atual:
            processo = chegadas.pop(0)
            motivo = self._motivo_impossivel(processo)
            if motivo:
                self._descartar(processo, motivo)
                continue
            try:
                self.filas.adicionar_fila_global(processo)
            except FilaCheiaError as erro:
                self._descartar(processo, str(erro))

    def _motivo_impossivel(self, processo: Processo) -> str:
        """Verifica se o processo nunca poderia ser executado."""
        if not self.memoria.cabe_na_particao(processo):
            area = "tempo real (8 frames)" if processo.eh_tempo_real() else "usuário (12 frames)"
            return f"pede {processo.max_frames} frames, mais que a área de {area}"
        return ""

    def _descartar(self, processo: Processo, motivo: str) -> None:
        self._separar_da_execucao()
        print(f"dispatcher =>\n    Processo {processo.pid} não pode ser criado: {motivo}.\n")
        processo.finalizado = True

    # ==================================================================
    # Criação de processos (fila global -> filas de prontos)
    # ==================================================================
    def _criar_processos_da_fila_global(self) -> None:
        for processo in list(self.filas.fila_global):
            if self._reservar_memoria_e_recursos(processo):
                self.filas.remover_fila_global(processo)
                self.memoria.simular_paginacao(processo)
                self._mostrar_criacao(processo)
                self.filas.inserir_pronto(processo)

    def _reservar_memoria_e_recursos(self, processo: Processo) -> bool:
        """Só cria o processo se conseguir memória E todos os recursos."""
        if processo.eh_tempo_real():
            self._ignorar_recursos_de_tempo_real(processo)
        if not self.memoria.alocar(processo):
            return False
        if not self.recursos.alocar(processo):
            self.memoria.liberar(processo)
            return False
        return True

    @staticmethod
    def _ignorar_recursos_de_tempo_real(processo: Processo) -> None:
        """Processos de tempo real não usam dispositivos de E/S."""
        if GerenciadorRecursos.recursos_pedidos(processo):
            print(f"Aviso: P{processo.pid} é de tempo real; pedido de E/S ignorado.\n")
        processo.impressora = processo.scanner = processo.modem = processo.disco_sata = 0

    def _separar_da_execucao(self) -> None:
        """Quebra de linha antes de uma mensagem do despachante no meio da execução."""
        if self.ultimo_a_executar is not None:
            print()
            self.ultimo_a_executar = None   # o próximo processo mostra o cabeçalho de novo

    def _mostrar_criacao(self, processo: Processo) -> None:
        self._separar_da_execucao()
        print("dispatcher =>")
        print(f"    PID: {processo.pid}")
        print(f"    frames: {len(processo.frames)}")
        print(f"    priority: {processo.prioridade}")
        print(f"    time: {processo.tempo_processador}")
        print(f"    printers: {processo.impressora}")
        print(f"    scanners: {processo.scanner}")
        print(f"    modems: {processo.modem}")
        print(f"    drives: {processo.disco_sata}")
        print()

    # ==================================================================
    # Escalonamento e execução
    # ==================================================================
    def _escolher_processo(self) -> Optional[Processo]:
        """Tempo real continua até o fim (sem preempção); senão, pega o próximo."""
        atual = self.processo_em_execucao
        if atual is not None and atual.eh_tempo_real():
            return atual
        return self.filas.proximo_processo()

    def _executar_um_quantum(self, processo: Processo) -> None:
        self._mostrar_troca_de_contexto(processo)
        numero = processo.executar_instrucao()
        print(f"P{processo.pid} instruction {numero}")

        if processo.terminou():
            self._finalizar(processo)
        elif processo.eh_tempo_real():
            self.processo_em_execucao = processo
        else:
            self.processo_em_execucao = None
            self.filas.realimentar(processo)      # usou o quantum: preempção

    def _mostrar_troca_de_contexto(self, processo: Processo) -> None:
        if self.ultimo_a_executar is processo:
            return
        print(f"process {processo.pid} =>")
        if not processo.iniciado:
            print(f"P{processo.pid} STARTED")
            processo.iniciado = True
        self.ultimo_a_executar = processo

    def _finalizar(self, processo: Processo) -> None:
        print(f"P{processo.pid} return SIGINT\n")
        processo.finalizado = True
        self.processo_em_execucao = None
        self.ultimo_a_executar = None
        self.memoria.liberar(processo)
        self.recursos.liberar(processo)

    # ==================================================================
    # Sistema de arquivos e relatório final
    # ==================================================================
    def executar_operacoes_arquivo(self, disco: SistemaArquivos,
                                   operacoes: List[OperacaoArquivo]) -> None:
        print("\nSistema de arquivos =>")
        processos_por_pid: Dict[int, Processo] = {p.pid: p for p in self.processos}
        for numero, operacao in enumerate(operacoes, start=1):
            sucesso, mensagem = self._executar_operacao(disco, operacao, processos_por_pid)
            print(f"Operação {numero} => {'Sucesso' if sucesso else 'Falha'}")
            print(f"{mensagem}\n")
        print("Mapa de ocupação do disco:")
        print(disco.mapa_ocupacao())

    @staticmethod
    def _executar_operacao(disco: SistemaArquivos, operacao: OperacaoArquivo,
                           processos_por_pid: Dict[int, Processo]):
        processo = processos_por_pid.get(operacao.pid)
        if processo is None:
            return False, f"O processo {operacao.pid} não existe."
        if operacao.codigo == OPERACAO_CRIAR:
            return disco.criar(processo, operacao.nome_arquivo, operacao.quantidade_blocos)
        return disco.deletar(processo, operacao.nome_arquivo)

    def mostrar_faltas_de_pagina(self) -> None:
        print("\nNúmero de Faltas de Páginas por processo:")
        for processo in self.processos:
            print(self._linha_faltas(processo))

    @staticmethod
    def _linha_faltas(processo: Processo) -> str:
        if not processo.iniciado:
            return f"P{processo.pid} = não executado"
        if processo.faltas_pagina == 1:
            return f"P{processo.pid} = 1 falta de página"
        return f"P{processo.pid} = {processo.faltas_pagina} faltas de páginas"


def configurar_saida_utf8() -> None:
    """Garante acentos corretos no terminal do Windows."""
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass


def main(argumentos: List[str]) -> int:
    configurar_saida_utf8()
    if len(argumentos) != 4:
        print("Uso: python dispatcher.py processes.txt files.txt string.txt")
        return 1
    try:
        processos = ler_processos(argumentos[1])
        disco, operacoes = ler_sistema_arquivos(argumentos[2])
        ler_strings_referencia(argumentos[3], processos)
    except ErroEntrada as erro:
        print(f"Erro na entrada: {erro}")
        return 1

    despachante = Despachante(processos)
    despachante.executar()
    despachante.executar_operacoes_arquivo(disco, operacoes)
    despachante.mostrar_faltas_de_pagina()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
