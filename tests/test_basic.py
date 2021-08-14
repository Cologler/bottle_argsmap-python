# -*- coding: utf-8 -*-
#
# Copyright (c) 2021~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

import webtest
from bottle import Bottle

from bottle_argsmap import ArgsMapPlugin, try_install

def test_try_install_new():
    app = Bottle()
    plugin = try_install(app)
    assert isinstance(plugin, ArgsMapPlugin)
    assert app.plugins[-1] is plugin

def test_try_install_exists():
    app = Bottle()
    plugin = try_install(app)
    assert plugin is try_install(app)
    assert plugin is try_install(app)
    assert plugin is try_install(app)
    assert len([p for p in app.plugins if isinstance(p, ArgsMapPlugin)]) == 1

def test_without_inject():
    plugin = ArgsMapPlugin()
    app = Bottle()
    app.install(plugin)

    @app.get('/entires/<name>/<value>')
    def entires(name: str, value: str):
        return dict(name=name, value=value)

    tapp = webtest.TestApp(app)
    resp = tapp.get('/entires/test123/test4566')
    assert resp.status_code == 200
    assert resp.json == dict(name='test123', value='test4566')

def test_with_inject_value():
    plugin = ArgsMapPlugin()
    app = Bottle()
    app.install(plugin)

    plugin.set_value('value', '1544')

    @app.get('/entires/<name>')
    def entires(name: str, value: str):
        return dict(name=name, value=value)

    tapp = webtest.TestApp(app)
    resp = tapp.get('/entires/test123')
    assert resp.status_code == 200
    assert resp.json == dict(name='test123', value='1544')

def test_with_inject_factory():
    plugin = ArgsMapPlugin()
    app = Bottle()
    app.install(plugin)

    plugin.set_factory('value', lambda _1, _2: '1544')

    @app.get('/entires/<name>')
    def entires(name: str, value: str):
        return dict(name=name, value=value)

    tapp = webtest.TestApp(app)
    resp = tapp.get('/entires/test123')
    assert resp.status_code == 200
    assert resp.json == dict(name='test123', value='1544')

def test_with_inject_factory_with_close():
    class Closable:
        closed = False
        def close(self):
            self.closed = True

    plugin = ArgsMapPlugin()
    app = Bottle()
    app.install(plugin)

    obj = Closable()
    plugin.set_factory('value', lambda _1, _2: obj, auto_close=True)

    @app.get('/entires/<name>')
    def entires(name, value):
        assert value is obj
        assert not obj.closed
        return dict(name=name)

    tapp = webtest.TestApp(app)
    assert not obj.closed
    resp = tapp.get('/entires/test123')
    assert obj.closed
    assert resp.status_code == 200
    assert resp.json == dict(name='test123')

def test_with_inject_factory_with_exit():
    class Exitable:
        exited = False
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            self.exited = True

    plugin = ArgsMapPlugin()
    app = Bottle()
    app.install(plugin)

    obj = Exitable()
    plugin.set_factory('value', lambda _1, _2: obj, auto_exit=True)

    @app.get('/entires/<name>')
    def entires(name, value):
        assert value is obj
        assert not obj.exited
        return dict(name=name)

    tapp = webtest.TestApp(app)
    assert not obj.exited
    resp = tapp.get('/entires/test123')
    assert obj.exited
    assert resp.status_code == 200
    assert resp.json == dict(name='test123')
