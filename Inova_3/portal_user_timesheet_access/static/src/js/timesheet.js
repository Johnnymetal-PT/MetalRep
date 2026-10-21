/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import { rpc } from "@web/core/network/rpc";

publicWidget.registry.TimesheetForm = publicWidget.Widget.extend({
    selector: '.oe_portal_timesheet_form',
    events: {
        'change #project_id': '_onProjectId',
    },
    /*privatemethod for set task based on project id*/
    _onProjectId: function () {
        var selecttasks = $("select[name='task_id']");
        selecttasks.html('');
        if (!$("#project_id").val()) {
            return;
        } else{
            rpc("/timesheet/project_infos/", {'project_id': $("#project_id").val()}).then(function (data) {
                if (selecttasks.data('init')===0 || selecttasks.find('option').length===0) {
                    if (data.length) {
                        data.forEach(x => {
                            var opt = $('<option>').text(x.name)
                                .attr('value', x.id)
                                .attr('data-code', x.name);
                            selecttasks.append(opt);
                        });
                        selecttasks.parent('div').show();
                    } else {
                        var opt = $('<option>').text('')
                            .attr('value', '')
                            .attr('data-code', '');
                        selecttasks.append(opt);
                        selecttasks.parent('div').show();
                    }
                    selecttasks.data('init', 0);
                } else {
                    selecttasks.data('init', 0);
                }
            });
        }
    },

});
return publicWidget.registry.TimesheetForm;

