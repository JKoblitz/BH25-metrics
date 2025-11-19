import pandas as pd
from rdflib import Graph, Namespace, URIRef, Literal, RDF, RDFS, XSD
from rdflib.namespace import FOAF, OWL, DCTERMS

BASE_TTL = "RIMO.ttl"
# CSV_FILE = "kpis.csv"
INPUT_URL = "http://docs.google.com/spreadsheets/d/1-pdz4O9cD8Xzy0ZbZbEQ3bSEn6k6hmlihqN6zG0kHeU/export?format=csv"
DATA_TTL = "KPIs.ttl"

# Load BASE to copy/bind prefixes, but don't mutate it
base = Graph()
base.parse(BASE_TTL, format="turtle")

# New data graph that imports BASE
data = Graph()
for pfx, ns in base.namespaces():
    data.bind(pfx, ns)

RIMO = Namespace(dict(base.namespaces()).get("rimo","https://w3id.org/RIMO#"))
data.bind("rimo", RIMO)

# Add owl:imports triple
ONTO = URIRef("http://w3id.org/RIMO")   # must match ontology IRI in BASE.ttl
DATA_ONTO = URIRef("http://w3id.org/RIMOkpi")
data.add((DATA_ONTO, RDF.type, OWL.Ontology))
data.add((DATA_ONTO, OWL.imports, ONTO))
data.add((DATA_ONTO, DCTERMS.title, Literal("RIMO KPI Instances", lang="en")))

# Helpers
import re
def slug(s): return re.sub(r"[^a-z0-9]+","_",str(s).strip().lower()).strip("_")
def slugcamel(s):
    # upper camel case from string
    parts = re.split(r"[^a-zA-Z0-9]+", str(s).strip())
    return "".join(p.capitalize() for p in parts if p)
def lit(v, lang=None, dt=None):
    if v is None or str(v).strip()=="" or pd.isna(v):
        return None
    if not dt:
        s = str(v).strip()
        if not s or s.lower() in {"nan", "na", "<na>", "none"}:
            return None
        return Literal(s, lang=lang)
    return Literal(v, lang=lang) if dt is None and lang else Literal(v, datatype=dt) if dt else Literal(v)

# Define a set of tool types
tool_types = {
    "Bioinformatics portal": "web site providing a platform/portal to multiple resources used for research in a focused area, including biological databases, web applications, training resources and so on.",
    "Command-line tool": "A tool with a text-based (command-line) interface.",
    "Database portal": "A Web application, suite or workbench providing a portal to a biological database.",
    "Desktop application": "A tool with a graphical user interface that runs on your desktop environment, e.g. on a PC or mobile device.",
    "Library": "A collection of components that are used to construct other tools. bio.tools scope includes component libraries performing high-level bioinformatics functions but excludes lower-level programming libraries.",
    "Ontology": "A collection of information about concepts, including terms, synonyms, descriptions etc.",
    "Plug-in": "A software component encapsulating a set of related functions, which are not standalone, i.e. depend upon other software for its use, e.g. a Javascript widget, or a plug-in, extension add-on etc. that extends the function of some existing tool.",
    "Script": "A tool written for some run-time environment (e.g. other applications or an OS shell) that automates the execution of tasks. Often a small program written in a general-purpose languages (e.g. Perl, Python) or some domain-specific languages (e.g. sed).",
    "SPARQL endpoint": "A service that provides queries over an RDF knowledge base via the SPARQL query language and protocol, and returns results via HTTP.",
    "Suite": "A collection of tools which are bundled together into a convenient toolkit. Such tools typically share related functionality, a common user interface and can exchange data conveniently. This includes collections of stand-alone command-line tools, or Web applications within a common portal.",
    "Web application": "A tool with a graphical user interface that runs in your Web browser.",
    "Web API": "An application programming interface (API) consisting of endpoints to a request-response message system accessible via HTTP. Includes everything from simple data-access URLs to RESTful APIs.",
    "Web service": "An API described in a machine readable form (typically WSDL) providing programmatic access via SOAP over HTTP.",
    "Workbench": "An application or suite with a graphical user interface, providing an integrated environment for data analysis which includes or may be extended with any number of functions or tools. Includes workflow systems, platforms, frameworks etc.",
    "Workflow": "A set of tools which have been composed together into a pipeline of some sort. Such tools are (typically) standalone, but are composed for convenience, for instance for batch execution via some workflow engine or script.",
    "Helpdesk": "A service providing assistance with the use of bioinformatics tools, data resources, or any other aspect of bioinformatics.",
}
def toolcat(service_category):
    """Map service category to ontology terms."""
    if pd.isna(service_category):
        return None
    service_category = service_category.strip()
    tool_uri = RIMO[service_category.replace(" ", "_")]
    if (tool_uri, RDF.type, RIMO.ServiceCategory) in data:
        return [tool_uri]
    if service_category == "Web applications":
        return [RIMO.Web_application]
    if service_category == "Database":
        return [RIMO.Database_portal]
    if service_category == "Libraries / APIs":
        return [RIMO.Library, RIMO.Web_API]
    if service_category == "Support / Consulting":
        return [RIMO.Helpdesk]
    if service_category == "Tools/ Applications":
        return [RIMO.Desktop_application]
    if service_category == "Workflows / pipelines":
        return [RIMO.Workflow]
    return None

