# -*- coding: utf-8 -*-
##############################################################################
#
#    jasper_connector module for OpenERP,
#    Copyright (C) 2010-2011 SYLEAM Info Services (<http://www.Syleam.fr/>)
#                            Damien CRIER
#    Copyright (C) 2015 MIROUNGA (<http://www.mirounga.fr/>)
#              Christophe CHAUVET <christophe.chauvet@gmail.com>
#
#    This file is a part of jasper_connector
#
#    jasper_connector is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    jasper_connector is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import models, fields, tools, _, exceptions, api
from odoo.addons.jasper_connector.common import (
    registered_report, KNOWN_PARAMETERS)
from StringIO import StringIO
from lxml import etree
import base64
from odoo.addons.jasper_connector import jasperlib
import logging

_logger = logging.getLogger(__name__)

JRXML_NS = {
    'root': 'http://jasperreports.sourceforge.net/jasperreports',
}


class JasperDocumentExtension(models.Model):
    _name = 'jasper.document.extension'
    _description = 'Jasper Document Extension'

    name = fields.Char('Name', size=128, translate=True)
    jasper_code = fields.Char('Code', size=32, required=True)
    extension = fields.Char('Extension', size=10, required=True)


class JasperDocument(models.Model):
    _name = 'jasper.document'
    _description = 'Jasper Document'
    _order = 'sequence'

    @api.model
    def _get_formats(self):
        """
        Return the list of all types of document that can be
        generate by JasperServer
        """
        extension_obj = self.env['jasper.document.extension']
        extensions = extension_obj.search([])
        ext = [(extension.jasper_code,
                extension.name + " (*." + extension.extension + ")")
               for extension in extensions]
        return ext

    name = fields.Char('Name', size=128, translate=True, required=True,
                       placeholder="InvoiceJ")  # button name
    enabled = fields.Boolean('Active', default=True,
                             help="Indicates if this document is active or not")  # noqa
    model_id = fields.Many2one('ir.model', 'Object Model', required=True)
    server_id = fields.Many2one('jasper.server', 'Server',
                                help='Select specific JasperServer')
    jasper_file = fields.Char('Jasper file', size=128)  # jasper filename
    group_ids = fields.Many2many('res.groups', 'jasper_wizard_group_rel',
                                 'document_id', 'group_id', 'Groups')
    depth = fields.Integer('Depth', required=True)
    format_choice = fields.Selection([('mono', 'Single Format'),
                                      ('multi', 'Multi Format')],
                                     'Format Choice', required=True,
                                     default='mono')
    format = fields.Selection(_get_formats, 'Formats', default='PDF')
    report_unit = fields.Char('Report Unit', size=128,
                              help='Enter the name for report unit in Jasper Server')  # noqa
    mode = fields.Selection([('sql', 'SQL'), ('xml', 'XML'),
                             ('multi', 'Multiple Report')], 'Mode',
                            required=True, default='sql')
    before = fields.Text('Before',
                         help='This field must be filled with a valid SQL request and will be executed BEFORE the report edition',)  # noqa
    after = fields.Text('After',
                        help='This field must be filled with a valid SQL request and will be executed AFTER the report edition',)  # noqa
    attachment = fields.Char('Save As Attachment Prefix', size=255,
                             help='This is the filename of the attachment used to store the printing result. Keep empty to not save the printed reports. You can use a python expression with the object and time variables.')  # noqa
    attachment_use = fields.Boolean('Reload from Attachment',
                                    help='If you check this, then the second time the user prints with same attachment name, it returns the previous report.')  # noqa
    param_ids = fields.One2many('jasper.document.parameter',
                                'document_id', 'Parameters')
    ctx = fields.Char('Context', size=128,
                      help="Enter condition with context does match to see the print action\neg: context.get('foo') == 'bar'")  # noqa
    sql_view = fields.Text('SQL View',
                           help='Insert your SQL view, if the report is base on it')  # noqa
    sql_name = fields.Char('Name of view', size=128)
    child_ids = fields.Many2many('jasper.document',
                                 'jasper_document_multi_rel',
                                 'source_id',
                                 'destin_id',
                                 'Child report',
                                 help='Select reports to launch when this report is called')  # noqa
    sequence = fields.Integer('Sequence', default=100,
                              help='The sequence is used when launch a multple report, to select the order to launch')  # noqa
    only_one = fields.Boolean('Launch one time for all ids',
                              help='Launch the report only one time on multiple id')  # noqa
    duplicate = fields.Char('Duplicate', size=256, default='1',
                            help="Indicate the number of duplicate copie, use o as object to evaluate\neg: o.partner_id.copy\nor\n'1'", )  # noqa
    lang = fields.Char('Lang', size=256,
                       help="Indicate the lang to use for this report, use o as object to evaluate\neg: o.partner_id.lang\n ctx as context\neg: ctx.get('test')\n or\n'fr_FR'\ndefault use user's lang")  # noqa
    report_id = fields.Many2one('ir.actions.report.xml', 'Report link',
                                readonly=True, help='Link to the report in ir.actions.report.xml')  # noqa
    check_sel = fields.Selection([('none', 'None'),
                                  ('simple', 'Simple'),
                                  ('func', 'Function')],
                                 'Checking type', default='none',
                                 help='if None, no check\nif Simple, define on Check Simple the condition\n if function, the object have check_print function')  # noqa
    check_simple = fields.Char('Check Simple', size=256,
                               help="This code inside this field must return True to send report execution\neg o.state in ('draft', 'open')")  # noqa
    message_simple = fields.Char('Return message', size=256,
                                 translate=True,
                                 help="Error message when check simple doesn't valid")  # noqa
    label_ids = fields.One2many('jasper.document.label', 'document_id',
                                'Labels')
    pdf_begin = fields.Char('PDF at begin', size=128,
                            help='Name of the PDF file store as attachment to add at the first page (page number not recompute)')  # noqa
    pdf_ended = fields.Char('PDF at end', size=128,
                            help='Name of the PDF file store as attachment to add at the last page (page number not recompute)')  # noqa

    @api.multi
    def make_action(self):
        """
        Create an entry in ir_actions_report_xml
        and ir.values
        """
        self.ensure_one()
        act_report_obj = self.env['ir.actions.report.xml']

        doc = self
        if doc.report_id:
            _logger.info('Update "%s" service' % doc.name)
            args = {
                'name': doc.name,
                'report_name': 'jasper.report_%d' % (doc.id,),
                'model': doc.model_id.model,
                'groups_id': [(6, 0, [x.id for x in doc.group_ids])],
                'header': False,
                'multi': False,
            }
            doc.report_id.write(args)
        else:
            _logger.info('Create "%s" service' % doc.name)
            args = {
                'name': doc.name,
                'report_name': 'jasper.report_%d' % (doc.id,),
                'model': doc.model_id.model,
                'report_type': 'jasper',
                'groups_id': [(6, 0, [x.id for x in doc.group_ids])],
                'header': False,
                'multi': False,
            }
            report = act_report_obj.create(args)
            self._cr.execute("""UPDATE jasper_document SET report_id=%s
                             WHERE id=%s""", (report.id, self.id))
            value = 'ir.actions.report.xml,' + str(report.id)
            self.env['ir.values'].sudo().\
                set_action(doc.name, action_slot='client_print_multi',
                           model=doc.model_id.model, action=value,
                           res_id=False)
        registered_report('jasper.report_%d' % (doc.id,))

    @api.model
    def action_values(self, report_id):
        """
        Search ids for reports
        """
        args = [
            ('key', '=', 'action'),
            ('key2', '=', 'client_print_multi'),
            ('value', '=', 'ir.actions.report.xml,%d' % report_id),
            # ('object', '=', True),
        ]
        return self.env['ir.values'].search(args)

    @api.model
    def get_action_report(self, module, name, datas=None):
        """
        Give the XML ID dans retrieve the report action

        :param module: name fo the module where the XMLID is reference
        :type module: str
        :param name: name of the XMLID (afte rthe dot)
        :type name: str
        :return: return an ir.actions.report.xml
        :rtype: dict
        """
        if datas is None:
            datas = {}

        result = self.env.ref(module + u"." + name)
        service = 'jasper.report_%d' % (result.id,)
        _logger.debug('get_action_report -> ' + service)

        return {
            'type': 'ir.actions.report.xml',
            'report_name': service,
            'datas': datas,
            'context': self.env.context,
        }

    @api.multi
    def create_values(self):
        self.ensure_one()
        doc = self
        if not self.action_values(doc.report_id.id):
            value = 'ir.actions.report.xml,%d' % doc.report_id.id
            _logger.debug('create_values -> ' + value)
            self.env['ir.values'].\
                set_action(doc.name, action_slot='client_print_multi',
                           model=doc.model_id.model, action=value,
                           res_id=False)
        return True

    @api.multi
    def unlink_values(self):
        """
        Only remove link in ir.values, not the report
        """
        self.ensure_one()
        self.action_values(self.report_id.id).unlink()
        _logger.debug('unlink_values')
        return True

    @api.model
    def create(self, vals):
        """
        Dynamicaly declare the wizard for this document
        """
        doc = super(JasperDocument, self).create(vals)
        doc.make_action()

        # Check if view and create it in the database
        if vals.get('sql_name') and vals.get('sql_view'):
            tools.drop_view_if_exists(self._cr, vals.get('sql_name'))
            sql_query = 'CREATE OR REPLACE VIEW %s AS\n%s' % (vals['sql_name'],
                                                              vals['sql_view'])
            self._cr.execute(sql_query)
        return doc

    @api.multi
    def write(self, vals):
        """
        If the description change, we must update the action
        """
        self.ensure_one()
        if vals.get('sql_name') or vals.get('sql_view'):
            sql_name = vals.get('sql_name', self.sql_name)
            sql_view = vals.get('sql_view', self.sql_view)
            tools.drop_view_if_exists(self._cr, sql_name)
            sql_query = 'CREATE OR REPLACE VIEW %s AS\n%s' % (sql_name,
                                                              sql_view)
            self._cr.execute(sql_query, (self.ids,))

        res = super(JasperDocument, self).write(vals)

        if not self.env.context.get('action'):
            self.make_action()

            if 'enabled' in vals:
                if vals['enabled']:
                    self.create_values()
                else:
                    self.unlink_values()
        return res

    @api.multi
    def copy(self, default=None):
        """
        When we duplicate code, we must remove some field, before
        """
        self.ensure_one()
        default = dict(default or {})

        default['report_id'] = False
        default['name'] = self.name + _(' (copy)')
        return super(JasperDocument, self).copy(default)

    @api.multi
    def unlink(self):
        """
        When remove jasper_document, we must remove data to
        ir.actions.report.xml and ir.values
        """
        for doc in self:
            if doc.report_id:
                doc.unlink_values()
                doc.report_id.unlink()

        return super(JasperDocument, self).unlink()

    @api.multi
    def check_report(self):
        # TODO, use jasperlib to check if report exists
        self.ensure_one()
        curr = self
        js_server = self.env['jasper.server']
        if curr.server_id:
            jss = curr.server_id
        else:
            js_servers = js_server.search([('enable', '=', True)])
            if not js_servers:
                raise exceptions.\
                    UserError(_('No JasperServer configuration found !'))

            jss = js_servers[0]

        def compose_path(basename):
            return jss['prefix'] and \
                '/' + jss['prefix'] + '/instances/%s/%s' or basename

        try:
            js = jasperlib.Jasper(jss.host, jss.port, jss.user, jss['passwd'])
            js.auth()
            uri = compose_path('/openerp/bases/%s/%s') % (self._cr.dbname,
                                                          curr.report_unit)
            envelop = js.run_report(uri=uri, output='PDF', params={})
            js.send(jasperlib.SoapEnv('runReport', envelop).output())
        except jasperlib.ServerNotFound:
            raise exceptions.\
                UserError(_('Error, server not found %s %d')
                          % (js.host, js.port))
        except jasperlib.AuthError:
            raise exceptions.\
                UserError(_('Error, Authentification failed for %s/%s')
                          % (js.user, js.pwd))
        except jasperlib.ServerError, e:
            raise exceptions.UserError(e)

        return True

    @api.multi
    def parse_jrxml(self, content):
        """
        Parse JRXML file to retrieve I18N parameters and OERP parameters
        are not standard
        """
        self.ensure_one()
        label_obj = self.env['jasper.document.label']
        param_obj = self.env['jasper.document.parameter']
        att_obj = self.env['ir.attachment']

        fp = StringIO(content)
        tree = etree.parse(fp)
        param = tree.xpath('//root:parameter/@name', namespaces=JRXML_NS)
        for label in param:
            val = tree.xpath('//root:parameter[@name="' + label + '"]//root:defaultValueExpression', namespaces=JRXML_NS)[0].text  # noqa
            _logger.debug('%s -> %s' % (label, val))

            if label.startswith('I18N_'):
                lab = label.replace('I18N_', '')
                labels = label_obj.search([('name', '=', lab)])
                if labels:
                    continue
                label_obj.\
                    create({'document_id': self.id,
                            'name': lab,
                            'value': val.replace('"', '')})
            if label.startswith('OERP_') and label not in KNOWN_PARAMETERS:
                lab = label.replace('OERP_', '')
                param_ids = param_obj.search([('name', '=', lab)])
                if param_ids:
                    continue
                param_obj.create({'document_id': self.id,
                                  'name': lab,
                                  'code': val.replace('"', ''),
                                  'enabled': True})

        # Now we save JRXML as attachment
        # We retrieve the name of the report with the attribute name from the
        # jasperReport element
        filename = '%s.jrxml' % tree.xpath('//root:jasperReport/@name',
                                           namespaces=JRXML_NS)[0]

        att_ids = att_obj.search([('name', '=', filename),
                                  ('res_model', '=', 'jasper.document'),
                                  ('res_id', '=', self.id)])
        if att_ids:
            att_ids.unlink()

        ctx = self.env.context.copy()
        ctx['type'] = 'binary'
        ctx['default_type'] = 'binary'
        att_obj.with_context(ctx).\
            create({'name': filename,
                    'datas': base64.encodestring(content),
                    'datas_fname': filename,
                    'file_type': 'text/xml',
                    'res_model': 'jasper.document',
                    'res_id': self.id})

        fp.close()
        return True


class JasperDocumentParameter(models.Model):
    _name = 'jasper.document.parameter'
    _description = 'Add parameter to send to jasper server'

    name = fields.Char('Name', size=32,
                       help='Name of the jasper parameter, the prefix must be OERP_', required=True)  # noqa
    code = fields.Char('Code', size=256, help='Enter the code to retrieve data', required=True)  # noqa
    enabled = fields.Boolean('Enabled', default=True)
    document_id = fields.Many2one('jasper.document', 'Document',
                                  required=True)


class JasperDocumentLabel(models.Model):
    _name = 'jasper.document.label'
    _description = 'Manage label in document, for different language'

    name = fields.Char('Parameter', size=64, required=True,
                       help='Name of the parameter send to JasperServer, prefix with I18N_\neg: test become I18N_TEST as parameter')  # noqa
    value = fields.Char('Value', size=256, required=True, translate=True,
                        help='Name of the label, this field must be translate in all languages available in the database')  # noqa
    document_id = fields.Many2one('jasper.document', 'Document',
                                  required=True)


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
