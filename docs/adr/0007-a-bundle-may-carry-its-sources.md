# An App Bundle may carry its sources and make Builds

An App Bundle is made in one of two kinds. By default it carries only its Builds, and the app opens them read-only, installing only the app's libraries (ADR 0001). Made `--with-sources`, it also carries each Build's source (a Snapshot's lightweight form, or an Import), `config/` and the two libraries a Build needs, `lxml` (the page parser, imported by the Build stage) and `markdown` (the report templates), so a researcher can duplicate a Build, change its settings and build it on their own computer. We chose this because Builds are cheap from the lightweight form (about 24 s), the `steamstudy` wheel already contains the Build code, and the two libraries are small, while the alternative, asking researchers for a repository and uv, is what the App Bundle exists to avoid. Each Build's read-only settings are shown in both kinds (Build menu, Settings…).

## Considered Options

- **Builds only, always.** Keeps ADR 0001's app-only install everywhere, but every settings question needs a new release from the maintainer.
- **Ship the whole pipeline group.** Simpler to describe, but pandas (unused by the Build) and `requests` (collection only; dash brings it anyway) add size and suggest the bundle can collect, which it never does.
- **Ship the raw Snapshot.** Builds take about 99 s instead of 24 s, and the raw pages are hundreds of MB.

## Consequences

- `bundle.json` records `kind` ("builds" or "sources") and the `sources` it ships; the zip's name ends in `-sources`. The app makes Builds wherever it finds `config/` and is not in a Builds-only bundle (`build_tree.is_bundle`).
- The app-only rule of ADR 0001 still holds for the app's own modules and for Builds-only bundles: `test_app_only` blocks every pipeline module and library. A Build must not need any pipeline library beyond `BUILD_LIBRARIES` (`bundle/make.py`): a test builds from a lightweight Snapshot with pandas blocked.
- A Snapshot needs a lightweight form of the current extract version to be shipped; the command refuses otherwise. Its lightweight form holds every collected game's tags, rank and players, so a bundle with sources is shared only where the Snapshot may be.
- Builds made in a bundle are written into the bundle's own `builds/` folder and become its `latest`, as in the repository.
