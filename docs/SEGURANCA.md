# SEGURANÇA.md — pendências antes do deploy

Auditoria do código feita em **11 de setembro de 2026**, antes de expor o portal
à internet. Cobre `config/settings/`, `docs/nginx.conf`, `Dockerfile`,
`docker-compose.prod.yml`, views, templates e `wagtail_hooks.py`.

A lista está ordenada por risco. Os itens 1 a 3 eram bloqueadores: não subir o
portal para a internet com qualquer um deles em aberto.

Cada item guarda o registro do problema original, e não só a correção — é o que
permite entender depois por que a configuração é do jeito que é, e evita que
alguém "simplifique" de volta.

**Status:** todos os sete itens resolvidos em 11/09/2026. Do ponto de vista do
código e da configuração, não há bloqueador conhecido para o deploy.

O que continua pendente está na última seção e não é auditável por código:
permissão do `.env` no servidor e um restore de backup efetivamente testado.

---

## 1. Django e Wagtail estão fora de suporte  ✅ resolvido em 11/09/2026

Resolvido no PR #3. Ficou como `Django==5.2.*` (LTS, suporte até abril/2028) e
`wagtail==7.4.*` (LTS, até novembro/2027). Nenhuma migração nova foi necessária
nos models do projeto e a suíte não deixou aviso de deprecação.

O registro do problema fica abaixo, porque a data de fim de suporte do novo par
é o gatilho da próxima atualização.

| Pinado antes | Situação | Fim do suporte |
|---|---|---|
| `Django==5.1.*` → 5.1.15 | **EOL** | 03/12/2025 |
| `wagtail==6.3.*` → 6.3.8 | **EOL** | 01/05/2026 |

Verificado em 11/09/2026 em `djangoproject.com/download/` e no wiki de release
schedule do Wagtail. Qualquer CVE publicado depois dessas datas não tinha
correção para as versões que estavam pinadas — era o maior risco da lista, e
nenhum hardening de Nginx compensaria.

**Próxima revisão:** conferir as datas de fim de suporte antes de
novembro/2027, que é quando o Wagtail 7.4 LTS encerra — é o mais curto dos dois.

## 2. `/media/` servido como alias direto pelo Nginx  ✅ resolvido em 11/09/2026

Está nos dois lugares: `docs/nginx.conf` e o bloco de Nginx do `docs/DEPLOY.md`.

Os templates fazem a coisa certa — `{{ doc.arquivo.url }}` aponta para
`/documents/<id>/<arquivo>`, a rota do Wagtail que checa permissão de coleção.
O problema é que o mesmo arquivo continua acessível em
`/media/documents/<nome>`, contornando essa checagem.

Consequências concretas:

- `DocumentoPage.ativo = False` tira o documento da listagem, mas o regulamento
  revogado segue baixável por quem tiver o link antigo
- Qualquer coleção privada que a comissão criar no futuro não protege nada
- O XML do Lattes deixado em `media/` vira download público — CPF, RG,
  filiação, endereço e telefone

**Corrigido no PR #6.** O `docs/nginx.conf` libera apenas `/media/images/` e
`/media/original_images/` e devolve 404 para todo o resto de `/media/`.
Documento passa pela rota `/documents/` do Wagtail.

O `WAGTAILDOCS_SERVE_METHOD = "serve_view"` virou explícito em
`config/settings/base.py`: é o que garante que o Wagtail entrega o arquivo pela
própria rota, depois de checar a coleção, em vez de redirecionar para a URL
crua. Se isso mudar, o Nginx bloqueia e todo download quebra — por isso há
teste travando o valor.

Verificado com o Nginx rodando: imagem 200, `/media/documents/ata.pdf` 404,
XML solto em `/media/` 404, e `/media/images/../documents/ata.pdf` 404.

## 3. Upload de SVG habilitado  ✅ resolvido em 11/09/2026

`WAGTAILIMAGES_EXTENSIONS` inclui `"svg"` em `config/settings/base.py`.

O Wagtail não sanitiza SVG — é decisão consciente do projeto e está na
documentação deles. Um SVG com `<script>` servido inline do próprio domínio é
XSS armazenado rodando na origem do portal; se um membro da comissão abrir a
imagem logado, a sessão dele está no escopo. Com o item 2 em aberto, o arquivo
chega cru ao navegador.

**Corrigido no PR #6.** `svg` saiu do `WAGTAILIMAGES_EXTENSIONS`. Há teste que
sobe um SVG com `<script>` dentro pelo formulário de imagem do Wagtail e exige
que seja recusado.

