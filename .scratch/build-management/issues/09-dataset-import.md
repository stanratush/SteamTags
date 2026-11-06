# How does a dataset get imported?
Type: grilling
Status: open
Blocked by: 04, 05, 06

## Question

Charted: an imported dataset is items with ordered attributes, an optional score and optional numeric fields. The import plays the Snapshot's role (raw and fixed). The app stays a Steam tool, with a note for imported data.

On the [generic dataset contract](04-generic-dataset-contract.md), decide:
- the file format(s) the user supplies (one CSV with a delimited attribute column, or items plus item–attribute rows), the encoding and the id rules;
- validation and its error report (duplicate ids, empty attribute lists, non-numeric scores);
- where the import is stored, how it is identified, and that it never changes afterwards;
- which Build settings apply to an import (list size, [tags per game](05-tags-per-game-and-list-size.md), [named rules](06-named-exclusion-rules.md) as attribute rules, datasets defined by an attribute), and which are hidden (app types, content descriptors, Manual Metadata, the Observation Window);
- how the file supplies optional attribute ids, the filter field and extra numeric fields, and how its config names attributes.

Already settled by the contract: item ids are positive integers; every item needs at least one attribute and, where there is a filter field, a value in it; with no score, file order ranks the items and list size still applies; the app shows the filter field's name and range in place of Months Observed, and "ID" in place of "AppID".
