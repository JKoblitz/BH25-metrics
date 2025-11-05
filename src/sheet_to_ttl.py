"""
Generate a KPI ontology (TTL) from a Google Sheet or CSV export.

This script:
- Reads the sheet with KPI definitions.
- Creates RDF triples for each indicator.
- Maps metadata fields (description, service category, measurement type, etc.) to properties.
- Writes the output as a .ttl file.
"""

import pandas as pd
from rdflib import Graph, Namespace, Literal, RDF, URIRef
from rdflib.namespace import RDFS, DCTERMS, XSD, FOAF, OWL


# === CONFIGURATION ===
input_url = "http://docs.google.com/spreadsheets/d/1-pdz4O9cD8Xzy0ZbZbEQ3bSEn6k6hmlihqN6zG0kHeU/export?format=csv"
output_file = "RIMO.ttl"

# Define base namespaces
BASE = Namespace("https://w3id.org/RIMO/")
PATO = Namespace("http://purl.obolibrary.org/obo/PATO_")
EDAM = Namespace("http://edamontology.org/")
NCIT = Namespace("http://purl.obolibrary.org/obo/NCIT_")

# Initialize RDF graph
g = Graph()
g.bind("rimo", BASE)
g.bind("rdfs", RDFS)
g.bind("dct", DCTERMS)
g.bind("xsd", XSD)
g.bind("foaf", FOAF)
g.bind("pato", PATO)
g.bind("edam", EDAM)
g.bind("ncit", NCIT)
g.bind("owl", OWL)

# === ADD ONTOLOGY METADATA ===
ontology_uri = URIRef("https://w3id.org/RIMO")

g.add((ontology_uri, RDF.type, OWL.Ontology))
g.add((ontology_uri, DCTERMS.title,
       Literal("Research Infrastructure Monitoring Ontology (RIMO)", lang="en")))
g.add((ontology_uri, DCTERMS.description,
       Literal("""An ontology for representing and harmonising Key Performance Indicators across research infrastructures 
and life science services. It defines classes and properties to describe indicators, measurement methods, relevance, 
and applicable service categories. Developed during the BioHackathon Europe 2025.""", lang="en")))
g.add((ontology_uri, DCTERMS.creator,
       Literal("Julia Koblitz (Leibniz Institute DSMZ)", lang="en")))
g.add((ontology_uri, DCTERMS.contributor,
       Literal("BioHackathon Europe 2025 KPI Monitoring Team", lang="en")))
g.add((ontology_uri, DCTERMS.issued, Literal("2025-11-05", datatype=XSD.date)))
g.add((ontology_uri, DCTERMS.license, URIRef("https://creativecommons.org/licenses/by/4.0/")))
g.add((ontology_uri, OWL.versionInfo, Literal("0.1.0")))
g.add((ontology_uri, DCTERMS.language, Literal("en")))
g.add((ontology_uri, RDFS.seeAlso, URIRef("https://github.com/elixir-europe/biohackathon-kpi")))


# Define a class for KPI indicators
g.add((BASE.Indicator, RDF.type, RDFS.Class))
g.add((BASE.Indicator, RDFS.label, Literal("KPI Indicator", lang="en")))
g.add((BASE.ServiceCategory, RDF.type, RDFS.Class))
g.add((BASE.ServiceCategory, RDFS.label, Literal("Service Category", lang="en")))


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
for tool_type, description in tool_types.items():
    tool_uri = BASE[tool_type.replace(" ", "_")]
    g.add((tool_uri, RDF.type, BASE.ServiceCategory))
    g.add((tool_uri, RDFS.label, Literal(tool_type, lang="en")))
    g.add((tool_uri, RDFS.comment, Literal(description, lang="en")))


def mapToolType(service_category):
    """Map service category to ontology terms."""
    if pd.isna(service_category):
        return None
    service_category = service_category.strip()
    tool_uri = BASE[service_category.replace(" ", "_")]
    if (tool_uri, RDF.type, BASE.ServiceCategory) in g:
        return [tool_uri]
    if service_category == "Web applications":
        return [BASE.Web_application]
    if service_category == "Database":
        return [BASE.Database_portal]
    if service_category == "Libraries / APIs":
        return [BASE.Library, BASE.Web_API]
    if service_category == "Support / Consulting":
        return [BASE.Helpdesk]
    if service_category == "Tools/ Applications":
        return [BASE.Desktop_application]
    if service_category == "Workflows / pipelines":
        return [BASE.Workflow]
    return None

# add Target Group terms
target_groups = {
    "Funding Agency": "An organization that provides funding for research activities.",
    "Service Provider": "An organization or individual that offers services to users or clients.",
    "End User": "The individual or group that ultimately uses or is intended to use a product or service.",
    "Network": "A group or system of interconnected people or organizations that collaborate or share resources.",
    "Technical": "Individuals or teams responsible for the technical aspects of service delivery, including maintenance and support.",
}
for group, description in target_groups.items():
    group_uri = BASE[group.replace(" ", "_")]
    g.add((group_uri, RDF.type, FOAF.Group))
    g.add((group_uri, RDFS.label, Literal(group, lang="en")))
    g.add((group_uri, RDFS.comment, Literal(description, lang="en")))
    
