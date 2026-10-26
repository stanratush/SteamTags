# Shipping Parameter Selection results in an App Bundle
Type: grilling
Status: open
Blocked by: none

## Question

Should `steamstudy bundle` carry precomputed Parameter Selection results, so a researcher opens finished grids and validations offline without a ~3-minute run? If so, how is a cache made on one machine trusted on another?

- Today `bundle/make.py` copies each Build folder **without** `app_cache/`, so nothing cached travels. [Modules, caching and parallelism](08-modules-caching-parallelism.md) fixed the cache layout: `app_cache/parameter_selection/grids/<grid_key_hash>/` and `validation/<validation_key_hash>.json`, keyed by settings and method versions, not by library versions.
- Which results to ship: none, only the default-settings grids and validations, or whatever the maker's cache holds? Is a missing cache produced at bundle time (a new `bundle` option that runs the job) or only copied?
- Trust across machines: `leidenalg==0.12.0` and `python-igraph==1.0.0` are pinned, but numpy and Python vary across the bundle targets (3.12–3.14, ADR 0001). Do library versions go into the keys, get recorded in the manifest and checked on load, or is the result accepted as it is? What does the mode show for a shipped result it can't reproduce locally?
- How "Clear app cache" treats shipped results, and whether the checklist in `docs/releasing-an-app-bundle.md` gains a step.
