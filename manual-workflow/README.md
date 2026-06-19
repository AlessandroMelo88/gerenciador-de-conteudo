# Manual Workflow — Canal de Cortes

Guia de operação manual para postagem de clipes enquanto o upload automático (Phase 5) não está em produção.

## Pré-requisitos

- Docker rodando com os serviços `clip-processor` e `mysql`
- Acesso ao YouTube Studio (conta "Futebol em Cortes")
- Variável `CLIPS_DB_PASSWORD` configurada no `.env`

## Passo a Passo

### 1. Listar clipes prontos para publicar

```bash
./manual-workflow/list-pending-clips.sh
```

Exibe todos os clipes com status `pending` na tabela `generated_clips`, incluindo:
- ID do clipe
- Título gerado pela IA
- Duração (calculada com start/end time)
- Caminho do arquivo de vídeo
- Caminho da thumbnail
- Score de viralidade (0–10)
- Data de criação

### 2. Localizar o arquivo de vídeo

Os clipes ficam no volume Docker. Para acessar localmente:

```bash
# Ver o volume montado
docker inspect clip-processor | grep -A5 Mounts

# Copiar clip para pasta local (substitua o ID)
docker cp clip-processor:/app/videos/clips/<arquivo>.mp4 ~/Desktop/
docker cp clip-processor:/app/videos/thumbnails/<arquivo>.jpg ~/Desktop/
```

### 3. Revisar o clipe

Assista ao vídeo antes de publicar. Verifique:
- [ ] Qualidade do corte (sem corte abrupto no início/fim)
- [ ] Legendas corretas e legíveis
- [ ] Thumbnail atrativa
- [ ] Título faz sentido para o momento

### 4. Buscar os metadados do clipe

```bash
./manual-workflow/list-pending-clips.sh --id <CLIP_ID>
```

Retorna o título, descrição e tags no formato pronto para copiar no YouTube Studio.

### 5. Fazer upload no YouTube Studio

1. Acesse [studio.youtube.com](https://studio.youtube.com)
2. Clique em **Criar → Fazer upload de vídeos**
3. Selecione o arquivo `.mp4`
4. Cole o **título** gerado pela IA (máx. 100 caracteres)
5. Cole a **descrição** completa
6. Adicione as **tags** (copie da listagem)
7. Faça upload da **thumbnail** customizada
8. Em "Público-alvo": Não é feito para crianças
9. Em "Visibilidade": **Público**
10. Em "Shorts": Marcar como Short se ≤60s
11. Clique em **Publicar**
12. Copie o **ID do vídeo** da URL (ex: `dQw4w9WgXcQ`)

### 6. Marcar como publicado no banco

```bash
./manual-workflow/mark-published.sh <CLIP_ID> <YOUTUBE_VIDEO_ID>
```

Exemplo:
```bash
./manual-workflow/mark-published.sh 42 dQw4w9WgXcQ
```

Isso atualiza o status para `published` e registra o YouTube video ID e timestamp.

## Frequência Recomendada

| Período | Frequência | Horário |
|---------|-----------|---------|
| Semana 1–2 | 1 clip/dia | 19h–20h BRT |
| Semana 3–4 | 2 clips/dia | 19h e 21h BRT |
| Mês 2+ | 3–4 clips/dia | 12h, 17h, 20h, 22h BRT |

**Por que 19h–21h?** Pico de audiência de esportes no Brasil. Evite publicar fora desse horário nas primeiras semanas para maximizar distribuição inicial.

## Solução de Problemas

### Nenhum clipe aparece na listagem

O pipeline pode não ter rodado ainda ou os vídeos estão em outro status. Verifique:

```bash
docker logs clip-processor --tail 50
./manual-workflow/list-pending-clips.sh --all-status
```

### Clip com qualidade ruim

Se o corte ficou ruim (corte no meio de frase, legenda errada), marque como falho:

```bash
./manual-workflow/mark-failed.sh <CLIP_ID> "motivo da falha"
```

### Download não aconteceu automaticamente

O step de download ainda não está conectado ao loop automaticamente. Para forçar o processamento:

```bash
docker exec clip-processor python -c "
from src.downloader import download_video
from src.db import get_connection
# ver manual-workflow/force-download.sh
"
```

Veja `force-download.sh` para o comando completo.
