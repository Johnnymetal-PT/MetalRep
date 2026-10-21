# -*- coding: utf-8 -*-
from odoo import api, models
import logging

_logger = logging.getLogger(__name__)

class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _trigger_specific_quality_check(self):
        """ Trigger a specific quality check by Control Point ID. """
        control_point_id = 3  # Replace with the specific Control Point ID
        qc_point = self.env['quality.point'].browse(control_point_id)

        if qc_point.exists():
            _logger.info(f"Triggering Quality Check for Control Point ID: {qc_point.id} on Picking ID: {self.id}")
            # Check if a quality check already exists for this control point and picking
            existing_qc = self.env['quality.check'].search([
                ('picking_id', '=', self.id),
                ('point_id', '=', qc_point.id),
            ])
            if not existing_qc:
                # Create the quality check
                self.env['quality.check'].create({
                    'picking_id': self.id,
                    'point_id': qc_point.id,
                    'team_id': 1,  # Replace with the correct Team ID
                    'product_id': False,  # Use specific product if needed
                })
                _logger.info(f"Quality Check created for Control Point ID: {qc_point.id} on Picking ID: {self.id}")
            else:
                _logger.info(f"Quality Check already exists for Control Point ID: {qc_point.id} on Picking ID: {self.id}")
        else:
            _logger.warning(f"Control Point ID {control_point_id} does not exist!")

    def write(self, vals):
        """ Override write method to trigger quality check when checkbox is checked. """
        if 'x_studio_com_defeito' in vals and vals['x_studio_com_defeito']:
            _logger.info(f"Checkbox 'x_studio_com_defeito' set to True for Picking ID: {self.id}")
            self._trigger_specific_quality_check()
        return super(StockPicking, self).write(vals)