Se um dia a comissão precisar de SVG para logo, o caminho é um `location`
próprio no Nginx com `Content-Disposition: attachment` — não reabrir a extensão.

## 4. Sem proteção contra força bruta no `/admin/`  ✅ resolvido em 11/09/2026

Django e Wagtail não têm bloqueio por tentativas. O portal é público e existem
3 a 5 contas da comissão.

**Corrigido no PR #6** com `limit_req` no Nginx: 5 tentativas por minuto por
IP, `burst=3 nodelay`. É `location =` (correspondência exata) e não prefixo,
para não atrapalhar a comissão editando conteúdo, que faz dezenas de
requisições por minuto em `/admin/`.

Zero dependência nova, que é o que importa com um mantenedor só. Verificado:
a quinta tentativa seguida já leva 503.

`django-axes` resolveria melhor e registraria as tentativas, mas custa mais uma
dependência, migração e tabela. Só vale se a auditoria institucional exigir o
log de tentativas.

## 5. Dois `nginx.conf` divergentes  ✅ resolvido em 11/09/2026

O bloco do `DEPLOY.md` tem `ssl_protocols TLSv1.2 TLSv1.3` e `http2`; o
`docs/nginx.conf` não tem nenhum dos dois e herda o default do sistema, que em
Ubuntu mais antigo ainda aceita TLS 1.0 e 1.1.

**Corrigido no PR #6.** O `docs/nginx.conf` é a fonte única e o `DEPLOY.md`
manda copiá-lo, em vez de repetir o conteúdo. A configuração passa no
`nginx -t`, validada em container.

## 6. Container roda como root  ✅ resolvido em 11/09/2026

O `Dockerfile` não define `USER`, e `gcc` e `libpq-dev` permanecem na imagem
final. Uma falha de execução remota no app vira root no container, com
compilador disponível.

**Corrigido no PR #6.** O `Dockerfile` cria e usa o usuário `portal`
(UID 1000, para bater com o dono dos bind mounts de `media/` e `staticfiles/`).

As ferramentas de compilação saíram junto: `psycopg2-binary` e `Pillow` são
wheels manylinux e nada era construído ali. A imagem caiu de 1,18 GB para
871 MB e não tem mais compilador. Verificado no container: `uid=1000(portal)`,
Pillow grava JPEG, `psycopg2` importa.

O `CMD` padrão deixou de ser o `runserver` e virou Gunicorn — se alguém subir a
imagem sem o `command` do compose, cai num servidor de produção.

## 7. `django_extensions` em produção  ✅ resolvido em 11/09/2026

Está em `THIRD_PARTY_APPS` no `config/settings/base.py`, que o `production.py`
importa. É ferramenta de desenvolvimento (`shell_plus`, `runscript`) e amplia a
superfície sem necessidade.

**Corrigido no PR #6.** Saiu do `THIRD_PARTY_APPS` do `base.py` e passou para
o `INSTALLED_APPS` do `dev.py`, junto do `debug_toolbar`. Há teste conferindo
que nenhum dos dois está na base, já que o `production.py` faz
`from .base import *`.

---

## O que a auditoria confirmou que está certo

Registrado para não se mexer nisso por engano em uma revisão futura:

- `SECRET_KEY` e `ALLOWED_HOSTS` sem `default` — a aplicação falha alto se
  faltarem, em vez de subir com chave insegura
- HSTS de um ano com `includeSubDomains` e `preload`, cookies de sessão e CSRF
  com `Secure`, `SECURE_CONTENT_TYPE_NOSNIFF`, `X_FRAME_OPTIONS = "DENY"`,
  referrer policy restritiva
- `SECURE_PROXY_SSL_HEADER` configurado junto com o `SECURE_SSL_REDIRECT`,
  evitando o loop de redirecionamento clássico atrás de proxy
- Gunicorn exposto apenas em `127.0.0.1:8000`
- Nenhum SQL cru, `eval`, `exec`, `pickle` ou segredo hardcoded no código
- Os três `mark_safe` dos painéis do dashboard interpolam apenas inteiros e
  rótulos fixos — nenhum dado de usuário passa por eles
- Templates sob autoescape; o `{{ query }}` da busca está escapado
- `.env` no `.gitignore`

## Fora do alcance da auditoria de código

Conferir no servidor, na hora do deploy:

- Permissão e dono do `.env` (`chmod 600`, dono do serviço)
- **Restore testado.** A rotina de `pg_dump` está na seção 10 do `DEPLOY.md`,
  mas backup que nunca foi restaurado é hipótese, não backup
- Trocar o hostname do Site em `/admin/sites/` — pendência já registrada no
  `CLAUDE.md`
