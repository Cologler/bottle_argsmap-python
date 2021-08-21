# bottle_argsmap

Auto inject arguments via a `dict` like pattern.

## Usage

``` py
from bottle import Bottle
from bottle_argsmap import ArgsMapPlugin

app = Bottle()
plugin = try_install(app)

# inject via singleton
plugin.set_value('value', '1544')

# or inject via factory, dynamic creation is allowed
# e.g. you can to inject database connection from a database pool
plugin.set_factory('value',
    lambda param_name, route: ...,
    auto_close=True,        # auto call `close()`  on the value after responsed
    context_manager=True,         # auto call `__exit__` on the value after responsed
)

# finally, inject it
@app.get('/path')
def get_it(value): # value is injected
    return dict(value=value)
```

## More

`ArgsMapPlugin().ioc` is a instance of type `anyioc.ServiceProvider`, which means you can use all features from `anyioc`.
