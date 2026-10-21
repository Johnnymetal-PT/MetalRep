/** @odoo-module **/
import { registry } from "@web/core/registry";

// The options class name & path can differ slightly by build.
// Look for something like "website.s_dynamic_snippet_options" or
// "@website/snippets/s_dynamic/options" and its "NumberOfRecords" control.
const { options } = await import("@website/snippets/s_dynamic/options");

if (options?.DynamicSnippetNumberOfRecords) {
    const proto = options.DynamicSnippetNumberOfRecords.prototype;
    // Common properties used by the slider widget:
    // MAX (or max) is often 16 by default.
    proto.MAX = 64;          // raise upper bound
    proto.step = 1;          // keep default step
}
// In some builds it’s options.DynamicSnippetRegistry.XYZ; adapt accordingly.

