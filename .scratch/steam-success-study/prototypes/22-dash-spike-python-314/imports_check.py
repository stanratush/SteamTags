import sys, time, warnings, importlib, importlib.metadata
warnings.simplefilter("default")
t0 = time.perf_counter()
mods = ["dash", "dash_cytoscape", "dash_ag_grid", "diskcache", "multiprocess", "psutil",
        "networkx", "numpy", "scipy", "scipy.sparse", "scipy.stats", "igraph", "leidenalg", "flask", "plotly"]
for m in mods:
    t = time.perf_counter(); mod = importlib.import_module(m)
    print(f"{m:16s} {(getattr(mod, "__version__", "-") if m != "flask" else importlib.metadata.version("flask")):10s} {1000*(time.perf_counter()-t):7.0f} ms")
print(f"total import {1000*(time.perf_counter()-t0):.0f} ms on Python {sys.version.split()[0]}, GIL enabled={getattr(sys, '_is_gil_enabled', lambda: True)()}")