def mapTargetGroup(target_group):
    """Map target group to ontology terms."""
    if pd.isna(target_group):
        return None
    target_group = target_group.split(",")
    groups = []
    for group in target_group:
        group = group.strip()
        group_uri = BASE[group.replace(" ", "_")]
        if (group_uri, RDF.type, FOAF.Group) in g:
            groups.append(group_uri)
    return groups if groups else None
        
automation_tools = {
    "Matomo": "An open-source web analytics platform.",
    "Google Analytics": "A web analytics service offered by Google that tracks and reports website traffic.",
    "Bioconductor": "An open-source software project for the analysis and comprehension of genomic data.",
    "Galaxy": "An open, web-based platform for data-intensive biomedical research.",
    "GitHub": "A web-based platform used for version control and collaborative software development.",
    "Custom scripts": "User-defined scripts created for specific tasks or analyses.",
    "OpenAlex": "An open catalog of the global research system, including publications, authors, institutions, and more.",
}

for tool, description in automation_tools.items():
    tool_uri = BASE[tool.replace(" ", "_")]
    g.add((tool_uri, RDF.type, FOAF.Agent))
    g.add((tool_uri, RDFS.label, Literal(tool, lang="en")))
    g.add((tool_uri, RDFS.comment, Literal(description, lang="en")))
    
def mapAutomationTool(tool_name):
    """Map automation tool to ontology terms."""
    if pd.isna(tool_name):
        return None
    tool_name = tool_name.strip()
    tool_uri = BASE[tool_name.replace(" ", "_")]
    if (tool_uri, RDF.type, FOAF.Agent) in g:
        return tool_uri
    return None

# Define common properties
properties = {
    "indicatorSet": BASE.indicatorSet,
    "description": BASE.description,
    "serviceCategory": BASE.serviceCategory,
    "valueType": BASE.valueType,
    "example": BASE.example,
    "targetGroup": BASE.targetGroup,
    "mandatory": BASE.mandatory,
    "measurement": BASE.measurement,
    "source": BASE.source,
    "automationTool": BASE.automationTool,
    "link": BASE.link,
}

for prop, uri in properties.items():
    g.add((uri, RDF.type, RDF.Property))
    g.add((uri, RDFS.label, Literal(prop.replace("_", " ").capitalize(), lang="en")))

# === LOAD DATA ===
df = pd.read_csv(input_url)
print(df.head())

# === CONVERT EACH ROW ===
for n, row in df.iterrows():
    # skip first two rows if they are headers
    if n < 2:
        continue
    # Create a URI for each KPI
    kpi_id = row["Indicator"].strip().replace(" ", "_").replace("/", "_")
    kpi_uri = BASE[kpi_id]

    g.add((kpi_uri, RDF.type, BASE.Indicator))
    g.add((kpi_uri, RDFS.label, Literal(row["Indicator"], lang="en")))

    # Add all non-empty values as literals
    def add_literal(property_name, value, datatype=None):
        if pd.notna(value) and str(value).strip():
            if datatype:
                lit = Literal(value, datatype=datatype)
            else:
                lit = Literal(value)
            g.add((kpi_uri, properties[property_name], lit))

    val_type = (
        PATO["0103000"]
        if row.get("Type of indicator") == "Quantitative"
        else PATO["0000068"]
    )
    tg = mapTargetGroup(row.get("Target Group"))
    service = mapToolType(row.get("Service Category"))
    add_literal("indicatorSet", row.get("Indicator set"))
    add_literal("description", row.get("Description").replace("\n", " "))
    if service:
        for svc in service:
            add_literal("serviceCategory", svc)
    add_literal("valueType", val_type)
    add_literal("example", row.get("Example"))
    if tg:
        for group in tg:
            add_literal("targetGroup", group)
    add_literal(
        "mandatory",
        row.get("Mandatory"),
        (
            XSD.boolean
            if str(row.get("Mandatory")).lower() in ["true", "yes", "1", 'Yes']
            else None
        ),
    )
    add_literal("measurement", row.get("Measurement (tool/estimation etc)"))
    add_literal("source", row.get("Source"))
    if (row.get("Automation possible")):
        for tool in str(row.get("Automation possible")).split(","):
            tool_uri = mapAutomationTool(tool)
            if tool_uri:
                g.add((kpi_uri, properties["automationTool"], tool_uri))

    add_literal(
        "link",
        row.get("Link"),
        XSD.anyURI if str(row.get("Link")).startswith("http") else None,
    )

# === SAVE TTL ===
g.serialize(destination=output_file, format="turtle")
print(f"KPI ontology exported to {output_file}")
