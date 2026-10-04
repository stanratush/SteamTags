import warnings
warnings.filterwarnings("error", category=DeprecationWarning)
warnings.filterwarnings("error", category=PendingDeprecationWarning)
warnings.filterwarnings("error", category=FutureWarning)
import app
c = app.app.server.test_client()
for path in ["/", "/_dash-layout", "/_dash-dependencies"]:
    r = c.get(path); print(path, r.status_code, len(r.data))
def post(output, outputs, inputs, changed, state=None):
    body = {"output": output, "outputs": outputs, "inputs": inputs, "changedPropIds": changed, "state": state or []}
    r = c.post("/_dash-update-component", json=body); return r.status_code, len(r.data)
print("update_graph", post("..cy.elements...stats.children..",
    [{"id": "cy", "property": "elements"}, {"id": "stats", "property": "children"}],
    [{"id": "min-games", "property": "value", "value": 8}, {"id": "min-shared", "property": "value", "value": 1},
     {"id": "layout", "property": "value", "value": "separated"}], ["min-shared.value"]))
edge = next(e for e in app.DATA["edges"] if e["weight"] > 30)
print("tap_edge", post("..tap-edge.children...edge-grid.rowData..",
    [{"id": "tap-edge", "property": "children"}, {"id": "edge-grid", "property": "rowData"}],
    [{"id": "cy", "property": "tapEdgeData", "value": edge}], ["cy.tapEdgeData"]))
print("mount", post("mounted-slot.children", {"id": "mounted-slot", "property": "children"},
    [{"id": "mount", "property": "n_clicks", "value": 1}], ["mount.n_clicks"]))
# the background job body, in-process (spawn path already exercised in the browser)
print("sensitivity body:", app.run_sensitivity.__wrapped__(lambda p: None, 1, 8, 8) if hasattr(app.run_sensitivity, "__wrapped__") else "n/a (wrapped)")
print("no deprecation warnings raised")
