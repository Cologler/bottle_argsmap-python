# -*- coding: utf-8 -*-
#
# Copyright (c) 2021~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

from typing import *
import inspect
import functools
import contextlib

import bottle
import anyioc

def _find_router(route: bottle.Route) -> bottle.Router:
    'find the router which contains the route.'

    def ifind_router(router: bottle.Router):
        # static route map by METHOD, than map by rule
        if router.static.get(route.method, {}).get(route.rule, (None, None))[0] is route:
            return router

        # dynamic route map by method, than a list
        for route_info in router.dyna_routes.get(route.method, ()):
            if (route, route.rule) == (route_info[2], route_info[0]):
                return router

    return ifind_router(route.app.router)


class ArgsMapPlugin:
    api = 2

    def __init__(self, name: str = 'argsmap') -> None:
        self.name = name
        self.ioc = anyioc.ServiceProvider()

    def __setitem__(self, k, v):
        self.set_value(k, v)

    def set_value(self, key, value):
        '''
        set a argument with value.
        '''
        self.ioc.register_value(key, value)

    def set_factory(self, key, factory, *, context_manager=False):
        '''
        set a argument with factory (`(key: str, route: bottle.Route) -> Any`).
        '''
        if not callable(factory):
            raise TypeError('factory must be callable')
        def factory_wrapper(ioc: anyioc.ServiceProvider):
            route: bottle.Route = ioc[bottle.Route]
            val = factory(key, route)
            if context_manager:
                val = ioc.enter(val)
            return val
        self.ioc.register_scoped(key, factory_wrapper)

    def setup(self, app: bottle.Bottle) -> None:
        pass

    def close(self) -> None:
        pass

    def apply(self, callback, route: bottle.Route):
        params = inspect.signature(route.callback).parameters # use original callback
        all_kwargs_names: Set[str] = {
            k for k, v in params.items() if v.kind in (
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
                inspect.Parameter.KEYWORD_ONLY
            )
        }

        router = _find_router(route)
        if not router:
            breakpoint()
            raise NotImplementedError('no router found')

        url_kwargs_names: Set[str] = {
            kvp[0] for kvp in router.builder[route.rule] if kvp[0]
        }

        req_kwargs_names = all_kwargs_names - url_kwargs_names

        if not req_kwargs_names:
            return callback

        @functools.wraps(callback)
        def wrapped_callback(*args, **kwargs):
            with self.ioc.scope() as scoped:
                scoped.register_value(bottle.Route, route)
                to_resolve = req_kwargs_names - set(kwargs)
                kwargs.update(
                    {key: scoped[key] for key in to_resolve}
                )
                return callback(*args, **kwargs)

        return wrapped_callback


def try_install(app: bottle.Bottle) -> ArgsMapPlugin:
    '''
    append a `ArgsMapPlugin` to the plugins list, or get the exists one.
    '''
    if p := [p for p in app.plugins if isinstance(p, ArgsMapPlugin)]:
        return p[-1]
    new_plugin = ArgsMapPlugin()
    app.install(new_plugin)
    return new_plugin


__all__ = [
    'try_install',
    'ArgsMapPlugin'
]
