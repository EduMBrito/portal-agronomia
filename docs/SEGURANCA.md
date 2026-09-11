# SEGURANÇA.md — pendências antes do deploy

Auditoria do código feita em **11 de setembro de 2026**, antes de expor o portal
à internet. Cobre `config/settings/`, `docs/nginx.conf`, `Dockerfile`,
`docker-compose.prod.yml`, views, templates e `wagtail_hooks.py`.

A lista está ordenada por risco. Os itens 1 a 3 são bloqueadores: não subir o
portal para a internet com qualquer um deles em aberto.

**Status:** item 1 resolvido em 11/09/2026 (PR #3). Restam os itens 2 e 3, que
são bloqueadores, e os quatro moderados.

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

## 2. `/media/` servido como alias direto pelo Nginx  🔴 bloqueador

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

**Correção:** liberar no Nginx apenas `/media/images/` e
`/media/original_images/`, que são públicos por natureza, e negar o resto.
Documento passa pela rota `/documents/` do Wagtail.

## 3. Upload de SVG habilitado  🔴 bloqueador

`WAGTAILIMAGES_EXTENSIONS` inclui `"svg"` em `config/settings/base.py`.

O Wagtail não sanitiza SVG — é decisão consciente do projeto e está na
documentação deles. Um SVG com `<script>` servido inline do próprio domínio é
XSS armazenado rodando na origem do portal; se um membro da comissão abrir a
imagem logado, a sessão dele está no escopo. Com o item 2 em aberto, o arquivo
chega cru ao navegador.

**Correção:** remover `svg` da lista. Se a comissão precisar de SVG para logo,
servir num `location` próprio com `Content-Disposition: attachment`.

## 4. Sem proteção contra força bruta no `/admin/`  🟡 moderado

Django e Wagtail não têm bloqueio por tentativas. O portal é público e existem
3 a 5 contas da comissão.

**Correção recomendada:** `limit_req` no Nginx para `location /admin/login/` —
zero dependência nova, que é o que importa com um mantenedor só.

`django-axes` resolve melhor e registra as tentativas, mas custa mais uma
dependência, migração e tabela para sustentar. Só vale se a auditoria
institucional exigir o log.

## 5. Dois `nginx.conf` divergentes  🟡 moderado

O bloco do `DEPLOY.md` tem `ssl_protocols TLSv1.2 TLSv1.3` e `http2`; o
`docs/nginx.conf` não tem nenhum dos dois e herda o default do sistema, que em
Ubuntu mais antigo ainda aceita TLS 1.0 e 1.1.

**Correção:** consolidar num arquivo só e o outro apontar para ele. Enquanto
houver dois, alguém vai seguir o errado.

## 6. Container roda como root  🟡 moderado

O `Dockerfile` não define `USER`, e `gcc` e `libpq-dev` permanecem na imagem
final. Uma falha de execução remota no app vira root no container, com
compilador disponível.

**Correção:** usuário não-privilegiado no `Dockerfile`. Build em múltiplos
estágios reduz a imagem e tira as ferramentas de compilação, mas isso é
otimização — o `USER` é o que importa.

## 7. `django_extensions` em produção  🟡 moderado

Está em `THIRD_PARTY_APPS` no `config/settings/base.py`, que o `production.py`
importa. É ferramenta de desenvolvimento (`shell_plus`, `runscript`) e amplia a
superfície sem necessidade.

**Correção:** mover para o `INSTALLED_APPS` do `dev.py`.

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
