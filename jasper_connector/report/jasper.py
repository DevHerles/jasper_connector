# -*- coding: utf-8 -*-
##############################################################################
#
#    jasper_connector module for OpenERP,
#    Copyright (C) 2009-2011 SYLEAM Info Services (<http://www.syleam.fr/>)
#                  Christophe CHAUVET <christophe.chauvet@gmail.com>
#    Copyright (C) 2015 MIROUNGA (<http://www.mirounga.fr/>)
#              Christophe CHAUVET <christophe.chauvet@mirounga.fr>
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

from odoo.report.interface import report_int
from odoo import exceptions

from odoo.addons.jasper_connector.report.report_soap import Report
from odoo.addons.jasper_connector.report.report_exception import (
    JasperException)

import logging

_logger = logging.getLogger(__name__)


class report_jasper(report_int):  # noqa
    """
    Extend report_int to use Jasper Server
    """

    def create(self, cr, uid, ids, data, context=None):
        if context is None:
            context = {}
        if _logger.isEnabledFor(logging.DEBUG):
            _logger.debug('Call %s' % self.name)
        try:
            return Report(self.name, cr, uid, ids, data, context).execute()
        except JasperException, e:
            raise exceptions.UserError(e.message)


report_jasper('report.print.jasper.server')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
