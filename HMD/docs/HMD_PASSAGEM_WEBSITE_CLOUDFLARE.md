# HMD — Passagem do website na Cloudflare

- **Tarefa:** #7040 — Dados de Acesso HMDFurniture.com
- **Passagem proposta:** quinta, 08/10/2026, às 18h (a confirmar com a Nina a 01/10)
- **Acesso:** conta Cloudflare da Parâmetro Global. A palavra-passe fica no gestor de palavras-passe, **nunca neste ficheiro nem em tarefas**. Pedido ao Hugo Ferreira: acesso em nome próprio.
- **Atenção:** a conta tem cinco clientes (casamagna.eu, gbntravel.com, hmdfurniture.com, pachecos.com, relvascork.com). Entrar sempre em `hmdfurniture.com` e confirmar o nome no topo antes de mexer.

---

## 1. Verificação feita a 30/09/2026 (sem alterações)

**DNS › Records: 20 registos.** Na passagem só mudam três:

| Registo | Hoje | Passa a |
|---|---|---|
| `hmdfurniture.com` (A) | **23.227.38.65** (Shopify), com proxy | **A → 154.58.193.71**, com proxy |
| `www` (CNAME) | **shops.myshopify.com**, sem proxy | **A → 154.58.193.71**, com proxy |
| `ftp` (CNAME) | **hmdfurniture.com**, sem proxy | **apagar**, se o Hugo confirmar que não é usado |

O `ftp` tem de sair ou passar pelo proxy. Sem proxy, depois da passagem, expõe o endereço real do servidor da Parâmetro Global, que também aloja o Odoo e outros clientes.

**Não tocar — 17 registos do email e do Microsoft 365:**

- **MX:** `hmdfurniture-com.mail.protection.outlook.com`
- **TXT:** SPF (`v=spf1 include:spf.protection.outlook.com -all`), `_dmarc`, `mail._domainkey`, `x._domainkey`, `MS=ms25889780`, `brevo-code`
- **CNAME:** `autodiscover`, `enterpriseenrollment`, `enterpriseregistration`, `lyncdiscover`, `sip`
- **SRV:** `_sip._tls`, `_sipfederationtls._tcp`
- **A:** `mail` e `webmail` (94.46.180.82); `intranet` (154.58.193.71, com proxy), que é o modelo a copiar

Se algum destes mudar, a HMD pode ficar sem email. É o maior risco da passagem.

**Por ver:**

- [ ] **SSL/TLS › Overview:** modo "Full" ou "Full (strict)"
- [ ] **Rules:** redireccionamentos existentes (por exemplo `hmdfurniture.com` → `www`)

---

## 2. Dias antes

**Na Cloudflare: certificado de origem**

1. **SSL/TLS › Origin Server › Create Certificate**, para `hmdfurniture.com` e `*.hmdfurniture.com`, válido 15 anos.
2. Guardar o **certificado** e a **chave privada**. A chave só é mostrada uma vez, e não se cola em conversas nem em tarefas.
3. Instalar no servidor, no site Apache do `hmdfurniture.com`.
4. Modo SSL em **"Full (strict)"**. O `intranet` continua a funcionar, porque o certificado dele é válido.

**No servidor e no Odoo**

- [ ] cópia de segurança da base `HMD`;
- [ ] aplicar o tema ao website «HMD Furniture 2026» (website 3), fora de horas;
- [ ] pôr o domínio `https://www.hmdfurniture.com` nesse website;
- [ ] criar no Apache o site do `hmdfurniture.com` e do `www`, com o certificado de origem, apontado à porta 9101 (produção), a partir do `hmd-le-ssl.conf` do `intranet`;
- [ ] confirmar com o Hugo que o `ftp` não é usado.

---

## 3. No dia da passagem (cerca de 5 minutos)

1. **DNS › Records › Edit** `hmdfurniture.com`: conteúdo **154.58.193.71**, com proxy.
2. **`www`:** apagar o CNAME `shops.myshopify.com` e criar **A → 154.58.193.71**, com proxy.
3. **`ftp`:** apagar, se o Hugo confirmou.
4. **Caching › Configuration › Purge Everything.**
5. Abrir `https://www.hmdfurniture.com` e `https://hmdfurniture.com`, e confirmar que aparece o site novo.
6. Confirmar que o email continua a chegar: enviar um email para um endereço `@hmdfurniture.com`.

## Reverter (efeito em segundos)

| Registo | Repor |
|---|---|
| `hmdfurniture.com` | **A 23.227.38.65**, com proxy |
| `www` | **CNAME shops.myshopify.com**, sem proxy |
| `ftp` | **CNAME hmdfurniture.com**, sem proxy |

---

## Depois da passagem

- Manter o Shopify activo uns dias, como retaguarda.
- Retirar o endereço de validação `novo.hmd.parametro.pt`: o registo DNS na zona `parametro.pt`, o domínio no website de teste e o `ServerAlias` no Apache (`hmd_teste-le-ssl.conf`). Retirar também o nome do certificado Let's Encrypt de `hmd.parametro.pt`.

## Referências

- Plano de passagem: `REUNIAO_HMD_GOLIVE_WEBSITE.md`, secção 5 (repositório do site).
- Configuração do servidor: `HMD_WEBSITE_CONFIG_PRODUCAO.md`, secção 8.
- Registos DNS verificados a 30/09/2026 na Cloudflare e por consulta pública (servidores `meg` e `rick.ns.cloudflare.com`; registo do domínio na NetEarth).
