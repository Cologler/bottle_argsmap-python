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
        self._args = {}

    def __setitem__(self, k, v):
        self.set_value(k, v)

    def set_value(self, key, value):
        '''
        set a argument with value.
        '''
        return self.set_factory(key, lambda *_: value)

    def set_factory(self, key, factory, *, context_manager=False):
        '''
        set a argument with factory (`(key: str, route: bottle.Route) -> Any`).
        '''
        if not callable(factory):
            raise TypeError('factory must be callable')
        self._args[key] = (factory, context_manager)

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
        if not router: breakpoint()
        assert router is not None, 'can not find route'
        url_kwargs_names: Set[str] = {
            kvp[0] for kvp in router.builder[route.rule] if kvp[0]
        }

        req_kwargs_names = all_kwargs_names - url_kwargs_names

        if not req_kwargs_names:
            return callback

        @functools.wraps(callback)
        def wrapped_callback(*args, **kwargs):
            with self._get_args_resolve_context() as ctx:
                to_resolve = req_kwargs_names - set(kwargs)
                kwargs.update(
                    ctx.resolve(to_resolve, route)
                )
                return callback(*args, **kwargs)

        return wrapped_callback

    def _get_args_resolve_context(self):
        return _ArgsResolveContext(self._args)


class _ArgsResolveContext:
    __slots__ = ('_argsmap', '_es')

    def __init__(self, argsmap: dict) -> None:
        self._argsmap = argsmap
        self._es: contextlib.ExitStack = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._es:
            self._es.__exit__(exc_type, exc_val, exc_tb)

    def resolve(self, keys: Iterable[str], route: bottle.Route) -> Dict[str, Any]:
        get_argval = self.get_argval
        return {key: get_argval(key, route) for key in keys}

    def get_argval(self, key: str, route: bottle.Route) -> Any:
        factory, context_manager = self._argsmap[key]
        val = factory(key, route)
        if context_manager:
            if not self._es:
                self._es = contextlib.ExitStack()
            val = self._es.enter_context(val)
        return val


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
