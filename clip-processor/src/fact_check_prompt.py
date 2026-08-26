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
    'fonte independente. Não invente fontes, URLs ou resultados. Se houver alegação factual, inclua '
    'no final da descrição uma linha exatamente no formato "Verificação de fake news: positivo", '
    '"Verificação de fake news: negativo" ou "Verificação de fake news: inconclusivo". Use '
    '"positivo" para informação falsa, enganosa ou descontextualizada, "negativo" para informação '
    'corroborada por fontes confiáveis e "inconclusivo" quando não houver evidência suficiente ou a '
    'pesquisa não estiver disponível. Não alegue que pesquisou se a ferramenta web não estiver '
    'disponível. '
)
