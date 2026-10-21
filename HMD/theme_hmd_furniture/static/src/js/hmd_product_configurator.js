/** @odoo-module **/

import { WebsiteSale } from "@website_sale/js/website_sale";

/**
 * Deixar escolher o acabamento do produto principal dentro do modal
 * "Configure your product".
 *
 * O que se passava
 * ----------------
 * No modal, cada produto de "Available options" mostra o seu seletor de
 * Finish, mas o produto principal aparecia so com o nome do acabamento ja
 * escolhido ("211 CLOSED MODULE (Natural Oak Veneer)") e sem forma de o
 * trocar. A HMD quer que o principal se comporte como os opcionais.
 *
 * Isto nao e um bug: e uma decisao do Odoo. Em
 * website_sale/static/src/js/website_sale_configurators.js o modal e aberto
 * com
 *
 *     options: { isMainProductConfigurable: !isOnProductPage, ... }
 *
 * e `isOnProductPage` vem de website_sale.js (~l.444), que testa se o
 * formulario de "Add to cart" esta dentro de `.o_wsale_product_page`. O
 * raciocinio do Odoo e que quem carrega em "Add to cart" na propria pagina do
 * produto ja escolheu ali a variante, e nao vale a pena repetir a pergunta.
 *
 * Essa bandeira e depois lida no t-if que o website_sale poe na linha de
 * atributo (product_template_attribute_line.xml):
 *
 *     this.env.isMainProductConfigurable
 *         || this.env.mainProductTmplId !== this.props.productTmplId
 *
 * — que e exatamente a razao de os opcionais mostrarem o Finish e o principal
 * nao: para os opcionais, a segunda metade da condicao e verdadeira.
 *
 * O que se faz
 * ------------
 * Forca-se `isOnProductPage` a false so na chamada que abre o modal, o que
 * equivale a `isMainProductConfigurable: true`. E o mesmo estado em que o
 * modal ja abre hoje quando se adiciona ao carrinho a partir da grelha da
 * Collection, por isso nao estamos a inventar um comportamento novo: estamos a
 * usar o que o Odoo ja faz no outro caminho.
 *
 * Porque nao mexer no `_onProductReady`, que recebe a mesma bandeira
 * -----------------------------------------------------------------
 * Porque ela serve la outra coisa. Em `_openDialog` o mesmo valor viaja como
 * `is_product_configured` para /website_sale/should_show_product_configurator,
 * que decide SE o modal chega a abrir: com `is_product_configured` a false, o
 * modal passaria a abrir tambem em produtos sem opcionais nenhuns, que nao e o
 * que a HMD pediu. Mexemos so no ponto de decisao certo.
 */
WebsiteSale.include({
    _openProductConfigurator(isOnProductPage, showQuantity) {
        return this._super(false, showQuantity);
    },
});
