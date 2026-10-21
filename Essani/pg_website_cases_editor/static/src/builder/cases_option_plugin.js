import { BEGIN, SNIPPET_SPECIFIC_END } from "@html_builder/utils/option_sequence";
import { Plugin } from "@html_editor/plugin";
import { isElement } from "@html_editor/utils/dom_info";
import { withSequence } from "@html_editor/utils/resource";
import { registry } from "@web/core/registry";
import { _t } from "@web/core/l10n/translation";
import { BaseAddProductOption } from "@html_builder/plugins/add_product_option";
import { BaseOptionComponent } from "@html_builder/core/utils";

/**
 * Cartões dos "casos reais" da página Inspiração do website V5.
 *
 * Os cartões são `div.case` simples dentro de uma grelha `.pg-cases`. O construtor do Odoo 19
 * só mostra clonar/remover/mover em blocos para os quais exista uma opção (seletor), e nenhuma
 * das do standard apanha este `div`. Este plugin regista-o, e com isso:
 *
 * - o cartão passa a ser um bloco selecionável, com os botões de clonar, remover e mover do
 *   próprio construtor;
 * - há um seletor do setor, que escreve `data-sector` (o atributo de que o filtro da página
 *   depende);
 * - a grelha ganha um botão "Adicionar cartão", que duplica o último.
 *
 * Os seletores só apanham `.pg-cases`, por isso o resto dos websites não é afetado.
 */

export class CaseCardOption extends BaseOptionComponent {
    static template = "pg_website_cases_editor.CaseCardOption";
    static selector = ".pg-cases .case";
}

export class CasesGridOption extends BaseAddProductOption {
    static selector = ".pg-cases";
    productSelector = ".case";
    buttonLabel = _t("Adicionar cartão");
}

class CasesPlugin extends Plugin {
    static id = "pgCases";
    /** @type {import("plugins").WebsiteResources} */
    resources = {
        builder_options: [
            withSequence(BEGIN, CasesGridOption),
            withSequence(SNIPPET_SPECIFIC_END, CaseCardOption),
        ],
        dropzone_selector: {
            selector: ".pg-cases .case",
            dropNear: ".pg-cases .case",
        },
        is_movable_selector: { selector: ".pg-cases .case", direction: "horizontal" },
        // Impede que o Enter/Backspace dividam ou fundam o cartão (imagem + etiqueta).
        unsplittable_node_predicates: (node) =>
            isElement(node) && node.matches(".pg-cases .case"),
    };
}

registry.category("website-plugins").add(CasesPlugin.id, CasesPlugin);
