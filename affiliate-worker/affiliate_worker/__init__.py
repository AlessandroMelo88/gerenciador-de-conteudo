"""Worker local de afiliados do Canal de Cortes.

Roda na máquina do operador, busca/importa ofertas, gera copy com IA
(Anthropic → Groq → template) e empurra para o painel via POST /api/offers.
O servidor nunca chama este worker.
"""
__version__ = '0.1.0'
