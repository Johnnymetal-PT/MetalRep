# MH Stone Reports

Módulo de relatórios personalizados para Stone Trading.

## Relatórios Disponíveis

### Vendas
- Cotação (Quotation)
- Cotação Detalhada (Detailed Quotation)
- Factura Proforma
- Proforma com Pagamento

### Contabilidade
- Factura (Invoice)
- Nota de Crédito (Credit Note)
- Nota de Débito (Debit Note)
- Recibo de Pagamento (Payment Receipt)

### Stock
- Guia de Remessa (Delivery Guide)
- Etiquetas (Stickers)
- Número de Série (Serial Number)
- Stock de Pedras (Stone Stock)

### Compras
- Ordem de Compra (Purchase Order)

### RH
- Recibo de Salário (Payslip)

### Fiscal
- Relatórios Fiscais

---

## Configuração para Docker (wkhtmltopdf)

### Problema
Quando o Odoo corre em Docker, o **wkhtmltopdf** não consegue carregar imagens nos PDFs, mostrando o erro:
```
wkhtmltopdf: Exit with code 1 due to network error: ConnectionRefusedError
```

### Causa
O wkhtmltopdf busca imagens via HTTP. Quando o URL é `http://localhost:8071`, o container Docker tenta aceder a si próprio (não ao host), causando o erro.

### Solução

Configurar os parâmetros do sistema para usar o **IP do host** em vez de `localhost`.

#### Via Interface Odoo
1. Ir a **Settings > Technical > System Parameters**
2. Configurar/Criar os parâmetros:

| Key | Value |
|-----|-------|
| `report.url` | `http://SEU_IP:8071` |
| `web.base.url` | `http://SEU_IP:8071` |

#### Via Script Python
```python
import xmlrpc.client

URL = 'http://localhost:8071'
DB = 'nome_da_base_de_dados'
HOST_IP = 'SEU_IP'  # Ex: 192.168.1.100
PORT = '8071'

common = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/common')
uid = common.authenticate(DB, 'admin', 'admin', {})
models = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/object')

report_url = f'http://{HOST_IP}:{PORT}'

# Configurar report.url
existing = models.execute_kw(DB, uid, 'admin', 'ir.config_parameter', 'search',
    [[('key', '=', 'report.url')]])

if existing:
    models.execute_kw(DB, uid, 'admin', 'ir.config_parameter', 'write',
        [existing, {'value': report_url}])
else:
    models.execute_kw(DB, uid, 'admin', 'ir.config_parameter', 'create',
        [{'key': 'report.url', 'value': report_url}])

# Configurar web.base.url
existing_web = models.execute_kw(DB, uid, 'admin', 'ir.config_parameter', 'search',
    [[('key', '=', 'web.base.url')]])

if existing_web:
    models.execute_kw(DB, uid, 'admin', 'ir.config_parameter', 'write',
        [existing_web, {'value': report_url}])
```

### Como Descobrir o IP do Host

**Windows:**
```cmd
ipconfig
```

**Linux:**
```bash
hostname -I
```

**Python:**
```python
import socket
print(socket.gethostbyname(socket.gethostname()))
```

### Alternativas de IP

| Ambiente | IP a usar |
|----------|-----------|
| Windows/Mac (Docker Desktop) | `host.docker.internal` |
| Linux (Docker) | `172.17.0.1` (gateway Docker) |
| Rede local | IP real da máquina (ex: `192.168.1.100`) |

---

## Estrutura do Módulo

```
mh_stone_reports/
├── __init__.py
├── __manifest__.py
├── README.md
├── data/
│   └── paperformat_data.xml
├── models/
│   ├── __init__.py
│   └── res_company.py
├── reports/
│   ├── account/
│   │   ├── invoice/
│   │   └── payment/
│   ├── fiscal/
│   ├── hr/
│   ├── other/
│   ├── purchase/
│   ├── sale/
│   │   ├── detailed_quotation/
│   │   ├── ft_proforma/
│   │   ├── proforma_payment/
│   │   └── quotation/
│   ├── stock/
│   │   ├── delivery_guide/
│   │   ├── serial_nr/
│   │   ├── stickers/
│   │   └── stone_stock/
│   └── website/
├── static/
│   └── img/
│       └── stone_trading_logo.png
└── views/
    └── res_company_views.xml
```

---

## Referências

- [Solved: wkhtmltopdf ConnectionRefusedError](https://blog.mhdsyarif.com/solved-odoo-wkhtmltopdf-bexit-with-code-1-due-to-network-error-connectionrefusederrorn/)
- [wkhtmltopdf in Docker - Odoo Forum](https://www.odoo.com/forum/help-1/wkhtml2pdf-in-docker-253393)
- [GitHub Issue: ConnectionRefusedError in Docker](https://github.com/wkhtmltopdf/wkhtmltopdf/issues/3968)

---

## Configuração Actual (Stone Trading)

| Parâmetro | Valor |
|-----------|-------|
| `report.url` | `http://11.2.79.3:8071` |
| `web.base.url` | `http://11.2.79.3:8071` |
| Base de Dados | `stone_trading_2026` |

**Data:** 2026-01-09
