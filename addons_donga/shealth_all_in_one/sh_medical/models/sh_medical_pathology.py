##############################################################################
#    Copyright (C) 2018 shealth (<http://scigroup.com.vn/>). All Rights Reserved
#    shealth, Hospital Management Solutions

# Odoo Proprietary License v1.0
#
# This software and associated files (the "Software") may only be used (executed,
# modified, executed after modifications) if you have purchased a valid license
# from the authors, typically via Odoo Apps, shealth.in, openerpestore.com, or if you have received a written
# agreement from the authors of the Software.
#
# You may develop Odoo modules that use the Software as a library (typically
# by depending on it, importing it and using its resources), but without copying
# any source code or material from the Software. You may distribute those
# modules under the license of your choice, provided that this license is
# compatible with the terms of the Odoo Proprietary License (For example:
# LGPL, MIT, or proprietary licenses similar to this one).
#
# It is forbidden to publish, distribute, sublicense, or sell copies of the Software
# or modified copies of the Software.
#
# The above copyright notice and this permission notice must be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

##############################################################################

from odoo import api, SUPERUSER_ID, fields, models, _
from odoo.osv import expression


class SHealthPathologyCategory(models.Model):
    _description='Disease Categories'
    _name = 'sh.medical.pathology.category'

    name = fields.Char(string='Category Name', required=True, translate=True, size=128)
    parent_id = fields.Many2one('sh.medical.pathology.category', string='Parent Category', index=True)
    child_ids = fields.One2many('sh.medical.pathology.category', 'parent_id', string='Children Category')
    active = fields.Boolean(string='Active', default=lambda *a: 1)

    _order = 'parent_id,id'


class SHealthPathology(models.Model):
    _name = "sh.medical.pathology"
    _description = "Diseases"

    name = fields.Char(string='Disease Name', size=128, help="Disease name", translate=True, required=True)
    code = fields.Char(string='Code', size=32, help="Specific Code for the Disease (eg, ICD-10, SNOMED...)")
    category = fields.Many2one('sh.medical.pathology.category', string='Disease Category')
    chromosome = fields.Char(string='Affected Chromosome', size=128, help="chromosome number")
    protein = fields.Char(string='Protein involved', size=128, help="Name of the protein(s) affected")
    gene = fields.Char(string='Gene', size=128, help="Name of the gene(s) affected")
    info = fields.Text(string='Extra Info')
    index_pathology = fields.Integer(string='STT mã bệnh', help="STT mã bệnh trong báo cáo icd10", size=3)

    diagnose = fields.Char(string="Chẩn đoán", help="Chẩn đoán tình trạng bệnh nhân")

    _sql_constraints = [
        ('code_uniq', 'unique (code)', 'The disease code must be unique')]

    @api.multi
    def name_get(self):
        res = []
        for category in self:
            res.append((category.id, _('[%s] %s') % (category.code, category.name[0:50])))
        return res

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('name', operator, name), ('code', operator, name)]
        pathology = self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)
        return self.browse(pathology).name_get()