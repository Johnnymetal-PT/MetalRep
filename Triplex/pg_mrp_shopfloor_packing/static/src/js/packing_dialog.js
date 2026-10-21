/** @odoo-module **/
// Diálogo de packing list do produto final, aberto ao fechar a produção no Shop Floor.
// Lê/escreve os campos packing_* do produto (definidos em pg_packing_list_triplex).
// Todos os campos visíveis são obrigatórios. Ver o __manifest__.py.

import { Component, useState, onWillStart } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";
import { _t } from "@web/core/l10n/translation";
import { useService } from "@web/core/utils/hooks";

const MAX_VOLUMES = 6;

// Campos (Comprimento, Altura, Largura) de cada um dos 6 volumes possíveis.
const DIM_FIELDS = [
    ["packing_comprimento", "packing_altura", "packing_largura"],
    ["packing_comprimento_2", "packing_altura_2", "packing_largura_2"],
    ["packing_comprimento_3", "packing_altura_3", "packing_largura_3"],
    ["packing_comprimento_4", "packing_altura_4", "packing_largura_4"],
    ["packing_comprimento_5", "packing_altura_5", "packing_largura_5"],
    ["packing_comprimento_6", "packing_altura_6", "packing_largura_6"],
];

const READ_FIELDS = [
    "display_name",
    "packing_volumes",
    "packing_weight",
    "packing_cubicagem",
    ...DIM_FIELDS.flat(),
];

export class PgPackingListDialog extends Component {
    static template = "pg_mrp_shopfloor_packing.PackingListDialog";
    static components = { Dialog };
    static props = {
        close: Function,
        productId: Number,
        // Necessário para as fotografias: elas ficam na ordem de fabrico, não no produto.
        // Ver `models/mrp_production.py` para a razão.
        productionId: { type: Number, optional: true },
        onConfirm: { type: Function, optional: true },
    };

    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.state = useState({
            loaded: false,
            saving: false,
            productName: "",
            values: {},
            error: "",
            // Fotografias escolhidas nesta sessão do diálogo, ainda não enviadas.
            fotos: [],
        });
        onWillStart(async () => {
            const [record] = await this.orm.read("product.product", [this.props.productId], READ_FIELDS);
            const values = {};
            for (const field of READ_FIELDS) {
                if (field === "display_name") {
                    continue;
                }
                values[field] = record[field] || 0;
            }
            this.state.productName = record.display_name || "";
            this.state.values = values;
            this.state.loaded = true;
        });
    }

    get title() {
        return _t("Packing list do produto final");
    }

    get volumesCount() {
        const volumes = parseInt(this.state.values.packing_volumes, 10) || 0;
        return Math.max(0, Math.min(MAX_VOLUMES, volumes));
    }

    get volumeRows() {
        const rows = [];
        for (let index = 0; index < this.volumesCount; index++) {
            rows.push({
                index: index + 1,
                comp: DIM_FIELDS[index][0],
                alt: DIM_FIELDS[index][1],
                larg: DIM_FIELDS[index][2],
            });
        }
        return rows;
    }

    get cubicagem() {
        let total = 0;
        for (let index = 0; index < this.volumesCount; index++) {
            const c = this.state.values[DIM_FIELDS[index][0]] || 0;
            const a = this.state.values[DIM_FIELDS[index][1]] || 0;
            const l = this.state.values[DIM_FIELDS[index][2]] || 0;
            total += c * a * l;
        }
        return total;
    }

    onInput(field, ev) {
        const value = parseFloat(ev.target.value);
        this.state.values[field] = Number.isNaN(value) ? 0 : value;
        this.state.error = "";
    }

    _validateAll() {
        const values = this.state.values;
        if (!(values.packing_volumes > 0)) {
            return _t("Indique o número de volumes (maior que zero).");
        }
        if (!(values.packing_weight > 0)) {
            return _t("Indique o peso (maior que zero).");
        }
        for (const row of this.volumeRows) {
            if (!(values[row.comp] > 0) || !(values[row.alt] > 0) || !(values[row.larg] > 0)) {
                return _t("Preencha todas as dimensões (C/A/L) do volume %s.", row.index);
            }
        }
        return "";
    }

    async confirm() {
        const error = this._validateAll();
        if (error) {
            this.state.error = error;
            this.notification.add(error, { type: "warning" });
            return;
        }
        this.state.saving = true;
        const values = this.state.values;
        const toWrite = {
            packing_volumes: values.packing_volumes,
            packing_weight: values.packing_weight,
        };
        for (let index = 0; index < this.volumesCount; index++) {
            for (const field of DIM_FIELDS[index]) {
                toWrite[field] = values[field];
            }
        }
        try {
            await this.orm.write("product.product", [this.props.productId], toWrite);
            // As fotografias são facultativas: se não houver nenhuma, fecha-se normalmente.
            if (this.state.fotos.length && this.props.productionId) {
                await this.orm.call("mrp.production", "pg_add_packing_photos",
                                    [this.props.productionId, this.state.fotos]);
            }
        } catch (err) {
            this.state.saving = false;
            throw err;
        }
        if (this.props.onConfirm) {
            await this.props.onConfirm();
        }
        this.props.close();
    }

    // ------------------------------------------------- fotografias da embalagem

    /**
     * Lê os ficheiros escolhidos e guarda-os em memória até se gravar.
     *
     * Usa-se um `<input type="file" capture>` e NÃO a API de câmara do browser
     * (`getUserMedia`), de propósito: essa API só funciona em contexto seguro, e esta
     * instância é servida por HTTP simples. O input com `capture` abre a aplicação de
     * câmara do sistema, que funciona em HTTP — e num tablet dá ao operador exactamente o
     * mesmo gesto.
     */
    async onFotosChange(ev) {
        const ficheiros = Array.from(ev.target.files || []);
        if (!ficheiros.length) {
            return;
        }
        const lidos = [];
        for (const ficheiro of ficheiros) {
            try {
                lidos.push({ name: ficheiro.name, data: await this._lerBase64(ficheiro) });
            } catch (err) {
                this.notification.add(
                    _t("Não foi possível ler a imagem %s.", ficheiro.name),
                    { type: "warning" }
                );
            }
        }
        this.state.fotos = [...this.state.fotos, ...lidos];
        // Limpar o input permite escolher outra vez o mesmo ficheiro se for preciso.
        ev.target.value = "";
    }

    _lerBase64(ficheiro) {
        return new Promise((resolve, reject) => {
            const leitor = new FileReader();
            leitor.onload = () => {
                const resultado = String(leitor.result || "");
                const virgula = resultado.indexOf(",");
                resolve(virgula === -1 ? resultado : resultado.slice(virgula + 1));
            };
            leitor.onerror = () => reject(leitor.error);
            leitor.readAsDataURL(ficheiro);
        });
    }

    removerFoto(indice) {
        this.state.fotos = this.state.fotos.filter((_foto, i) => i !== indice);
    }

    cancel() {
        this.props.close();
    }
}
