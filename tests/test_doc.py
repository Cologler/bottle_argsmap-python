# -*- coding: utf-8 -*-
#
# Copyright (c) 2021~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

import webtest
from bottle import Bottle

from bottle_argsmap import try_install

def test_simplest():
    app = Bottle()
    plugin = try_install(app)

    plugin.args.set_value('value', '1544')

    @app.get('/path')
    def get_it(value):
        return dict(value=value)

    tapp = webtest.TestApp(app)
    resp = tapp.get('/path')
    assert resp.status_code == 200
    assert resp.json == dict(value='1544')
