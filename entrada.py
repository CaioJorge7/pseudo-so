"""
Módulo de Entrada.

Lê e valida os três arquivos .txt usados pelo pseudo-SO:
  1. processes.txt -> um processo por linha;
  2. files.txt     -> disco, arquivos já gravados e operações;
  3. string.txt    -> string de referência de páginas de cada processo.
"""

from typing import List, Tuple

from arquivos import OPERACAO_CRIAR, OPERACAO_DELETAR, OperacaoArquivo, SistemaArquivos
from processo import MENOR_PRIORIDADE_USUARIO, PRIORIDADE_TEMPO_REAL, Processo

CAMPOS_PROCESSO = 8


class ErroEntrada(Exception):
    """Erro de formato em algum arquivo de entrada."""


def _ler_linhas(caminho: str) -> List[str]:
    """Lê o arquivo ignorando linhas vazias. 'utf-8-sig' aceita o BOM do Bloco de Notas."""
    try:
        with open(caminho, encoding="utf-8-sig") as arquivo:
            return [linha.strip() for linha in arquivo if linha.strip()]
    except OSError as erro:
        raise ErroEntrada(f"não foi possível abrir '{caminho}': {erro.strerror}") from erro


def _inteiros(linha: str, caminho: str) -> List[int]:
    try:
        return [int(campo) for campo in linha.split(",") if campo.strip()]
    except ValueError as erro:
        raise ErroEntrada(f"{caminho}: valor não numérico na linha '{linha}'") from erro


# ----------------------------------------------------------------------
# processes.txt
# ----------------------------------------------------------------------
def ler_processos(caminho: str) -> List[Processo]:
    processos = []
    for pid, linha in enumerate(_ler_linhas(caminho)):
        campos = _inteiros(linha, caminho)
        if len(campos) != CAMPOS_PROCESSO:
            raise ErroEntrada(f"{caminho}: a linha '{linha}' deve ter {CAMPOS_PROCESSO} valores")
        processos.append(_criar_processo(pid, campos, caminho))
    return processos


def _criar_processo(pid: int, campos: List[int], caminho: str) -> Processo:
    inicio, prioridade, tempo_cpu, frames, impressora, scanner, modem, sata = campos
    if not PRIORIDADE_TEMPO_REAL <= prioridade <= MENOR_PRIORIDADE_USUARIO:
        raise ErroEntrada(f"{caminho}: prioridade {prioridade} do processo {pid} deve ser de 0 a 3")
    if inicio < 0 or tempo_cpu <= 0 or frames <= 0:
        raise ErroEntrada(f"{caminho}: tempos e frames do processo {pid} devem ser positivos")
    return Processo(pid, inicio, prioridade, tempo_cpu, frames,
                    impressora, scanner, modem, sata)


# ----------------------------------------------------------------------
# string.txt
# ----------------------------------------------------------------------
def ler_strings_referencia(caminho: str, processos: List[Processo]) -> None:
    """Associa a linha i do arquivo ao processo de PID i."""
    linhas = _ler_linhas(caminho)
    for processo in processos:
        if processo.pid < len(linhas):
            processo.string_referencia = _inteiros(linhas[processo.pid], caminho)
        else:
            print(f"Aviso: {caminho} não tem string de referência para o processo {processo.pid}.")


# ----------------------------------------------------------------------
# files.txt
# ----------------------------------------------------------------------
def ler_sistema_arquivos(caminho: str) -> Tuple[SistemaArquivos, List[OperacaoArquivo]]:
    linhas = _ler_linhas(caminho)
    if len(linhas) < 2:
        raise ErroEntrada(f"{caminho}: faltam as linhas de total de blocos e de segmentos")
    total_blocos = _um_inteiro(linhas[0], caminho)
    quantidade_segmentos = _um_inteiro(linhas[1], caminho)

    disco = SistemaArquivos(total_blocos)
    linhas_segmentos = linhas[2:2 + quantidade_segmentos]
    for linha in linhas_segmentos:
        _gravar_segmento(disco, linha, caminho)

    operacoes = [_criar_operacao(linha, caminho) for linha in linhas[2 + quantidade_segmentos:]]
    return disco, operacoes


def _um_inteiro(linha: str, caminho: str) -> int:
    valores = _inteiros(linha, caminho)
    if len(valores) != 1:
        raise ErroEntrada(f"{caminho}: esperado um único número na linha '{linha}'")
    return valores[0]


def _gravar_segmento(disco: SistemaArquivos, linha: str, caminho: str) -> None:
    campos = [campo.strip() for campo in linha.split(",")]
    if len(campos) != 3:
        raise ErroEntrada(f"{caminho}: segmento inválido '{linha}' (use: nome, bloco, quantidade)")
    try:
        disco.gravar_existente(campos[0], int(campos[1]), int(campos[2]))
    except ValueError as erro:
        raise ErroEntrada(f"{caminho}: segmento '{linha}' inválido: {erro}") from erro


def _criar_operacao(linha: str, caminho: str) -> OperacaoArquivo:
    campos = [campo.strip() for campo in linha.split(",")]
    try:
        pid, codigo, nome = int(campos[0]), int(campos[1]), campos[2]
        if codigo == OPERACAO_CRIAR:
            return OperacaoArquivo(pid, codigo, nome, int(campos[3]))
        if codigo == OPERACAO_DELETAR:
            return OperacaoArquivo(pid, codigo, nome)
    except (ValueError, IndexError) as erro:
        raise ErroEntrada(f"{caminho}: operação inválida '{linha}'") from erro
    raise ErroEntrada(f"{caminho}: código de operação {codigo} inválido (use 0 ou 1)")
