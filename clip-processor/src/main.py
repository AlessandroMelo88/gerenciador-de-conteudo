"""
Canal de Cortes — clip-processor
Stub de inicialização para Phase 1 (infraestrutura).
Implementação do pipeline nas Phases 2-5.
"""
import os
import sys
import time

print("clip-processor iniciado — aguardando implementação do pipeline")
print(f"MYSQL_HOST: {os.environ.get('MYSQL_HOST', 'não configurado')}")
print(f"ANTHROPIC_API_KEY: {'configurado' if os.environ.get('ANTHROPIC_API_KEY') else 'NÃO configurado'}")

# Loop infinito para manter o container em execução durante desenvolvimento
while True:
    time.sleep(60)
