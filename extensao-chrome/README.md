# Extensão "Transcrever esta aula"

Um clique na página da aula e ela entra na base de conhecimento (aba **Transcrições** do painel).
Funciona em site com login (Hotmart, Asimov, Vimeo...) usando o login que você **já tem no Chrome**.

## Instalar (uma vez)

1. Chrome → `chrome://extensions`
2. Ligue **Modo do desenvolvedor** (canto superior direito)
3. **Carregar sem compactação** → escolha esta pasta (`extensao-chrome`)
4. Fixe o ícone na barra (ícone de quebra-cabeça → alfinete)

## Usar

Abra a aula logado → clique no ícone → **Transcrever**. O andamento aparece em Transcrições.

## Como funciona e o que sai do seu Mac

```
Chrome (aba da aula) ──link + sessão só deste site──> worker do Mac (127.0.0.1:8765)
                                                         ├─ sessão → ~/.config/canaldecortes/cookies.txt (600)
                                                         └─ link  → fila transcription_jobs (servidor)
```

- A sessão **não vai para o servidor** nem para o repositório: fica no `cookies.txt` do Mac.
- A extensão manda só os cookies do site da aba aberta, não os do navegador inteiro.
- A API local só aceita pedido de extensão (cabeçalho `Origin: chrome-extension://`); um site
  qualquer aberto no Chrome recebe `403`.
- O worker do Mac precisa estar ligado. Se não estiver, a extensão avisa.

Código do lado do Mac: `scripts/extensao_api.py`. Testes: `scripts/test_extensao_api.py`.
