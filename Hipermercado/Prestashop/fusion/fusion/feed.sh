#!/bin/bash

# Caminho do arquivo de controle
feedmergeCurrentBatch="/home/hipermercado/public_html/modules/fusion/logs/feedmergeCurrentBatch.txt"
LOG_FILE="/home/hipermercado/public_html/modules/fusion/logs/$(date '+%Y-%m-%d')_processamento.log"

# Verifica se o arquivo existe
if [ ! -f "$feedmergeCurrentBatch" ]; then
    exit 0
fi

# Verifica se o arquivo está vazio
if [ ! -s "$feedmergeCurrentBatch" ]; then
    exit 0
fi

# Lê o conteúdo do arquivo
batch=$(cat $feedmergeCurrentBatch)
url="https://hipermercado.pt/modules/fusion/feedmerge.php?batch=$batch&t=d85a0768910eca8b7f719d5f854a4f85"

# Log da URL gerada
echo "$(date '+%Y-%m-%d %H:%M:%S') - Processando URL: $url" >> "$LOG_FILE"

# Executa o comando curl
curl --silent --show-error --location --insecure --output "/dev/null" "$url"
if [ $? -eq 0 ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Requisição para batch $batch concluída com sucesso." >> "$LOG_FILE"
else
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Falha ao processar batch $batch." >> "$LOG_FILE"
fi
