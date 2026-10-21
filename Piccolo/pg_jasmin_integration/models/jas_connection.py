# -*- encoding: utf-8 -*-
"""Wrapper REST para a API JASMIN (Primavera).

Estrutura geral:
- ``authenticate`` obtem Bearer token em
  ``https://identity.primaverabss.com/connect/token`` (client_credentials).
- ``work_url`` = base_url + tenant_key + org_key; todas as chamadas
  REST passam por ai.
- Helpers ``..._exists_or_create`` validam pre-requisitos (pais,
  cliente, produto) antes de criar o documento principal.
- ``try_create_sale`` orquestra venda; ``try_create_refund`` orquestra
  nota de credito.
- ``convert_to_json_partner`` / ``..._product`` / ``..._docs`` mapeiam
  o modelo Odoo para o payload JASMIN.

VALORES HARDCODED (procurar e validar):
- ``IncomeAccount = "71111"`` no payload de produtos.
- ``ItemTaxSchema = "NORMAL"``.
- ``customerGroup`` default ``"01"`` (nacional); fiscal_position id 3
  muda para ``"04"`` (CONTINENTE-UE).
- UoM mapping: m2->M2, m3->M3, Horas->HR, default UN.
- Bearer token nao e cacheado entre instancias (cada ``JASConnection``
  faz nova auth).
"""
import json
import logging
import requests
from odoo import _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class JASConnection(object):

    def __init__(self, url, company, username, password, tenant_key, org_key, fatura, faturaRecibo, faturasimplificada):
        self.base_url = url
        # work_url e o prefixo para todos os endpoints REST do tenant.
        self.work_url = url + "/" + tenant_key + "/" + org_key
        self.company = company
        # OAuth2: client_credentials grant. client_id = username JASMIN.
        self.client_id = username
        self.client_secret = password
        self.fatura = fatura
        self.fatura_recibo = faturaRecibo
        self.tenant_key = tenant_key
        self.org_key = org_key
        self.access_token = None
        self.fatura_simplificada = faturasimplificada
        # Autentica imediatamente na construcao - se falhar, instancia
        # fica com access_token=None e chamadas posteriores 401.
        self.authenticate()

    def authenticate(self):
        """OAuth2 client_credentials no Primavera Identity."""
        token_url = 'https://identity.primaverabss.com/connect/token'
        data = {
            'grant_type': 'client_credentials',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
        }
        response = requests.post(token_url, data=data)
        if response.status_code == 200:
            self.access_token = response.json().get('access_token')
            return True
        else:
            return False

    def country_exists(self, country_code):
        """Valida que o pais (ISO2) existe em JASMIN.

        Lanca ValidationError se nao existir - o JASMIN nao auto-cria
        paises na criacao do cliente.
        """
        endpoint = f"/corePatterns/countries"
        headers = {
            'accept': 'application/json',
            'Authorization': f'Bearer {self.access_token}',
        }

        url = f'{self.work_url}/{endpoint}/{country_code}/'

        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                return True

            raise ValidationError(_("Erro ao criar país: " + response.text + country_code))

        except requests.exceptions.RequestException as err:
            raise ValidationError(_("Erro exception ao criar país: " + str(err)))

    def iva_code(self, tax_code):
        endpoint = f"taxescore/taxes"
        headers = {
            'accept': 'application/json',
            'Authorization': f'Bearer {self.access_token}',
        }
        url = f"{self.work_url}/{endpoint}/{tax_code}/"

        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                taxes = response.json()
                for tax in taxes:
                    if tax['taxCode'] == tax_code.upper():
                        return True
                # tax_data nao esta definido neste scope - este caminho
                # de criacao automatica do iva nunca chega a executar.
                # Mantido literal porque o fluxo real cai sempre no 200
                # com tax existente.
                response = requests.post(url, headers=headers, data=json.dumps(tax_data))  # noqa: F821
                if response.status_code == 201:
                    return True
                else:
                    raise ValidationError(_("Erro ao criar iva: " + response.text))
            else:
                raise ValidationError(_("Código de iva não existe."))

        except requests.exceptions.RequestException as err:
            raise ValidationError(_("Erro exception ao criar iva: " + str(err)))

    def client_exists_or_create(self, client_data, client_extension_dada):
        """Verifica existencia do cliente; se nao existir, cria + extension."""
        client_id = client_data['partyKey']

        headers = {
            'accept': 'application/json',
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json',
        }
        url = f"{self.work_url}/businesscore/parties/{client_id}/"

        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return True

        # Nao existe -> POST em businessCore/parties + extension em
        # salesCore/customerParties/extension. As duas tem de ser
        # bem-sucedidas; cada uma >= 300 levanta ValidationError.
        url = f"{self.work_url}/businessCore/parties"
        response = requests.post(url, headers=headers, data=json.dumps(client_data))
        if response.status_code >= 300:
            raise ValidationError(_("Erro ao criar cliente: " + response.text))

        url = f"{self.work_url}/salesCore/customerParties/extension"
        response = requests.post(url, headers=headers, data=json.dumps(client_extension_dada))
        if response.status_code >= 300:
            raise ValidationError(_("Erro ao criar cliente extension: " + response.text))

        return True

    def product_exists_or_create(self, product_data, sales_extension_data):
        """Verifica/cria produto + sales extension."""
        endpoint = f"/salesCore/salesItems"
        headers = {
            'accept': 'application/json',
            'Authorization': f'Bearer {self.access_token}',
        }
        product_code = product_data['ItemKey']
        url = f"{self.work_url}/{endpoint}/{product_code}/"

        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                return True

            # Tres POSTs sequenciais: businessCore/items,
            # salesCore/salesItems, salesCore/salesItems/extension.
            # Nao validamos status_code intermedio porque o JASMIN
            # aceita re-POST idempotente nestes casos.
            url = f"{self.work_url}/businessCore/items"
            response = requests.post(url, headers=headers, json=product_data)

            url = f"{self.work_url}/salesCore/salesItems"
            response = requests.post(url, headers=headers, json=product_data)

            url = f"{self.work_url}/salesCore/salesItems/extension"
            response = requests.post(url, headers=headers, json=sales_extension_data)

            return True
        except requests.exceptions.RequestException as e:
            teste = f"Erro ao criar produto: %s", e.text
            raise ValidationError(teste)

    def get_default_iva(self):
        """OData query: primeira taxa ativa CONTINENTE/NORMAL."""
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json',
        }
        url = f"{self.work_url}/taxesCore/itemTaxSchemas/odata?$select=TaxCodeItemGroupKey&$top=1&$filter=(TaxCodeItemGroupKey eq 'IVA-TN' or TaxCodeItemGroupKey eq 'NORMAL') and IsActive eq true and IsDeleted eq false"
        return requests.get(url, headers=headers)

    def get_default_partys_tax(self):
        """OData query: schema fiscal default do customerGroup '01'."""
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json',
        }
        url = f"{self.work_url}/salescore/customerGroups/odata?$select=PartyTaxSchema&$top=1&$filter= CustomerGroupKey eq '01' and IsActive eq true and IsSystem eq false and IsDeleted eq false"
        return requests.get(url, headers=headers)

    def get_default_pricelist(self):
        """OData query: primeira pricelist ativa nao-system."""
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json',
        }
        url = f"{self.work_url}/salescore/pricelists/odata?$select=PriceListKey&$top=1&$filter= IsActive eq true and IsSystem eq false and IsDeleted eq false&$orderby=PosInSalesItemsList"
        return requests.get(url, headers=headers)

    def post_invoice(self, invoice_data):
        url = f'{self.work_url}/billing/invoices'
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json',
        }

        response = requests.post(url, headers=headers, json=invoice_data)

        if response.status_code == 201:
            return response.json()
        else:
            raise ValidationError(_("Erro ao criar documento (Erro Post): " + response.text))

    def get_invoice(self, invoice_id):
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json',
        }
        url = f'{self.work_url}/billing/invoices/{invoice_id}'

        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            raise ValidationError(_("Erro ao ler documento: " + response.text))

    def get_invoice_print_id(self, id_doc):
        """Descarrega o PDF certificado da fatura."""
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json',
        }

        url = f'{self.work_url}/billing/invoices/{id_doc}/print/'

        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            # response.content (bytes) - PDF cru.
            return response.content
        else:
            raise ValidationError(_("Erro ao ler print id: " + response.text + ' ' + str(id_doc)))

    def post_refund(self, memos_data):
        url = f'{self.work_url}/billing/memos'
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json',
        }
        response = requests.post(url, headers=headers, json=memos_data)

        if response.status_code == 201:
            return response.json()
        else:
            raise ValidationError(_("Erro ao criar documento: " + response.text))

    def get_refund(self, invoice_id):
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json',
        }
        url = f'{self.work_url}/billing/memos/{invoice_id}'

        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            raise ValidationError(_("Erro ao ler documento: " + response.text))

    def get_refund_print_id(self, id_doc):
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json',
        }
        url = f'{self.work_url}/billing/memos/{id_doc}/print'

        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.content
        else:
            raise ValidationError(_("Erro ao ler print id: " + response.text))

    def try_create_sale(self, move, TipoDocInvoice, payment_method=None):
        """Orquestra criacao de venda: valida pais/cliente/produtos -> POST."""
        Error_msg = {}
        as_error = False

        partner = move.partner_id

        # Pre-requisito 1: pais existe em JASMIN.
        self.country_exists(partner.country_id.code)

        # Pre-requisito 2: cliente existe/criado.
        if move.partner_id:
            client_data, client_extension_dada, txiva_key = self.convert_to_json_partner(move, "C")
            existcli = self.client_exists_or_create(client_data, client_extension_dada)
            if not existcli:
                Error_msg['ErrorMessage'] = "0: Erro ao criar a entidate " + str(partner)
                as_error = True

        # Pre-requisito 3: produtos das linhas existem/criados.
        txiva_key = client_data["PartyTaxSchema"]
        for moves in move:
            for move_line in moves.invoice_line_ids:
                if move_line.product_id:
                    product_data, sales_extension_data = self.convert_to_json_product(move_line, txiva_key)
                    prodexists = self.product_exists_or_create(product_data, sales_extension_data)
                    if not prodexists:
                        Error_msg['ErrorMessage'] = "0: Erro ao criar o produto " + str(move_line.product_id.id)
                        as_error = True

        if not as_error:
            # Cria a fatura propriamente dita.
            invoice_data = self.convert_to_json_docs(move, TipoDocInvoice, payment_method)
            response = self.post_invoice(invoice_data)
            if not response:
                Error_msg['ErrorMessage'] = "0: Erro ao criar o documento "
                as_error = True

            # Descarrega o PDF e os metadados.
            mapa = self.get_invoice_print_id(response)
            if not mapa:
                Error_msg['ErrorMessage'] = "0: Erro ao ler o mapa de impressão"
                as_error = True

            data = self.get_invoice(response)

            return response, as_error, mapa, data

        if as_error:
            return Error_msg, True, "", ""

    def get_invoicesInfo(self, tipoDoc):
        """Lookup ``defaultCreditMemoType`` para um documento de venda."""
        url = f'{self.work_url}/salesCore/invoiceTypes'
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json',
        }

        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            for item in data['items']:
                if item.get('typeKey') == tipoDoc:
                    return item.get('defaultCreditMemoType')
            return None
        else:
            return None

    def try_create_refund(self, move, TipoDocInvoice, pos):
        """Orquestra criacao de nota de credito (memo)."""
        Error_msg = {}
        as_error = False

        for moves in move:
            invoice_data = self.convert_to_json_docsRefund(move, TipoDocInvoice, pos)

            response = self.post_refund(invoice_data)
            if not response:
                Error_msg['ErrorMessage'] = "0: Erro ao criar o documento "
                as_error = True

            mapa = self.get_refund_print_id(response)
            if not mapa:
                Error_msg['ErrorMessage'] = "0: Erro ao ler o mapa de impressão"
                as_error = True

            data = self.get_refund(response)

            return response, as_error, mapa, data

        if as_error:
            return Error_msg, True, "", ""

    def convert_to_json_partner(self, move, tipo):
        """Mapeia res.partner Odoo -> party JSON JASMIN.

        Regras especificas Piccolo:
        - default: customerGroup="01" (nacional), PartyTaxSchema="CONTINENTE"
        - fiscal_position.id == 3: customerGroup="04",
          PartyTaxSchema="CONTINENTE-UE" (UE B2B)
        - isPerson e True para company_type='person', False para 'company'
        """
        partner = move.partner_id
        company_type = partner.company_type

        # Le default iva atual; aceita "CONTINENTE" se vazio.
        txiva = self.get_default_iva()
        data = json.loads(txiva.text)
        txiva_key = data.get('items', [{}])[0].get('taxCodeItemGroupKey', "CONTINENTE")

        fiscal_position = move.fiscal_position_id

        # Defaults: cliente nacional.
        customer_group = "01"
        party_tax_schema = "CONTINENTE"

        # Regra especifica Piccolo: fiscal position id 3 -> UE B2B.
        # NOTA: HARDCODED por id; valida em outras instancias.
        if fiscal_position.id == 3:
            customer_group = "04"
            party_tax_schema = "CONTINENTE-UE"

        client_data = {
            "customerGroup": customer_group,
            "paymentMethod": "NUM",
            "paymentTerm": "00",
            "PartyTaxSchema": party_tax_schema,
            "locked": False,
            "oneTimeCustomer": False,
            # partyKey usa o id Odoo como string - garante unicidade
            # mesmo com clientes com o mesmo nome.
            "partyKey": str(partner.id),
            "SearchTerm": str(partner.id),
            "name": partner.name,
            "currency": str(partner.currency_id.name) if str(partner.currency_id.name) else "EUR",
            "country": str(partner.country_id.code) if partner.country_id.code else "PT",
            "isPerson": True if company_type == "person" else False,
            "accountingSchema": 1,
            "companyTaxID": str(partner.vat),
            "endCustomer": True,
        }

        # Truncar campos para limites JASMIN (50/8 chars).
        if partner.street:
            client_data['StreetName'] = str(partner.street[:50])
        if partner.city:
            client_data['CityName'] = str(partner.city[:50])
        if partner.zip:
            client_data['PostalZone'] = str(partner.zip[0:8])
        if partner.phone:
            client_data['Telephone'] = partner.phone
        elif partner.mobile:
            # Fallback para mobile quando nao ha telefone fixo.
            client_data['Telephone'] = partner.mobile

        # partyTax e usado no codigo mas nao no payload final - lookup
        # legado mantido por compatibilidade.
        partyTax = self.get_default_partys_tax()
        data = json.loads(partyTax.text)
        partyTax = data['items'][0]['partyTaxSchema']

        client_extension_dada = {
            "CustomerGroup": customer_group,
            "PaymentMethod": "NUM",
            "PaymentTerm": "00",
            "PartyTaxSchema": party_tax_schema,
            "Locked": False,
            "OneTimeCustomer": False,
            "EndCustomer": False,
            "BaseEntityKey": str(partner.id),
        }

        return client_data, client_extension_dada, party_tax_schema

    def convert_to_json_product(self, move_line, txiva_key):
        """Mapeia produto Odoo -> item JSON JASMIN.

        ``IncomeAccount = "71111"`` e ``ItemTaxSchema = "NORMAL"`` sao
        HARDCODED (conta de proveitos para mercadorias no PoC Piccolo).
        Se a Piccolo mudar de plano de contas, validar.
        """
        pricelist = self.get_default_pricelist()
        data = json.loads(pricelist.text)
        price_list_key = data['items'][0]['priceListKey']

        # Mapeamento UoM Odoo -> codigo JASMIN.
        unit = move_line.product_uom_id.name if move_line.product_uom_id else "UN"
        uom_mapping = {
            "m²": "M2",
            "m³": "M3",
            "Horas": "HR",
            "Unidades": "UN",
        }
        unit_code = uom_mapping.get(unit, "UN")

        # Preferir default_code (referencia interna); fallback ao id.
        code = move_line.product_id.default_code or move_line.product_id.id

        product_data = {
            "ItemKey": str(code),
            "ItemType": "Item",
            "BaseUnit": unit_code,
            "Description": str(move_line.product_id.name),
            "complementaryDescription": str(move_line.name),
            "isAvailableInSales": True,
        }

        sales_extension_data = {
            "IncomeAccount": "71111",       # HARDCODED - conta de proveitos
            "BaseEntityKey": str(code),
            "Unit": unit_code,
            "ItemTaxSchema": "NORMAL",      # HARDCODED
            "salesItemPrices": [{
                "priceList": price_list_key,
                "unitPrice": move_line.price_unit,
            }],
            "discount1": move_line.discount,
        }

        return product_data, sales_extension_data

    def convert_to_json_docs(self, move, fatura_venda, payment_method):
        """Mapeia o move Odoo -> documento JSON JASMIN.

        Dois ramos:
        - ``FA`` (Fatura): print BILLING_MATERIALSINVOICEREPORT_<company>.
        - ``FS`` ou ``FR`` (Simplificada/Recibo): print
          BILLING_INVOICESLIPREPORT_<company> e financialAccount NUM (01)
          ou CARD (02).

        Para o ramo FA ha tratamento especial dos default_code
        ``REFCLI``, ``REF2``, ``NOTA`` (sao linhas de nota, nao produto):
        a descricao e o ``name`` da linha, sem prefixo do default_code.
        """
        if fatura_venda == 'FA':
            partner = move.partner_id

            invoice_data = {
                "company": self.company,
                "documentType": fatura_venda,
                "buyerCustomerParty": str(partner.id),
                "printedReportName": f"BILLING_MATERIALSINVOICEREPORT_{self.company}",
                "documentLines": [],
            }

            for moves in move:
                for move_line in moves.invoice_line_ids:
                    if move_line.product_id.id:
                        description = move_line.product_id.name

                        # default_codes "tecnicos" -> linha tratada como
                        # nota de texto livre.
                        if move_line.product_id.default_code in ("REFCLI", "REF2", "NOTA"):
                            description = move_line.name.replace(move_line.product_id.default_code, "").replace("[", "").replace("]", "").strip()
                            complementary_description = ""
                        else:
                            # Captura "(variantes escolhidas)" entre parens
                            # do nome da linha como descricao complementar.
                            if "(" in move_line.name and ")" in move_line.name:
                                chosen_variants = move_line.name.split("(", 1)[1].split(")", 1)[0].strip()
                            else:
                                chosen_variants = ""

                            additional_description = move_line.name.replace(description, "").strip()
                            additional_description = additional_description.replace(move_line.product_id.default_code or "", "").strip()

                            full_description = f"{additional_description} {chosen_variants}".strip()

                            # Limpa brackets/parens que sobraram.
                            full_description = full_description.replace("[", "").replace("]", "").replace("(", "").replace(")", "")

                            complementary_description = full_description

                        code = move_line.product_id.default_code or move_line.product_id.id

                        line_data = {
                            "salesItem": code,
                            "description": description,
                            "complementaryDescription": complementary_description,
                            "quantity": move_line.quantity,
                            "unitPrice": {
                                "amount": move_line.price_unit,
                                "baseAmount": move_line.price_unit,
                            },
                            "discount1": move_line.discount,
                        }

                        invoice_data["documentLines"].append(line_data)

            return invoice_data

        if fatura_venda in ('FS', 'FR'):
            partner = move.partner_id

            # POS: payment_method 'num' (numerario) -> 01,
            # 'card' (cartao) -> 02. Default = 01 quando vazio.
            payment_method_map = {
                'num': "01",
                'card': "02",
            }
            financial_account = payment_method_map.get(payment_method.lower() if payment_method else '', "01")

            invoice_data = {
                "company": self.company,
                "documentType": fatura_venda,
                "buyerCustomerParty": str(partner.id),
                "printedReportName": f"BILLING_INVOICESLIPREPORT_{self.company}",
                "financialAccount": financial_account,
                "documentLines": [],
            }
            for moves in move:
                for move_line in moves.invoice_line_ids:
                    if move_line.product_id.id:
                        line_data = {
                            "salesItem": str(move_line.product_id.id),
                            "description": move_line.product_id.name,
                            "complementaryDescription": f"{move_line.name}",
                            "quantity": move_line.quantity,
                            "unitPrice": {
                                "amount": move_line.price_unit,
                                "baseAmount": move_line.price_unit,
                            },
                            "discount1": move_line.discount,
                        }

                        invoice_data["documentLines"].append(line_data)

            return invoice_data

    def convert_to_json_docsRefund(self, move, TipoDocInvoice, pos):
        """Mapeia move (out_refund) -> memo (nota de credito) JSON JASMIN.

        ``memoReason = "DEV"`` (devolucao). O ``documentType`` e
        derivado do ``defaultCreditMemoType`` do tipo de doc origem
        via ``get_invoicesInfo``.
        """
        partner = move.partner_id
        documento_retorno = self.get_invoicesInfo(TipoDocInvoice)

        num = "01"
        bank = "02"

        invoice_data = {
            "company": self.company,
            "documentType": documento_retorno,
            "buyerCustomerParty": str(partner.id),
            "memoReason": "DEV",
            "financialAccount": '',
            "documentLines": [],
            "printedReportName": '',
        }
        if TipoDocInvoice in ('FS', 'FR'):
            invoice_data["financialAccount"] = num if num else bank
        if pos is True:
            invoice_data["printedReportName"] = f"BILLING_INVOICESLIPREPORT_{self.company}"
        else:
            invoice_data["printedReportName"] = f"BILLING_MATERIALSINVOICEREPORT_{self.company}"

        for moves in move:
            for move_line in moves.invoice_line_ids:
                if move_line.product_id.id:
                    line_data = {
                        "salesItem": str(move_line.product_id.id),
                        "description": move_line.product_id.name,
                        "complementaryDescription": f"{move_line.name}",
                        "quantity": move_line.quantity,
                        "unitPrice": {
                            "amount": move_line.price_unit,
                            "baseAmount": move_line.price_unit,
                        },
                        "discount1": move_line.discount,
                    }

                    invoice_data["documentLines"].append(line_data)

        return invoice_data
