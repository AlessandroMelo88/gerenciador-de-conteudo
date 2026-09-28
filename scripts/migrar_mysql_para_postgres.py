"""Copia os dados do MySQL de produção para o PostgreSQL da VM A1.

O schema do Postgres vem das migrations do painel (`php artisan migrate`); este
script só move dados. Pode rodar mais de uma vez: cada tabela é truncada antes
da carga, então a segunda rodada (delta da virada) substitui a primeira.

Converte o que o MySQL guarda diferente:
  - tinyint 0/1 em coluna boolean do Postgres vira True/False;
  - datas zeradas ('0000-00-00') viram NULL.

Depois da carga acerta as sequences (`setval`) — sem isso o primeiro insert
colide com id existente — e confere a contagem de linhas tabela a tabela.

Uso (dentro de um container com pymysql e psycopg2, ex. a imagem do clip-processor):
  MYSQL_HOST=... MYSQL_USER=root MYSQL_PASSWORD=... \
  POSTGRES_HOST=... POSTGRES_USER=... POSTGRES_PASSWORD=... \
  python migrar_mysql_para_postgres.py
"""
import os
import sys

import psycopg2
import psycopg2.extras
import pymysql

DATABASE = os.environ.get('DATABASE', 'clips_automation')

# Ordem respeita as FKs. Sessões, cache e filas não migram: são transitórios.
TABLES = [
    'users',
    'niches',
    'source_channels',
    'destination_channels',
    'source_videos',
    'generated_clips',
    'system_settings',
    'transcription_jobs',
]


def pg_columns(pg, table):
    with pg.cursor() as cur:
        cur.execute(
            'SELECT column_name, data_type FROM information_schema.columns '
            "WHERE table_schema = 'public' AND table_name = %s ORDER BY ordinal_position",
            (table,),
        )
        return dict(cur.fetchall())


def convert(value, pg_type):
    if value is None:
        return None
    if pg_type == 'boolean':
        return bool(value)
    if isinstance(value, str) and value.startswith('0000-00-00'):
        return None
    return value


def main() -> int:
    my = pymysql.connect(
        host=os.environ['MYSQL_HOST'],
        user=os.environ.get('MYSQL_USER', 'root'),
        password=os.environ['MYSQL_PASSWORD'],
        database=DATABASE,
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor,
    )
    pg = psycopg2.connect(
        host=os.environ['POSTGRES_HOST'],
        user=os.environ['POSTGRES_USER'],
        password=os.environ['POSTGRES_PASSWORD'],
        dbname=DATABASE,
    )

    ok = True
    with pg:
        with pg.cursor() as cur:
            cur.execute('TRUNCATE ' + ', '.join(TABLES) + ' RESTART IDENTITY CASCADE')

        for table in TABLES:
            pg_cols = pg_columns(pg, table)
            if not pg_cols:
                print(f'ERRO: {table} não existe no Postgres — rodou as migrations?')
                return 1

            with my.cursor() as cur:
                cur.execute(f'SELECT * FROM `{table}`')
                rows = cur.fetchall()

            my_cols = list(rows[0].keys()) if rows else []
            only_mysql = [c for c in my_cols if c not in pg_cols]
            if only_mysql:
                print(f'ERRO: {table} tem colunas só no MySQL: {only_mysql}')
                return 1

            cols = [c for c in my_cols if c in pg_cols]
            if rows:
                values = [tuple(convert(r[c], pg_cols[c]) for c in cols) for r in rows]
                col_sql = ', '.join(f'"{c}"' for c in cols)
                with pg.cursor() as cur:
                    psycopg2.extras.execute_values(
                        cur, f'INSERT INTO {table} ({col_sql}) VALUES %s', values, page_size=500
                    )

            with pg.cursor() as cur:
                if 'id' in pg_cols:
                    cur.execute(
                        f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), "
                        f'COALESCE((SELECT MAX(id) FROM {table}), 0) + 1, false)'
                    )
                cur.execute(f'SELECT COUNT(*) FROM {table}')
                pg_count = cur.fetchone()[0]

            status = 'ok' if pg_count == len(rows) else 'DIVERGE'
            ok = ok and status == 'ok'
            print(f'{table:24} mysql={len(rows):6} postgres={pg_count:6} {status}')

    my.close()
    pg.close()
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
