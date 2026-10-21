"""Merge multifornecedor.

Quando varios fornecedores oferecem o mesmo produto, o merger decide qual e
o registo "vencedor" para publicacao e guarda o resto em ``compare_data``
para auditoria. Regras de selecao (em ``merge``):

1. Se o seleccionado actual tem quantidade 0 e a alternativa tem stock,
   troca-se de fornecedor.
2. Se a alternativa tem stock e preco menor (positivo) que o actual, troca.

A chave de agrupamento (``_group_key``) usa EAN13 valido se existir, depois
referencia, depois um fingerprint do payload normalizado.
"""

from collections import defaultdict

from .utils import fingerprint_for_payload, is_valid_ean13


class HiperMerger:
    """Agrupa rows iguais entre fornecedores e elege o registo a publicar."""

    def merge(self, vendor_rows):
        groups = defaultdict(list)
        for row in vendor_rows:
            groups[self._group_key(row)].append(row)

        merged = []
        for key, rows in groups.items():
            selected = None
            compare_data = {}
            for row in rows:
                compare_data[f"module_{row['vendor_code']}"] = {
                    "quantity": row["quantity"],
                    "unit_price": row["unit_price"],
                    "wholesale_price": row["wholesale_price"],
                }
                if not selected:
                    selected = row
                    continue
                selected_qty = selected.get("quantity", 0)
                row_qty = row.get("quantity", 0)
                selected_price = selected.get("unit_price", 0.0)
                row_price = row.get("unit_price", 0.0)
                if selected_qty == 0 and row_qty > 0:
                    selected = row
                elif row_qty > 0 and row_price and (selected_price == 0 or row_price < selected_price):
                    selected = row
            if selected:
                selected = dict(selected)
                selected["group_key"] = key
                selected["compare_data"] = compare_data
                merged.append(selected)
        return merged

    def _group_key(self, row):
        ean13 = row.get("ean13")
        if is_valid_ean13(ean13):
            return ean13
        return fingerprint_for_payload(
            row.get("name_pt") or row.get("name") or "",
            row.get("description_short_pt") or row.get("description_short") or "",
            row.get("description_pt") or row.get("description") or "",
        )
