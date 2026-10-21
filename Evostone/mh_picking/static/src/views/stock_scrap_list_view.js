/** @odoo-module **/

import { registry } from '@web/core/registry';
import { listView } from '@web/views/list/list_view';

export const stockScrapListView = {
    ...listView,
    props(genericProps, view, config, extension) {
        const props = listView.props(genericProps, view, config, extension);
        // Forçar allowSelectors = false sempre, mesmo ao agrupar/desagrupar
        props.allowSelectors = false;
        return props;
    },
};

registry.category('views').add('stock_scrap_list_no_check', stockScrapListView);
