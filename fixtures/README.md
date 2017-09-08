`boxes.json` is not actually a Django fixture file. It's mainly used by
the `initial_data` function in `boxes/factories.py`. 
 
We still use `sitetree_menus.json` fixture because it's hard to create
its data via `factory_boy` or programmatically by using its API.
