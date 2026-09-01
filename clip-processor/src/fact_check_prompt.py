"""Instruções compartilhadas para verificação de fatos nos prompts de IA."""

FAKE_NEWS_STATUSES = ('positivo', 'negativo', 'inconclusivo')

FACT_CHECK_INSTRUCTION = (
    'VERIFICAÇÃO OBRIGATÓRIA DE FATOS: sempre que o trecho apresentar um fato, dado, data, número, '
    'nome, estatística, declaração ou outra informação verificável, pesquise na internet antes de '
    'escolher ou justificar o momento. Consulte fontes confiáveis e, quando possível, confirme em '
    'uma segunda fonte independente. Não invente fontes, URLs ou resultados. Em cada momento, preencha '
    '"fake_news" com "positivo" quando houver evidência de que uma afirmação é falsa, enganosa ou '
    'descontextualizada; "negativo" quando fontes confiáveis corroborarem a afirmação; ou '
    '"inconclusivo" quando não houver evidência suficiente ou a pesquisa não estiver disponível. '
    'Não alegue que pesquisou se a ferramenta web não estiver disponível. O campo "reason" deve '
    'terminar exatamente com "Fake news: <fake_news>". '
)

METADATA_FACT_CHECK_INSTRUCTION = (
    'VERIFICAÇÃO OBRIGATÓRIA DE FATOS: sempre que o trecho apresentar um fato, dado, data, número, '
    'nome, estatística, declaração ou outra informação verificável, pesquise na internet antes de '
    'escrever os metadados. Consulte fontes confiáveis e, quando possível, confirme em uma segunda '
    'fonte independente. Não invente fontes, URLs ou resultados. Use "positivo" para informação '
    'falsa, enganosa ou descontextualizada, "negativo" para informação corroborada por fontes '
    'confiáveis e "inconclusivo" quando não houver evidência suficiente ou a pesquisa não estiver '
    'disponível. Nunca inclua na descrição os rótulos "Fake news: negativo", '
    '"Verificação de fake news: negativo" ou seus equivalentes para o status inconclusivo. Somente '
    'quando o veredito for "Fake news: positivo", pule duas linhas e inclua o prefixo exatamente '
    'como "Fact Check: ", seguido dos fatos reais que corrigem a informação. Se não houver detalhes '
    'factuais adicionais disponíveis, use "Fact Check: E os fatos reais.". Não alegue que pesquisou '
    'se a ferramenta web não estiver disponível. '
)
