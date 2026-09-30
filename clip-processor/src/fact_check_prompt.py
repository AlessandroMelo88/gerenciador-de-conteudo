"""Instruções compartilhadas para verificação de fatos nos prompts de IA."""

FAKE_NEWS_STATUSES = ('positivo', 'negativo', 'inconclusivo')

FACT_CHECK_INSTRUCTION = (
    'LIMITE DE VERIFICAÇÃO: esta etapa recebe a transcrição, mas não dispõe de ferramenta de busca '
    'nem de fontes externas. Não pesquise, não alegue consulta e não classifique uma afirmação como '
    'verdadeira ou falsa com base apenas no que o próprio vídeo diz. Para todos os momentos, use '
    '"fake_news": "inconclusivo" e termine "reason" com "Fake news: inconclusivo". '
)

METADATA_FACT_CHECK_INSTRUCTION = (
    'LIMITE DE VERIFICAÇÃO: você não recebeu resultados de busca nem fontes independentes. Não '
    'afirme que um fato foi confirmado ou desmentido, não invente correções e não acrescente um '
    'bloco "Fact Check". Descreva alegações como falas do vídeo quando isso for necessário para '
    'preservar o contexto. '
)
