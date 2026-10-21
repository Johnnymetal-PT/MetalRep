import { Interaction } from '@web/public/interaction';
import { registry } from '@web/core/registry';

export class RangeFilter extends Interaction {
    static selector = '.js_attributes';
    dynamicContent = {
        'input[type="range"]': { 't-on-newRangeValue': this.onRangeSelected },
    };

    onRangeSelected(ev) {
        const range = ev.currentTarget;
        const url = new URL(window.location.href);
        const searchParams = url.searchParams;
        const existingRanges = searchParams.getAll('attrib_range');
        const newRangeValue = `${range.id},${range.valueLow},${range.valueHigh}`;

        searchParams.delete('attrib_range');

        let replaced = false;
        for (const r of existingRanges) {
            const [existingId] = r.split(',');
            if (existingId !== range.id.toString()) {
                searchParams.append('attrib_range', r);
            } else {
                // Replace the one that matches
                searchParams.append('attrib_range', newRangeValue);
                replaced = true;
            }
        }

        if (!replaced) {
            searchParams.append('attrib_range', newRangeValue);
        }

        redirect(`${url.pathname}?${searchParams.toString()}`);

//        window.location.href = `${url.pathname}?${searchParams.toString()}`;
    }
}

registry.category("public.interactions").add("theme_clarico_vega.RangeFilter", RangeFilter);