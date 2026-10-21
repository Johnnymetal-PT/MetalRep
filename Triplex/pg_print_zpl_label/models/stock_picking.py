# -*- coding: utf-8 -*-
"""Impressão de etiquetas de receção em ZPL numa Zebra ligada à IoT Box.

Ver o __manifest__.py para o objetivo, dependências e avisos (impressora com nome fixo,
campos Studio, verify=False, etc.).
"""
import base64
import json
import uuid

import requests
from odoo import fields, models
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = "stock.picking"

    @staticmethod
    def _pg_zpl_safe(value):
        # Remove caracteres que quebrariam o ZPL: quebras de linha e os comandos ^ e ~.
        return (str(value or "")).replace("\r", " ").replace("\n", " ").replace("^", " ").replace("~", " ")

    @staticmethod
    def _pg_send_zpl_to_iot(device, zpl):
        # Envia a string ZPL para a IoT Box, que a encaminha para a impressora.
        if not device or not device.identifier:
            raise UserError("IoT printer is not configured correctly (missing device identifier).")

        base_url = (device.iot_id.ip_url or "").rstrip("/")
        if not base_url:
            if not device.iot_id.ip:
                raise UserError("IoT Box has no IP configured.")
            base_url = f"http://{device.iot_id.ip}:8069"

        action_url = f"{base_url}/hw_drivers/action"
        action_data = {
            "document": base64.b64encode(zpl.encode("utf-8")).decode("ascii"),
            "print_id": str(uuid.uuid4()),
            "iot_idempotent_id": str(uuid.uuid4()),
        }
        payload = {
            "params": {
                "session_id": str(uuid.uuid4()),
                "device_identifier": device.identifier,
                "data": json.dumps(action_data),
            }
        }

        try:
            response = requests.post(
                action_url,
                json=payload,
                timeout=12,
                verify=False,
            )
            response.raise_for_status()
            result = response.json()
        except Exception as exc:
            raise UserError(f"Failed to send ZPL to IoT Box at {action_url}: {exc}") from exc

        # /hw_drivers/action returns a json boolean result.
        if not result:
            raise UserError("IoT Box did not accept the print action for this device.")

    def action_print_zpl_label(self):
        # Ponto de entrada (botão): gera e imprime as etiquetas de cada picking selecionado.
        for picking in self:
            labels = []
            # Usa as linhas sem embalagem; se não houver, recorre a todas as linhas com produto.
            moves = picking.move_ids_without_package.filtered(lambda m: m.product_id)
            if not moves:
                moves = picking.move_ids.filtered(lambda m: m.product_id)

            today_str = fields.Datetime.context_timestamp(picking, fields.Datetime.now()).strftime("%d/%m/%Y")
            # Campos Studio: tecido -> 1 etiqueta só; nº de encomenda interno -> impresso na etiqueta.
            tecido_single_label = bool(getattr(picking, "x_studio_tecido", False))
            enc_interno_val = self._pg_zpl_safe(getattr(picking, "x_studio_n_encomenda_interno", "") or "")

            for move in moves:
                # Venda -> compra -> "-". Decidido com o cliente a 28/07/2026.
                #
                # A venda ganha sempre, que era o pedido. A compra entra como recurso para as
                # compras soltas — feitas sem encomenda associada, como o tecido comprado
                # para stock —, em que não há venda nenhuma para identificar.
                #
                # Os dois não se confundem na etiqueta porque os prefixos são diferentes:
                # `S00537` é venda, `P00026` é compra.
                #
                # O que saiu de propósito da precedência foi o grupo de procura e o `origin`
                # em bruto. A precedência anterior era `venda -> grupo de procura -> origin`,
                # e era a causa da queixa: medido nesse dia, em 2839 receções, a maioria das
                # etiquetas saía com o nome do grupo de procura. E o `origin` em bruto podia
                # imprimir texto livre como "Retorno de WH/OUT/00211", que não é referência
                # de nada para quem lê a etiqueta.
                enc_val = ((picking.so_id and picking.so_id.name)
                           or (picking.po_name or "")
                           or "-")
                cliente_val = (picking.partner_id and picking.partner_id.name) or ""
                artigo_val = (move.product_id and move.product_id.display_name) or ""
                desc_raw = (
                    move.description_picking
                    or (move.product_id and getattr(move.product_id, "description_picking", False))
                    or ""
                )
                desc_val = desc_raw.replace("\r", " ").replace("\n", " ")

                # Quantidade a imprimir: o que foi feito, ou o planeado se ainda não houver feito.
                done_qty = sum(move.move_line_ids.mapped("qty_done")) if move.move_line_ids else 0.0
                qty_to_print = done_qty if done_qty and done_qty > 0 else (move.product_uom_qty or 0.0)
                qty_int = int(qty_to_print)
                # Tecido imprime sempre 1 etiqueta; restantes imprimem uma por unidade.
                label_count = 1 if tecido_single_label else qty_int

                if label_count <= 0:
                    continue

                enc_val = self._pg_zpl_safe(enc_val)
                cliente_val = self._pg_zpl_safe(cliente_val)
                artigo_val = self._pg_zpl_safe(artigo_val)
                desc_val = self._pg_zpl_safe(desc_val)

                for _ in range(label_count):
                    labels.append(
                        f"""^XA
^CI28
^MTD
^MNY
^PW800
^LL560
^LS0
^LT0
^LH0,0

^FO20,50^GFA,4012,4012,59,gN06P02gI03S01,I01E07CM03MFCI01F8M0103EM07F8J01F8J01FCJ01FCK07EN0FCP03FEO0FFC,I07F07EM07MFCI03F8L01F83F8L07F8J07FCJ01FEJ07FEK0FFM01FF8O0IF8M03IF,I0FF07F8L07MFCI03FCL03FC3FEL07FCJ07FEJ01FEJ07FEK0FFM01FF8N03IFCM0JF8,001FF07FCL07MFCI03FCL07FC3FFL07F8J07FEJ01FEJ03FFK0FFM01FFCN07JFL01JFC,003FF87FEL07MFCI03FCL0FFC3FF8K07FCJ07FFJ01FEJ03FFJ01FFM03FFCN0KFL03JFE,007FF87FFL07MFCI03FCK01FFC3FFCK07FCJ03FFJ03FEJ03FF8I01FFM03FFCM01KF8K07KF,00IF87FF8K03MFCI03FCK03FFC3FFEK07FCJ03FF8I03FEJ01FF8I01FFM03FFEM03KFCK07KF8,01IF87FF8K03MFCI03FCK03FFC3FFEK07FCJ03FF8I03FEJ01FFCI01FFM03FFEM07KFEK0LF8,01IF87FFCK03MFCI03FCK07FFC3IFK07FCJ01FF8I03FEK0FFCI01FFM07FFEM07KFEK0LFC,03IF07FFEK03MFCI03FCK07FFC3IFK07F8K0FFCI03FEK0FFEI01FFM07FFEM0LFEJ01LFC,07IF07FFEK03MFCI03FCK0IF81IF8J07F8K0FFEI03FEK07FEI01FFM07IFM0MFJ01LFC,07FFE03IFM07FFCL03FCK0IF81IFCJ07F8K0FFEI03FEK07FFI01FFM0JFM0MFJ03LFE,0IFC01IFW03FCJ01IF00IFCJ07F8K07FFI03FEK03FFI01FFM0JFL01IF0IFJ03FFC3FFE,0IF800IF8V03FCJ01FFE003FFEJ07F8K07FFI03FEK03FF8001FFM0JF8K01FFE03FF8I03FF80FFE,1IFI07FF8V03FCJ03FFC001FFEJ07F8K03FF8003FEK03FF8001FFL01JF8K01FFC01FF8I03FF007FE,1FFEI03FFCV03FCJ03FF8I0FFEJ07F8K03FF8003FEK01FFC001FFL01JF8K01FF800FF8I03FE003FE,1FFCI01FFCV03FCJ03FF8I07FFJ07F8K03FFC003FEK01FFC001FFL01JFCK01FFI0FF8I03FE003FE,3FF8J0FFEV03FCJ07FFJ07FFJ07F8K01FFC003FEL0FFE001FFL01JFCK01FFI0FF8I07FC001FE,3FF8J0FFEV03FCJ07FEJ03FFJ07F8K01FFE003FEL0FFE001FFL03JFCK01FEI07F8I07FC001FE,3FFK07FEV03FCJ07FEJ01FFJ07F8L0FFE003FEL07FF001FFL03JFCK01FEI07F8I03F8001FE,3FFK07FFV01FCJ07FCJ01FFJ03F8L0IF003FEL07FF001FFL03JFEK01FCI0FF8I03F8001FE,7FEK03FFW0F8J0FFCK0FFJ03FM07FF003FEL03FF801FFL03JFEL0F8I0FF8I01FI03FF,7FEK03FFgI0FFCK07FS07FF803FEL03FF801FFL07FE7FEQ0FF8N03FE,7FCK03FFgI0FF8K01ES03FF803FEL01FFC01FFL07FE7FEQ0FF8N03FE,7FCK01FFgI0FF8g03FFC03FEL01FFC01FFL07FC3FFP01FF8N07FE,7FCK01FFgI0FF8R02M01FFC03FEM0FFE01FFL0FFC3FFP01FF8N07FE,7FCK01FFV01FCJ0FF8Q03FM01FFE03FEM0FFE01FFL0FFC3FFP03FFO0FFE,FFCK01FFV01FCJ0FF8Q03F8L01FFE03FEM07FF01FFL0FF81FF8O07FFO0FFE,FFCK01FFJ07MFJ03FCJ0FF8Q03F8M0IF03FEM07FF01FFK01FF81FF8O0IFN01FFC,FF8K01FFJ07MFJ03FCJ0FF8Q03F8M0IF03FEM03FF81FFK01FF81FF8O0FFEN03FFC,FF8L0FFJ07MFJ03FCJ0FF8Q03F8M07FF83FEM03FF81FFK01FF80FF8N01FFEN03FF8,FF8L0FFJ07MFJ03FCJ0FF8Q03F8M07FF83FEM01FFC1FFK01FF00FFCN03FFCN07FF8,FF8L0FFJ07MFJ03FCJ0FF8Q07F8M03FFC3FEM01FFC1FFK03FF00FFCN07FFCN0IF,FF8L0FFJ07MFJ03FCJ0FF8Q07F8M03FFC3FEM01FFE1FFK03FF00FFCN0IF8M01IF,FF8L0FFJ07MFJ03FCJ0FF8Q07F8M01FFE3FEN0FFE1FFK03FE007FEM01IF8M03FFE,FF8K01FFJ07MFJ03FCJ0FF8Q07F8M01FFE3FEN0IF1FFK03FE007FEM01IFN07FFC,FF8K01FFJ07MFJ03FCJ0FF8Q07F8N0IF3FEN07FF1FFK07FE007FEM03FFEN0IFC,FF8K01FFJ07LFEJ03FCJ0FF8Q07F8N0IF3FEN07FFBFFK07FC003FEM07FFCN0IF8,FFCK01FFJ07LFK03FCJ0FF8Q07F8N07FFBFEN03KFK07FC003FFM0IFCM01IF,7FCK01FFJ07FFO03FCJ0FF8Q07F8N07JFEN01KFK07FC003FFL01IF8M03FFE,7FCK01FFJ07FEO03FCJ0FF8Q07F8N03JFEN01KFK0FFC003FFL01IFN07FFC,7FCK03FFJ07FEO03FCJ0FF8Q07F8N03JFEN01KFK0FF8001FFL03FFEN0IF8,7FEK03FFJ07FEO03FCJ0FFCK07FJ07F8J03E001JFEJ01FI0KFK0FF8001FF8K07FFCM01IF,7FEK03FFJ07FCO03FCJ0FFCK0FFJ07F8J07F001JFEJ03F800KFK0FF8001FF8K0IFCM01IF,7FFK07FEJ07FCO03FCJ0FFCK0FFJ07F8J07F800JFEJ07F8007JFJ01FFJ0FF8K0IF8M03FFE,3FFK07FEJ07FCO03FCJ07FEJ01FFJ07F8J07F800JFEJ07F8007IFEJ01FFJ0FF8J01IFN07FFC,3FF8J0FFEJ07FCO03FCJ07FEJ03FFJ07F8J07F8007IFEJ07F8003IFEK0FEJ0FFCJ03FFEN07FF8,3FF8I01FFCJ07FCO07FCJ07FFJ03FFJ07F8J0FF8007IFEJ07F8003IFEK07CJ0FFCJ03FFCN0IF,1FFCI01FFCJ03FCO07FCJ07FF8I07FFJ07F8J0FF8003IFEJ07FC001IFEQ0FFCJ07FF8N0IF,1FFEI03FFCJ03FCO07FCJ03FFCI07FFJ07F8J0FF8001IFEJ07FC001IFEQ07FEJ07FF8M01FFE,0IFI07FFCJ03FCO07FCJ03FFEI0FFEJ07F8J0FF8001IFEJ07FCI0IFEQ07FEJ0IFN01FFE,0IF800IF8J03FCO07FCJ03FFE003FFEJ07F8J0FF8I0IFEJ07FCI0IFEQ0FFEJ0IFN03FFE,07FFE01IF8J03FCO07FCJ01IF007FFCJ07F8J0FF8I0IFEJ07FCI07FFEM03LFJ0JFM03IFE,07IF03IFK03FCO07FCJ01IF81IFCJ07F8J0FF8I07FFEJ07FCI07FFEJ0PFI01MF8I03LFE,03IF87IFK03FCO07FCK0IF83IF8J07F8J0FF8I07FFEJ07FCI03FFEJ0PFI01MF8I03LFE,03IF87FFEK03FCO03FCK0IFC3IF8J07F8J0FF8I03FFEJ07FCI03FFEJ0PFI01MF8I07MF,01IF87FFEK03FCO03FCK07FFC3IFK07F8J0FF8I03FFEJ07FCI01FFEI01PF8001MF8I07MF,00IF87FFCK03FCO03FEK03FFC3FFEK07F8J0FF8I01FFEJ07FCI01FFEI01PF8001MF8I07MF,00IF87FF8K03FCO03FEK03FFC3FFEK07F8J0FF8I01FFEJ07FCJ0FFEI01PF8003MF8I07MF,007FF87FFL03FCO03FEK01FFC3FFCK07F8J0FF8J0FFEJ07FCJ07FEI01PF8003MF8I07MF,003FF87FEL03FCO03FEL0FFC3FF8K07F8J07F8J07FEJ07FCJ07FEI03PF8001MF8I07MF,001FF87FCL03FCO03FEL07FC3FFL07F8J07F8J07FEJ07FCJ03FEI03PFC001MF8I07MF,I07F87F8L03FCO03FEL03FC3FEL07F8J07FK03FCJ07FCJ03FEI03PFC001MF8I03LFE,I03F07EM03FCO03FEL01FC1F8L07F8J07FK03FCJ03FCJ01FEI01PF8I0MF8I03LFE,J06078g0F8M0781FM07gV0200FFEM07KF8J01KFE,gY01C,,^FS

^FO500,60^A0N,28,28^FDRECEPCAO MERCADORIA^FS
^FO500,105^A0N,26,26^FDN Enc.^FS
^FO580,95^A0N,46,46^FD{enc_val}^FS

^FO30,200^A0N,28,28^FDCliente:^FS
^FO180,200^A0N,28,20^FB560,2,2,L,0^FD{cliente_val}^FS

^FO500,145^A0N,26,26^FDN Enc. Int.^FS
^FO620,145^A0N,32,22^FB170,2,0,L,0^FD{enc_interno_val}^FS

^FO30,260^A0N,30,30^FDARTIGO^FS
^FO180,260^A0N,32,22^FB560,2,0,L,0^FD{artigo_val}^FS

^FO30,320^A0N,28,28^FDDescricao:^FS
^FO180,320^A0N,26,18^FB560,3,2,L,0^FD{desc_val}^FS

^FO30,480^A0N,30,30^FDQNT:^FS
^FO180,475^A0N,36,36^FB120,1,0,L,0^FD{qty_int}^FS

^FO30,525^A0N,26,26^FDDATA:^FS
^FO100,525^A0N,26,26^FD{today_str}^FS
^XZ"""
                    )

            if not labels:
                continue

            # Junta todas as etiquetas e envia para a impressora Zebra ligada à IoT Box.
            zpl = "\n".join(labels)
            device = self.env["iot.device"].sudo().search(
                [
                    ("name", "=", "ZDesigner ZD421-203dpi ZPL"),
                    ("type", "=", "printer"),
                    ("connected", "=", True),
                ],
                limit=1,
            )
            if not device:
                raise UserError("No connected IoT printer found with name 'ZDesigner ZD421-203dpi ZPL'.")

            self._pg_send_zpl_to_iot(device, zpl)

