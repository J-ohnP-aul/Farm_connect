# UML Diagrams — Local Farm Map V1

PlantUML sources (`.puml`) with rendered PNGs. Derived from the SRS, the database design (`../database/database-design.md`) and the SDD (`../system/system-design.md`); where those documents mark a call as "my call", the diagrams reflect it.

| # | Diagram | File | Covers |
|---|---------|------|--------|
| 1 | Use case | [use-case](use-case.png) | All four SRS use cases (UC-01..04) plus admin/system behaviour, with include/extend |
| 2 | Class | [class-diagram](class-diagram.png) | The six domain classes + the four key services/managers, per the database design |
| 3 | Sequence | [sequence-diagram](sequence-diagram.png) | Buyer journey: discovery query → farm detail → WhatsApp contact (with ContactEvent logging) |
| 4 | Activity | [activity-diagram](activity-diagram.png) | Farmer daily availability update (UC-03), with validation and connectivity branches |
| 5 | Component | [component-diagram](component-diagram.png) | Browser PWA parts, the six Django apps + dependency rules, nginx/gunicorn, DB, OSM tiles |

## Re-rendering

Requires Java (PlantUML jar is not stored in the repo):

```bash
curl -sL -o /tmp/tools/plantuml/plantuml.jar \
  https://github.com/plantuml/plantuml/releases/download/v1.2026.10/plantuml-1.2026.10.jar
java -jar /tmp/tools/plantuml/plantuml.jar -tpng -charset UTF-8 *.puml
```

Edit the `.puml` source, re-render, and the PNG updates — sources are the canonical artefacts.
