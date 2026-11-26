# Pseudo-SO Multiprogramado — Introdução a Sistemas Operacionais (Grupo 02)

Simulação de um pseudo-sistema operacional com **Gerenciador de Processos**, **Gerenciador de Memória**, **Gerenciador de E/S** e **Gerenciador de Arquivos**, conforme a especificação do trabalho prático de ISO 2026/2.

- **Linguagem:** Python 3 (versão 3.8 ou superior)
- **Bibliotecas:** apenas a biblioteca padrão do Python (`collections`, `dataclasses`, `threading`, `typing`, `sys`). Nenhuma biblioteca de terceiros, nada para instalar com `pip`.
- **Sistemas:** Windows 11, Linux e macOS (compatível com ambiente UNIX).

---

## 1. Como executar no Windows 11

### Passo 1 — Instalar o Python (só uma vez)
1. Abra a **Microsoft Store**, procure por **Python 3.12** (ou mais novo) e clique em **Obter**.
   - Alternativa: baixe em <https://www.python.org/downloads/> e, na instalação, marque **"Add python.exe to PATH"**.
2. Para conferir, abra o **Terminal** (botão Iniciar → digite `terminal`) e rode:
   ```
   python --version
   ```

### Passo 2 — Rodar o programa
**Jeito mais simples:** dê **duplo clique** em `executar.bat`. Ele roda o exemplo do enunciado e deixa a janela aberta.

**Pelo terminal** (dentro da pasta do projeto):
```
python dispatcher.py processes.txt files.txt string.txt
```

Cenário de teste extra (processos de usuário, recursos de E/S, espera por memória):
```
python dispatcher.py testes\processes.txt testes\files.txt testes\string.txt
```
ou duplo clique em `executar_teste.bat`.

Para salvar a saída em um arquivo: `python dispatcher.py processes.txt files.txt string.txt > saida.txt`

## 2. Como executar no Linux/macOS
```
python3 dispatcher.py processes.txt files.txt string.txt
```
ou `./executar.sh`.

---

## 3. Arquivos de entrada

**processes.txt** — um processo por linha (a linha 1 é o PID 0, a linha 2 é o PID 1, ...):
```
<tempo de inicialização>, <prioridade>, <tempo de processador>, <frames>, <impressora>, <scanner>, <modem>, <disco SATA>
```
Prioridade 0 = tempo real; 1, 2 e 3 = usuário. Para os recursos, 0 = não usa e qualquer outro valor = usa.

**files.txt**
```
linha 1: quantidade de blocos do disco
linha 2: quantidade n de segmentos já ocupados
n linhas: <nome do arquivo>, <primeiro bloco>, <quantidade de blocos>
demais linhas: <PID>, <código: 0 = criar | 1 = deletar>, <nome>, <blocos (só para criar)>
```

**string.txt** — uma string de referência de páginas por linha (linha i = processo i).

> **Observação sobre o exemplo do enunciado:** a última linha de `files.txt` é `1, 0, E, 2` (código **0 = criar**), mas a saída de exemplo do PDF mostra uma tentativa de **deletar** E. O programa segue a regra escrita na especificação, então o processo 1 **cria** o arquivo E nos blocos 8 e 9. As faltas de página (P0 = 7, P1 = 15) e as operações 1 a 4 são idênticas às do enunciado.

---

## 4. Organização do código

| Arquivo | Módulo | Responsabilidade |
|---|---|---|
| `dispatcher.py` | Despachante | Programa principal: chegada, criação e escalonamento dos processos; operações de arquivo; relatório final |
| `processo.py` | Processos | Estrutura `Processo` (PCB) com os dados e o estado de cada processo |
| `filas.py` | Filas | Fila global, fila de tempo real (FIFO) e 3 filas de usuário com realimentação e aging (máx. 1000 processos) |
| `memoria.py` | Memória | 20 frames de 1 KB (8 tempo real / 12 usuário), proteção de memória, paginação LRU local com pré-carga de 1 página |
| `recursos.py` | Recursos (E/S) | 2 impressoras, 1 scanner, 1 modem, 2 SATA, controlados por semáforos; alocação "tudo ou nada" |
| `arquivos.py` | Arquivos | Disco com alocação contígua e first-fit; permissões de criar/deletar; mapa de ocupação |
| `entrada.py` | Entrada | Leitura e validação dos três arquivos `.txt` |

## 5. Decisões de projeto

- **Tempo simulado:** cada tick = 1 ms = 1 instrução executada.
- **Tempo real (prioridade 0):** FIFO sem preempção; usa só os frames 0–7; não usa E/S (pedidos são ignorados com aviso).
- **Usuário (prioridades 1–3):** quantum de 1 ms. Depois de cada quantum o processo desce um nível (realimentação). Se esperar 10 ms numa fila, sobe um nível (aging), evitando starvation.
- **Criação de processos:** o processo espera na fila global até haver frames livres na sua área **e** todos os recursos de E/S pedidos. Processos que nunca caberiam (ex.: tempo real pedindo mais de 8 frames) são recusados.
- **Deadlock:** evitado porque o processo pega todos os recursos de uma vez (sem posse e espera) e só devolve ao terminar.
- **Sistema de arquivos:** as operações são executadas pelo despachante depois que todos os processos terminam; arquivos já gravados no disco não têm dono, então só processos de tempo real podem apagá-los.

---

## 6. Enviando para o GitHub

### Opção A — Pelo site (sem instalar nada)
1. Entre em <https://github.com> → botão **New** (novo repositório).
2. Nome: `pseudo-so-iso` → **Create repository**.
3. Clique em **uploading an existing file**, arraste **todo o conteúdo desta pasta** (não a pasta em si) e clique em **Commit changes**.

### Opção B — Pelo terminal (Git instalado)
```
cd caminho\para\pseudo-so
git init
git add .
git commit -m "Pseudo-SO multiprogramado - ISO Grupo 02"
git branch -M main
git remote add origin https://github.com/SEU_USUARIO/pseudo-so-iso.git
git push -u origin main
```
Se o Git não estiver instalado: `winget install --id Git.Git -e` no Terminal.

---

## 7. Uso de IA
O código foi gerado com apoio do Claude (Anthropic) e revisado pela equipe.
