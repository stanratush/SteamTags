# Imported data

> **Reading this guide for an Import Build.** This guide is written for Steam data. In an Import Build, read **game** as *item* and **tag** as *attribute*. Entries marked *Steam Builds only* do not apply.

An Import lets the study's methods (the Top-N Datasets, the feature analysis, the Tag Network and Parameter Selection) run on a list of items that does not come from Steam. This chapter describes the file, how to import it, why an import can be refused, and what differs in a Build made from it.

## What an Import is

An **Import** plays the role a Snapshot plays for Steam data: a fixed source that Builds read. It is made once from one CSV file and never changes afterwards; a corrected file is a new Import with a new id, and importing a byte-identical file again is refused, naming the existing Import. One Import can define several Top-N Datasets, as a Snapshot does: Overall and, optionally, datasets that keep only the items with a defining attribute.

## The Import file

One wide CSV, one row per item:

- `id`: a whole number above 0, unique per item;
- `name`: the item's name;
- `attributes`: the item's attribute names separated by `;`, most important first (the order is what [Tags per game](03-metric-reference.md#tags-per-game-tag-depth) cuts);
- `score` (optional): a number that ranks the items, highest first. Without it, the file order is the rank;
- any other column: an extra numeric field, shown in the app beside each item. Empty cells are allowed. One of them can be named as the **filter field**, which then drives the app's filter slider and must be filled for every item.

The text rules: UTF-8 (a byte-order mark is removed), commas between columns, quotes as in RFC 4180 (a name with a comma is quoted), a header row, and `.` as the decimal point. Names are trimmed and normalised; attribute names are case-sensitive. Nothing is guessed: a file in another encoding or with another separator is refused with "save as CSV UTF-8". An optional `attributes.csv` beside the file (`id,name`) gives the attributes fixed ids; without it they are numbered in name order.

A small example (an Import needs at least 10 items, so this one would be refused as too short):

```
id,name,attributes,score,months
1,Harbour Lights,Puzzle;Relaxing;Pixel Graphics,812.5,24
2,Night Courier,Action;Roguelike,640,9
3,Seed Vault,Farming Sim;Relaxing,512.25,31
4,Glass Tower,Puzzle;Strategy;Turn-Based,498,12
5,"Ash, Iron and Salt",Strategy;City Builder,455,40
```

Here `score` ranks the items and `months` is an extra field that could be named as the filter field.

## Making an Import

From the repository, either:

- in the app, press **Import data…** below the Build menu's tree, choose the file and, optionally, the filter column (the menu lists the file's numeric columns, or none); or
- on the command line, `steamstudy import items.csv --filter months` (see the [Running Guide](../running-guide.md#import)).

The whole file is checked in one pass. When it is valid, the Import appears in the Build menu with its own **+ New Build** button, which starts a draft from the Import defaults. Making the Import does not make a Build; its first Build is made from a draft ([Making Builds in the app](07-making-builds.md)).

### When an Import is refused

A file with any error is refused as a whole and nothing is stored. The menu shows every problem in a table (file, row, column, code, value and message), and the full list is written to `imports/failed/<attempt_id>/errors.csv` beside a copy of the file. The row is the spreadsheet row number, counting the header as row 1. Warnings do not refuse the file: they are shown after the import and kept in `import.json`.

| Code | Kind | Meaning | What to do |
|---|---|---|---|
| `not_csv_utf8` | error | The file is not UTF-8 text: save it as CSV UTF-8. | Save the file as CSV UTF-8 from your spreadsheet program. |
| `not_comma_delimited` | error | The columns are not separated by commas: save it as CSV UTF-8. | Save it as CSV UTF-8 (comma-separated), not with semicolons or tabs. |
| `bad_csv` | error | The file is not valid CSV (a quote is not closed, or a stray quote). | Close the quote, or remove the stray one, in the row given. |
| `empty_file` | error | The file has no header row. | Add the header row: id,name,attributes. |
| `missing_column` | error | A required column is missing. | Add the column named in the row; names are case-sensitive. |
| `duplicate_column` | error | A column name appears twice in the header. | Rename or remove one of the two columns. |
| `unknown_filter_column` | error | The filter column is not a numeric column of the file. | Name a numeric column of the file, or no filter. |
| `row_length` | error | The row has a different number of cells from the header. | Fix the row's cells; a comma inside a name needs quotes. |
| `bad_id` | error | The id is not a positive whole number. | Give the item a whole number above 0. |
| `duplicate_id` | error | Another item already has this id. | Give each item its own id. |
| `empty_name` | error | The name is empty. | Fill in the item's name. |
| `empty_attributes` | error | The item has no attributes. | Give the item at least one attribute, or remove the row. |
| `empty_attribute` | error | An attribute between two ';' is empty. | Remove the doubled `;` or the `;` at the start or end. |
| `repeated_attribute` | error | The item lists the same attribute twice. | List each attribute once per item. |
| `bad_score` | error | The score is empty or not a finite number. | Give every item a number, with `.` as the decimal point. |
| `bad_filter_value` | error | The filter value is empty or not a finite number. | Fill the filter column for every item, with a number. |
| `bad_field_value` | error | The value is not a finite number (leave the cell empty for none). | Write a number, or leave the cell empty. |
| `attributes_bad_header` | error | attributes.csv must have exactly the columns id,name. | Make the header of attributes.csv exactly `id,name`. |
| `attributes_bad_id` | error | The attribute id is not a positive whole number. | Give the attribute a whole number above 0. |
| `attributes_duplicate_id` | error | Another attribute already has this id. | Give each attribute its own id. |
| `attributes_duplicate_name` | error | Another attribute already has this name. | List each attribute name once. |
| `attributes_empty_name` | error | The attribute name is empty. | Fill in the attribute's name. |
| `attributes_missing` | error | An attribute used by the items is not in attributes.csv. | Add the attribute to attributes.csv, or leave that file out. |
| `too_few_items` | error | An Import needs at least 10 items. | Add items: an Import needs at least 10. |
| `case_clash` | warning | Attribute names that differ only by case are different attributes. | Nothing, if they are meant to differ; otherwise spell them the same. |
| `duplicate_item_name` | warning | Two items have the same name. | Nothing, if they are different items; the id tells them apart. |
| `attributes_unused` | warning | A row of attributes.csv is not used by any item; it is dropped. | Nothing; remove the row if it is a mistake. |
| `many_items` | warning | More than 50,000 items: Builds will be slow. | Nothing; expect Builds and the preview to take longer. |
| `many_attributes` | warning | More than 5,000 distinct attributes: Builds will be slow. | Nothing; expect Builds and the preview to take longer. |

## What changes in an Import Build

- **Rank:** by `score`, highest first, with ties broken by file order; without a score, the file order is the rank, and there are no ties ([Rank and ties](03-metric-reference.md#rank-and-ties)).
- **The filter slider** carries the filter field's name and takes its range from the data; without a filter field it is hidden.
- **The inspector's item table** shows the extra fields.
- **Hidden settings:** app types, content descriptors, the Adult Only notice, Manual Metadata Entries and the Observation Window have no meaning for an Import and are not shown.
- **An attribute missing from the Import's vocabulary** (for example in a rule or a defining attribute) fails the Build.
- **Fewer files:** an Import Build writes `topn_<dataset>.csv` and `item_fields.csv` and none of the Steam-only reports ([Import Builds](04-files.md#import-builds)).
- **Citing:** quote the Import's id and sha256 ([Cite an Import Build](05-citing-and-reproducing.md#cite-an-import-build)), and see the [limits of imported data](06-known-limitations.md#imported-data).
