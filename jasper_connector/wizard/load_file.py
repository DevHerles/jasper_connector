# -*- coding: utf-8 -*-
##############################################################################
#
#    jasper_connector module for OpenERP,
#    Copyright (C) 2014-2016 Mirounga (<http://www.mirounga.fr/>)
#                   Christophe CHAUVET <christophe.chauvet@gmail.com>
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

from odoo import models, fields, api
import base64


class LoadFile(models.TransientModel):
    _name = 'load.jrxml.file'
    _description = 'Load file in the jasperdocument'

    datafile = fields.Binary('File', required=True,
                             help='Select file to transfert')

    @api.multi
    def import_file(self):
        self.ensure_one()
        content = base64.decodestring(self.datafile)
        docs = self.env['jasper.document'].\
            browse(self.env.context['active_ids'])
        docs.parse_jrxml(content)

        return True

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
