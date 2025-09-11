# Documentação de Uso da API

## Sumário Rápido
- Autenticação: Chave de API do Site (obrigatória)
- Formato: JSON
- Base URL (dev): `http://127.0.0.1:8000/api/`
- Padrão de paginação: PageNumber (?page=, ?page_size=)
- Códigos de resposta principais: 200 (OK), 201 (Criado), 400 (Erro validação), 401 (Não autenticado), 403 (Sem permissão), 404 (Não encontrado)

# Documentação (Escopo Reduzido) – Endpoint Único de Agregação de Site

Este documento reflete exclusivamente o **único** endpoint novo criado para retornar os dados compilados de um site. Todo o restante da API existente não faz parte deste escopo e foi removido desta página para evitar ambiguidade.

## 1. Autenticação (Obrigatória)
O endpoint exige exclusivamente uma chave de API específica do site enviada em `X-API-Key`.

Formato da chave: `PREFIX.TOKENLONGO` (o prefixo possui 8 caracteres).

Procedimento:
1. No painel admin (`/admin-panel/` > Sistema > API Keys) gere a chave (exibida só uma vez).
2. Armazene de forma segura no backend/frontend do site.
3. Em cada requisição inclua `X-API-Key: PREFIX.TOKENLONGO`.
  
CLI (alternativo):
```
python manage.py create_site_api_key <dominio> --name="Frontend Público"
```
Saída exibirá a chave completa uma única vez.

Regras:
- Revogação imediata ao desativar a chave.
- `last_used_at` é atualizado a cada uso.
- Chaves são vinculadas a exatamente um site ativo.
- (Opcional) Pode enviar também `domain=<dominio>` para validar correspondência.

## 2. Endpoint Único
`GET /api/site/full/?domain=<dominio>` (header obrigatório `X-API-Key`)

### 2.1 Parâmetros de Query
| Parâmetro | Tipo | Default | Min/Max | Descrição |
|-----------|------|---------|---------|-----------|
| domain | string | - | - | (Obrigatório) Domínio (ou parte) do site |
| ttl | int | 300 | 30–1800 | TTL do cache em segundos |

### 2.2 Estrutura de Resposta (Exemplo Simplificado)
```json
{
  "id": 1,
  "domain": "https://exemplo.com",
  "status": "active",
  "bio": {
    "title": "Meu Site",
    "logo": "http://.../media/sites/logos/logo.png"
  },
  "categories": [{"id":10,"name":"Categoria"}],
  "services": [{"id":5,"title":"Serviço","final_value":"100.00"}],
  "social_networks": [{"id":3,"network_type":"instagram","url":"https://..."}],
  "ctas": [{"id":2,"title":"Fale Conosco"}],
  "blog_posts": [{"id":7,"title":"Post","published_at":"2025-09-11T15:00:00Z"}],
  "banners": [{"id":1,"image":"http://.../banner.png"}],
  "cache": {"hit": false, "ttl": 300, "key": "site_full:1:1757210170"}
}
```

### 2.3 Regras de Inclusão
- `social_networks`, `ctas`, `banners`: apenas itens ativos (`is_active=true`)
- `blog_posts`: somente publicados (`is_published=true`)
- `services.final_value`: calculado dinamicamente a partir de `value` e `discount`

### 2.4 Estratégia de Cache
Chave: `site_full:<site_id>:<timestamp>` onde `<timestamp>` = maior `updated_at` entre site e relacionamentos. Alterou algum registro? Nova chave automaticamente.

### 2.5 Erros Possíveis
| Código | Motivo | Ação |
|--------|-------|------|
| 400 | Parâmetros inválidos | Verificar query |
| 401 | Chave ausente / inválida | Verificar header X-API-Key |
| 403 | Domain não corresponde ou site inativo | Validar domínio/status |
| 404 | (Não usado na chave) | - |

## 3. Snippets
PowerShell / curl:
```
$APIKEY="PREFIX.TOKENLONGO"
curl -H "X-API-Key: $APIKEY" "http://127.0.0.1:8000/api/site/full/?domain=meusite.com&ttl=600"
```
Python (requests):
```python
import requests
API_KEY = "PREFIX.TOKENLONGO"
r = requests.get(
  'http://127.0.0.1:8000/api/site/full/?domain=meusite.com&ttl=120',
  headers={'X-API-Key': API_KEY}
)
print(r.status_code, r.json()['cache'])
```

## 4. Checklist Rápido
1. ID correto? 404 indica possivelmente inexistente.
2. Cache não reflete mudança? Confirme se objeto alterado teve `updated_at` atualizado.
3. Campo ausente? Verifique se item está ativo/publicado.

## 5. Extensões Futuras (Opcional)
- Suporte a `?include=` e `?exclude=`.
- ETag / If-Modified-Since.
- Paginação de coleções grandes.
- Rotação / escopo de chaves (ex: origem permitida).

## 6. Change Log (Este Documento)
- Versão reduzida criada para alinhar ao requisito de **um único endpoint** agregado.

_Fim._

