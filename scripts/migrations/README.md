# Migrações operacionais

Esta pasta reúne utilitários excepcionais de migração entre ambientes ou
motores de banco. Eles não fazem parte do startup normal da aplicação e não
substituem as migrations do Laravel.

## MySQL → PostgreSQL

`migrate-mysql-to-postgres.py` copia os dados do banco MySQL legado para o
PostgreSQL, preserva as chaves primárias, faz upsert por chave primária e
recalibra as sequences do destino. A origem não é apagada.

Antes de executar:

1. Faça e valide um backup do MySQL.
2. Inicialize o schema do PostgreSQL e execute o `panel-init`.
3. Confira as variáveis de conexão dos dois bancos.
4. Execute somente após confirmar explicitamente a operação:

```bash
CONFIRM_MIGRATION=I_UNDERSTAND \
  python3 scripts/migrations/migrate-mysql-to-postgres.py
```

O script não deve ser chamado pelo Docker Compose, pelo worker ou pelo fluxo
normal de deploy.
