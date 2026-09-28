# 📋 Regras de Negócio e Gatilhos Operacionais — Canal de Cortes

Este documento resume as regras de negócio, limites diários de download e postagem, e gatilhos de auto-expurgo do sistema.

---

## 1. 🎯 Metas Diárias de Publicação (Cota do Canal)
* **Meta Diária:** **10 vídeos por dia**
  * ⚽ **Futebol em Cortes:** 5 publicações por dia
  * 🏛️ **Cortes da Política:** 5 publicações por dia
* **Horários / Janelas de Upload:**
  * Meio-dia (12:00 BRT)
  * Noite (19:00 BRT)
  * **Ou imediato:** se aprovado manualmente pelo operador no painel.

---

## 2. 📥 Janela de Download e Captação
* **Teto Máximo por Ciclo:** **20 vídeos no total** (10 futebol + 10 política).
* **Idade Máxima do Conteúdo (48 Horas):**
  * O monitor de RSS e o worker residencial filtram estritamente:  
    `published_at >= NOW() - INTERVAL 2 DAY`.
  * **Motivo:** Notícias de futebol e política perdem relevância rapidamente. Qualquer matéria com mais de 2 dias é ignorada.

---

## 3. 🤖 Seleção e Ranqueamento por IA
* **Modo Vídeos Longos:**
  * Duração permitida: **7 a 20 minutos** (trava rígida máxima de 30 minutos).
* **Modo Vídeos Curtos (Shorts):**
  * Duração permitida: **30 a 180 segundos** (máximo 3 minutos).
* **Ranqueamento (Score 1 a 10):**
  * A IA atribui nota para cada momento viral identificado.
  * O operador revisa e aprova os **10 melhores clips** na **Fila de Aprovação**.

---

## 4. 🧹 Gatilhos de Auto-Expurgo e Limpeza de Disco (Watchdog & TTL)
* **Auto-Purge de Vídeos Velhos:**  
  Vídeos pendentes com mais de 48 horas são automaticamente marcados como descartados e removidos da fila de download.
* **Liberação de Disco Imediata:**  
  Após a publicação no YouTube (ou rejeição de um clipe), os arquivos brutos `.mp4` e `.jpg` locais são apagados, mantendo o consumo de disco do servidor sempre baixo (dentro da cota gratuita).
* **Proteção de CPU:**  
  Nenhum processo de renderização pode ultrapassar o teto estipulado, evitando congelamento ou sobrecarga do servidor.
