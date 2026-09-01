# Hacker Libertário — Identidade e SEO do canal

> **Tipo:** referência manual de branding e SEO · **Atualizado:** 2026-08-26
> Este arquivo não é concatenado nem carregado como prompt em runtime.

Este arquivo é a fonte de verdade para a identidade do canal e para os textos usados no
YouTube Studio e no pipeline de publicação.

## Identidade atual

| Campo | Valor |
|-------|-------|
| Nome | Hacker Libertário |
| Tagline | Tecnologia, liberdade e conhecimento sem intermediários. |
| Público | Brasil; pessoas interessadas em tecnologia, IA, Linux e software livre |
| Tom | Direto, crítico, didático e curioso |
| Paleta | Grafite `#0B0F14`, verde-lima `#B7F34A`, ciano `#00D9FF` e branco `#F2F6F8` |

### Logo final

- Arquivo para upload e backup: `assets/channels/hacker-libertario/logo.png`
- Formato: PNG RGBA, 800×800px, fundo transparente
- Conceito: terminal, circuitos e símbolo de liberdade em uma marca legível em tamanho pequeno
- Upload: YouTube Studio → Personalização → Identidade visual → Foto do perfil

Os arquivos `template/banner-2048x1152.png` e `template/Logo Canal Futebol (offline).html`
são exportações da identidade antiga de futebol. Trate ambos como legado e não os use no canal
“Hacker Libertário”.

## Texto da página do canal

### Descrição “Sobre”

```text
Tecnologia, inteligência artificial, Linux, programação, open source, privacidade e soberania digital — em cortes diretos e sem enrolação.

No Hacker Libertário, você encontra ideias, ferramentas e debates que ajudam a entender como a tecnologia funciona e quem controla os sistemas que usamos. Trechos de entrevistas, podcasts e análises sobre software livre, automação, segurança e cultura hacker.

Inscreva-se para acompanhar conversas que ampliam sua autonomia digital.

Conteúdo de terceiros é publicado com os devidos créditos na descrição. Para assuntos relacionados a direitos autorais, entre em contato pelo canal.
```

### Palavras-chave do canal

Use como conjunto de referência, sem repetir palavras artificialmente:

```text
hacker libertário, cultura hacker, inteligência artificial, IA, Linux, open source, software livre, programação, privacidade digital, soberania digital, segurança da informação, automação, tecnologia, desenvolvimento de software, filosofia hacker
```

### Hashtags de referência

Use somente as que combinarem com o vídeo e mantenha o conjunto enxuto:

```text
#Hacker #Linux #OpenSource
```

## Regras de SEO para cada vídeo

1. **Título:** comece pela ferramenta, conceito, pessoa ou problema técnico que aparece no
   trecho; use uma promessa específica, uma pergunta ou uma contradição. Não copie o título da
   fonte e não desperdice espaço com “Shorts”, “corte”, “vídeo longo” ou duração.
2. **Descrição:** as primeiras linhas devem explicar o insight com a palavra-chave principal.
   Depois, inclua o contexto factual presente na transcrição, um CTA curto para inscrição e,
   quando relevante, até três hashtags. A linha de créditos entra automaticamente pelo pipeline.
3. **Tags:** combine termos amplos e específicos do trecho, em PT-BR, sem `#`, sem duplicatas e
   sem palavras-chave desconectadas do assunto. Para vídeos longos, não use `shorts` ou `cortes`.
4. **Veracidade:** nomes de ferramentas, versões, autores, vulnerabilidades, números e acusações
   só podem aparecer quando estiverem no contexto ou na transcrição disponíveis para a IA.

### Estrutura recomendada de descrição

```text
[Resumo claro do insight em uma ou duas frases.]

[Contexto: quem fala, qual problema é discutido e qual conclusão aparece no trecho.]

Inscreva-se no Hacker Libertário para acompanhar tecnologia, IA, Linux e software livre.

[Créditos gerados pelo pipeline]
#Hacker #Linux #OpenSource
```

As instruções acima já estão incorporadas em `clip-processor/src/metadata_generator.py`, que
gera os metadados dos próximos vídeos e remove hashtags/duplicatas acidentais das tags.

Os prompts ativos de seleção, metadata e thumbnail estão catalogados em
[`Docs/SISTEMA-IA-SELECAO.md`](../../Docs/SISTEMA-IA-SELECAO.md). Alterar este arquivo não altera
o prompt executado pelo worker.

## Checklist de publicação

- [ ] Foto do perfil atualizada com `assets/channels/hacker-libertario/logo.png`
- [ ] Nome do canal: **Hacker Libertário**
- [ ] Descrição “Sobre” atualizada com o texto acima
- [ ] Palavras-chave revisadas no YouTube Studio
- [ ] Título, descrição, tags e thumbnail revisados antes de publicar
