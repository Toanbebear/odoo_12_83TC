# -*- coding: utf-8 -*-
# (c) 2015 AvanzOSC
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models, exceptions, api, _
import base64
import csv
# from io import BytesIO
import io
    # import StringIO
# import cStringIO


class ImportInventory(models.TransientModel):
    _name = 'import.inventory'
    _description = 'Import inventory'

    def _get_default_location(self):
        ctx = self.env.context
        if 'active_id' in ctx:
            inventory_obj = self.env['stock.inventory']
            inventory = inventory_obj.browse(ctx['active_id'])
            return inventory.location_id or self.env['stock.location']
        return False

    def _get_default_date(self):
        ctx = self.env.context
        if 'active_id' in ctx:
            inventory_obj = self.env['stock.inventory']
            inventory = inventory_obj.browse(ctx['active_id'])
            return inventory.date or fields.Datetime.now()
        return False

    data = fields.Binary('File', required=True)
    name = fields.Char('Filename')
    delimeter = fields.Char('Delimeter', default=',',
                            help='Default delimeter is ","')
    location = fields.Many2one('stock.location', 'Default Location',
                               default=_get_default_location, required=True)

    sci_date_done = fields.Datetime('Ngày hoàn thành', copy=False, help="Ngày ghi nhận hoàn thành SCI",
                                    default=_get_default_date, required=True)

    @api.multi
    def action_import(self):
        """Load Inventory data from the CSV file."""
        ctx = self.env.context
        stloc_obj = self.env['stock.location']
        inventory_obj = self.env['stock.inventory']
        inv_imporline_obj = self.env['stock.inventory.import.line']
        product_obj = self.env['product.product']
        inventory = inventory_obj
        if 'active_id' in ctx:
            inventory = inventory_obj.browse(ctx['active_id'])
        # Decode the file data
        data = base64.b64decode(self.data).decode('utf-8')
        print('import dataaaaaaaaaaaaaaaaa')
        file_input = io.StringIO(data)
        file_input.seek(0)
        location = self.location
        sci_date_done = self.sci_date_done
        reader_info = []
        if self.delimeter:
            delimeter = str(self.delimeter)
        else:
            delimeter = ','
        reader = csv.reader(file_input, delimiter=delimeter,
                            lineterminator='\r\n')
        try:
            reader_info.extend(reader)
        except Exception:
            raise exceptions.Warning(_("Not a valid file!"))
        keys = reader_info[0]
        # check if keys exist
        if not isinstance(keys, list) or ('code' not in keys or
                                          'quantity' not in keys):
            raise exceptions.Warning(
                _("Not 'code' or 'quantity' keys found"))
        del reader_info[0]
        values = {}
        inv_name = u'{} - {}'.format(self.name, sci_date_done.strftime('%d-%m-%Y'))
        inventory.write({'name': inv_name,
                         'date': sci_date_done,
                         'imported': True,
                         'state': 'confirm',
                         })
        lines = {
            ':'.join([
                l.code, l.lot and str(l.lot.id) or '',
                l.location_id and str(l.location_id.id) or '']): l
            for l in inventory.import_lines}
        for i in range(len(reader_info)):
            val = {}
            field = reader_info[i]
            values = dict(zip(keys, field))
            prod_location = location.id
            if 'location' in values and values['location']:
                locations = stloc_obj.search([('name', '=',
                                               values['location'])])
                if locations:
                    prod_location = locations[:1].id
            prod_lst = product_obj.search([
                '|',
                ('default_code', '=', values['code']),
                ('barcode', '=', values['code'])])
                # ('ean13', '=', values['code'])])
            if prod_lst:
                val['product'] = prod_lst[0].id
            if 'lot' in values and values['lot']:
                val['lot'] = values['lot']
            val['code'] = values['code']
            val['quantity'] = values['quantity']
            val['location_id'] = prod_location
            val['inventory_id'] = inventory.id
            val['fail'] = True
            val['fail_reason'] = _('No processed')
            if 'standard_price' in values and values['standard_price']:
                val['standard_price'] = values['standard_price']
            line_id = ':'.join([
                values['code'], values.get('lot', ''), str(prod_location)])
            if line_id in lines:
                lines[line_id].quantity += float(values['quantity'])
            else:
                lines[line_id] = inv_imporline_obj.create(val)


class StockInventoryImportLine(models.Model):
    _name = "stock.inventory.import.line"
    _description = "Stock Inventory Import Line"

    code = fields.Char('Product Code')
    product = fields.Many2one('product.product', 'Found Product')
    quantity = fields.Float('Quantity')
    inventory_id = fields.Many2one('stock.inventory', 'Inventory',
                                   readonly=True)
    location_id = fields.Many2one('stock.location', 'Location')
    lot = fields.Char('Product Lot')
    fail = fields.Boolean('Fail')
    fail_reason = fields.Char('Fail Reason')
    standard_price = fields.Float(string='Cost Price')