df = pd.read_csv(INPUT_URL)
# Build instances
for n, row in df.iterrows():
    # skip first two rows if they are headers
    if n < 2:
        continue
    name = str(row.get("Indicator","")).strip()
    if not name:
        continue
    kpi = RIMO[slugcamel(name)]

    data.add((kpi, RDF.type, RIMO.KPI))
    data.add((kpi, RIMO.name, Literal(name, lang="en")))

    d = lit(row.get("Description").replace("\n", " ").replace("  ", " "), lang="en")
    if d: data.add((kpi, RIMO.description, d))
    if row.get("Example"):
        ex = lit(row.get("Example"), lang="en")
        if ex: data.add((kpi, RIMO.example, ex))

    # qualitative flag
    t = str(row.get("Type of indicator","")).lower()
    if "qualit" in t:
        data.add((kpi, RIMO.isQualitativeIndicator, Literal(True, datatype=XSD.boolean)))
    elif "quant" in t:
        data.add((kpi, RIMO.isQualitativeIndicator, Literal(False, datatype=XSD.boolean)))

    # tool category relations
    category = toolcat(row.get("Service Category"))
    if category:
        for cat in category:
            data.add((kpi, RIMO.appliedTo, cat))
            mand = str(row.get("Mandatory","")).strip().lower()
            if mand in {"yes","true","1"}:
                data.add((kpi, RIMO.mandatoryFor, cat))
            elif mand in {"no","false","0"}:
                data.add((kpi, RIMO.recommendedFor, cat))

    # means of measurement
    means = str(row.get("Measurement (tool/estimation etc)","")).strip()
    if means:
        mm = RIMO["means/" + slugcamel(means)]
        data.add((mm, RDF.type, RIMO.MeasurementMeans))
        data.add((mm, RDFS.label, Literal(means, lang="en")))
        data.add((kpi, RIMO.measuredBy, mm))

    # automation tools (comma-separated)
    auto = row.get("Automation possible")
    if pd.notna(auto):
        for tok in str(auto).split(","):
            tool = tok.strip()
            if not tool: continue
            at = RIMO["tool/" + slugcamel(tool)]
            data.add((at, RDF.type, RIMO.AutomationTool))
            data.add((at, RDFS.label, Literal(tool)))
            data.add((kpi, RIMO.canBeAutomatedBy, at))

    # requester (Target Group as free text Agent)
    for tgt in str(row.get("Target Group") or "").split(","):
        tgt = tgt.strip()
        if not tgt:
            continue
        ag = RIMO["agent/" + slugcamel(tgt)]
        data.add((ag, RDF.type, FOAF.Agent))
        data.add((ag, RDFS.label, Literal(tgt)))
        data.add((kpi, RIMO.requestedBy, ag))

    # source + link as literals
    link = str(row.get("Link") or "")
    if link.startswith("http"):
        data.add((kpi, DCTERMS.relation, URIRef(link)))


# Serialize only instances + imports
data.serialize(DATA_TTL, format="turtle")
print(f"✅ Wrote {DATA_TTL} (imports BASE)")