# -*- coding: utf-8 -*-
##############################################################################
#
#    jasper_connector module for OpenERP
#    Copyright (c) 2008-2009 EVERLIBRE (http://everlibre.fr) Eric VERNICHON
#    Copyright (C) 2009-2011 SYLEAM ([http://www.syleam.fr]) Christophe CHAUVET
#    Copyright (C) 2015-2016 MIROUNGA (<http://www.mirounga.fr/>)
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
#    along with this program.  If not, see [http://www.gnu.org/licenses/].
#
##############################################################################

from . import models  # noqa
from . import report  # noqa
from . import wizard  # noqa


def create_function_get_field(cr):
    cr.execute('''
CREATE OR REPLACE FUNCTION get_field(
    server   text,
    port     integer,
    login    text,
    password text,
    database text,
    model    text,
    obj_id   integer,
    field    text)
RETURNS text AS
$BODY$

if obj_id is None:
    return '0'
else :
    import odoorpc

    res = {}
    try:
        odoo = odoorpc.ODOO(server, port=port)
        odoo.login(database, login, password)
        res = odoo.execute(model, 'read', [obj_id], [field])

    except AssertionError, e:
        plpy.error('Authentification error')
    except Exception, e:
        import traceback
        plpy.error(traceback.format_exc())
        raise

    return res[0][field]

$BODY$
LANGUAGE plpythonu;
    ''')
