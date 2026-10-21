/** @odoo-module **/
// Liga o diálogo do número de pessoas ao arranque da contagem no Chão de Fábrica.
//
// São dois patches pequenos:
//   1. acrescentar os dois campos da operação aos dados que o Chão de Fábrica carrega;
//   2. perguntar o número antes de arrancar, na primeira contagem de cada operação.
//
// O número é gravado na operação ANTES de chamar o comportamento original. Não vai pelo
// contexto porque o `startWorking` do Enterprise monta o contexto de `button_start`
// internamente, com valores fixos — acrescentar-lhe uma chave obrigaria a reimplementar o
// método, que é longo e muda entre versões. Ver `models/mrp_workorder.py`.

import { patch } from "@web/core/utils/patch";
import { MrpDisplayAction } from "@mrp_workorder/mrp_display/mrp_display_action";
import { MrpDisplayRecord } from "@mrp_workorder/mrp_display/mrp_display_record";
import { PgPeopleCountDialog } from "@pg_mrp_people_count/js/people_count_dialog";

const CAMPOS_OPERACAO = ["pg_people_count", "pg_people_count_needed"];

patch(MrpDisplayAction.prototype, {
    get fieldsStructure() {
        const estrutura = super.fieldsStructure;
        const campos = [...(estrutura["mrp.workorder"] || [])];
        for (const campo of CAMPOS_OPERACAO) {
            if (!campos.includes(campo)) {
                campos.push(campo);
            }
        }
        return { ...estrutura, "mrp.workorder": campos };
    },
});

patch(MrpDisplayRecord.prototype, {
    // ------------------------------------------------- botão do número no cartão
    get pgShowPeopleCount() {
        return this.props.record.resModel === "mrp.workorder";
    },

    get pgPeopleCount() {
        return this.props.record.data.pg_people_count || 1;
    },

    async openPeopleCountDialog() {
        const registo = this.props.record;
        const escolhido = await this._pgAskPeopleCount(this.pgPeopleCount);
        if (!escolhido || escolhido === this.pgPeopleCount) {
            return;
        }
        // O servidor decide se corrige o registo em curso ou se o fecha e abre outro — a
        // distinção depende do tempo decorrido e não deve ser pedida ao operador.
        // Ver `pg_set_people_count` em `models/mrp_workorder.py`.
        await this.model.orm.call("mrp.workorder", "pg_set_people_count",
                                  [registo.resId, escolhido]);
        await this.env.reload(this.props.production);
    },

    _pgAskPeopleCount(atual) {
        return new Promise((resolve) => {
            let resolvido = false;
            this.dialog.add(
                PgPeopleCountDialog,
                {
                    current: atual,
                    onSelect: (numero) => {
                        resolvido = true;
                        resolve(numero);
                    },
                },
                { onClose: () => !resolvido && resolve(false) }
            );
        });
    },

    async startWorking(shouldStop = false) {
        const registo = this.props.record;
        // Só nas operações, e só à primeira contagem. Nas seguintes o valor já gravado na
        // operação é reutilizado sem incomodar o operador.
        const perguntar =
            registo.resModel === "mrp.workorder" &&
            registo.data.pg_people_count_needed &&
            !this.active;

        if (!perguntar) {
            return super.startWorking(shouldStop);
        }

        // Fechar sem escolher (Cancelar, Esc, clicar fora) devolve false e cancela o
        // arranque, em vez de arrancar com um número que ninguém confirmou.
        const escolhido = await this._pgAskPeopleCount(registo.data.pg_people_count || 1);

        if (!escolhido) {
            return;
        }

        await this.model.orm.write("mrp.workorder", [registo.resId], {
            pg_people_count: escolhido,
        });
        return super.startWorking(shouldStop);
    },
});
