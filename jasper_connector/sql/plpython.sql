--
-- Add some function
--
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
        res = odoo.execute(model, 'read', obj_id, [field])

    except AssertionError, e:
        plpy.error('Authentification error')
    except Exception, e:
        import traceback
        plpy.error(traceback.format_exc())
        raise

    return res[0][field]

$BODY$
LANGUAGE plpythonu;

ALTER FUNCTION get_field(text, integer, text, text, text, text, integer, text)
  OWNER TO %(db_user)s;

-- vim:ft=pgsql
