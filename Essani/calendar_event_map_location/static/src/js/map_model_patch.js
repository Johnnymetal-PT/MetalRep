/** @odoo-module **/

import { MapModel } from "@web_map/map_view/map_model";
import { patch } from "@web/core/utils/patch";

const superSetup = MapModel.prototype.setup;
const superGetRecordSpecification = MapModel.prototype._getRecordSpecification;
const superAddPartnerToRecord = MapModel.prototype._addPartnerToRecord;
const superWriteCoordinatesUsers = MapModel.prototype._writeCoordinatesUsers;

function isCalendarEvent(metaData) {
    return metaData.resModel === "calendar.event";
}

function getCalendarLocation(record) {
    return (record.location || "").trim();
}

function ensureCalendarLocationField(fieldNames) {
    if (Array.isArray(fieldNames) && !fieldNames.includes("location")) {
        fieldNames.push("location");
    }
}

patch(MapModel.prototype, "calendar_event_map_location", {
    setup(params, services) {
        if (params?.resModel === "calendar.event" && params?.fieldNames) {
            ensureCalendarLocationField(params.fieldNames);
        }
        superSetup.call(this, params, services);
    },

    _getRecordSpecification(metaData, data) {
        const specification = superGetRecordSpecification.call(this, metaData, data);
        if (isCalendarEvent(metaData)) {
            ensureCalendarLocationField(metaData.fieldNames);
            if (!specification.location) {
                specification.location = {};
            }
        }
        return specification;
    },

    _addPartnerToRecord(metaData, data) {
        if (!isCalendarEvent(metaData)) {
            return superAddPartnerToRecord.call(this, metaData, data);
        }
        let locatedCount = 0;
        for (const record of data.records) {
            let partner;
            if (metaData.resModel === "res.partner" && metaData.resPartnerField === "id") {
                partner = data.partners[record.id];
            } else {
                const relation = record[metaData.resPartnerField];
                if (relation) {
                    partner = data.partners[relation.id];
                }
            }
            const location = getCalendarLocation(record);
            if (location) {
                const pseudoId = `calendar_event_location_${record.id}`;
                let locationPartner = data.partners[pseudoId];
                if (!locationPartner) {
                    locationPartner = {
                        id: pseudoId,
                        display_name: location,
                        contact_address_complete: location,
                        partner_latitude: undefined,
                        partner_longitude: undefined,
                    };
                    data.partners[pseudoId] = locationPartner;
                } else {
                    locationPartner.partner_latitude = undefined;
                    locationPartner.partner_longitude = undefined;
                }
                record.partner = locationPartner;
            } else {
                record.partner = partner;
            }
            if (record.partner) {
                locatedCount++;
            }
        }
        data.numberOfLocatedRecords = locatedCount;
    },

    async _writeCoordinatesUsers(metaData, data) {
        if (!isCalendarEvent(metaData)) {
            return superWriteCoordinatesUsers.call(this, metaData, data);
        }
        if (data.partnerToCache.length) {
            data.partnerToCache = data.partnerToCache.filter(
                (partner) => typeof partner.id === "number"
            );
        }
        if (!data.partnerToCache.length) {
            data.partnerToCache = [];
            return;
        }
        await superWriteCoordinatesUsers.call(this, metaData, data);
    },
});
