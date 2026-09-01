#!/usr/bin/env python3
"""
Generate the synthetic sales dataset that Archer queries.

Why this exists
---------------
The demo needs a realistic sales database that can be published without
disclosing anything. Rather than committing a 45MB binary, the repository
carries this generator and the database is built during the container image
build. That keeps the repository small, makes the dataset reproducible by
anyone, and means the evaluation suite can rely on fixed, known data.

The output is deterministic: the same seed always produces byte-identical
rows. That property is load-bearing - the evaluation suite compares generated
SQL against expected results, which is only meaningful if the underlying data
does not move.

Nothing here is real. Companies, addresses and identifiers are generated.
Product names are genuine IBM product names, which are public and are the
point of the demo.

Usage
-----
    python scripts/generate_dataset.py                    # writes ./sales.db
    python scripts/generate_dataset.py --output /app/sales.db --rows 100000
"""

from __future__ import annotations

import argparse
import os
import random
import sqlite3
import sys
from datetime import date, timedelta

# Fixed by default so the dataset is reproducible. Change it only if you are
# prepared to regenerate the evaluation expectations along with it.
DEFAULT_SEED = 20260901
DEFAULT_ROWS = 100_000

# The dataset spans a little over six years, matching the original extract.
DATE_START = date(2020, 1, 1)
DATE_END = date(2026, 3, 17)

CUSTOMER_COUNT = 150
END_USER_COUNT = 499

# --- Reference data -------------------------------------------------------

# Weighted so the mix matches the original: mostly software, then services,
# then converged hardware.
ITEM_GROUPS = [("IBM SOFT", 0.55), ("IBM SERV", 0.25), ("IBM CCHW", 0.20)]

DOCUMENT_TYPES = [("Invoice", 0.80), ("Credit", 0.20)]

# Vendor names are deliberately readable company names. Sales extracts of this
# shape tend to carry vendor-master codes and internal routing notes in this
# field rather than anything a person would recognise, and those have no place
# in a public demo.
VENDORS = [
    ("501-V00612", "IBM United Kingdom Limited"),
    ("501-V00890", "IBM Global Financing"),
    ("501-V01034", "IBM Software Group"),
    ("501-V00508", "IBM Dealer Finance"),
]

SUB_BRAND = "SAA"
COUNTRY = "GBR"

RENEWAL_TERMS = ["-", "1.0", "3.0", "12.0", "24.0", "36.0"]

# Sub-group codes per item group, mirroring the original hierarchy.
SUB_GROUPS = {
    "IBM SERV": [("IBW99", "IBW1")],
    "IBM CCHW": [("IBMHW1", "IBW2"), ("IBMHW2", "IBW2"), ("IBMHW3", "IBW2"), ("IBMHW4", "IBW2")],
    "IBM SOFT": [
        ("IBMXAAS-E", "IBW4"), ("IBW44", "IBW8"), ("IBW51", "IBW4"), ("IBW55", "IBW6"),
        ("IBW18", "IBW5"), ("IBW62", "IBW9"), ("IBW57", "IBW6"), ("IBW48", "IBW3"),
        ("IBW33", "IBW3"), ("IBW36", "IBW11"), ("IBW72", "IBW11"), ("IBW21", "IBW5"),
        ("IBW70", "IBW3"), ("IBW39", "IBW11"),
    ],
}

PRODUCTS = {
    "IBM CCHW": [
        "IBM Elastic Storage Server 3000",
        "IBM FlashSystem 5200 All-Flash Storage Array",
        "IBM FlashSystem 9500 NVMe All-Flash Array",
        "IBM Power E1080 Processor Server",
        "IBM Power S1014 4-Core 3.0 GHz Processor Server",
        "IBM Power S1024 16-Core 3.9 GHz Processor Server",
        "IBM Tape Library TS4300 LTO Ultrium 8 Data Cartridge",
        "IBM Z16 A02 Central Processing Complex Frame",
    ],
    "IBM SERV": [
        "IBM Consulting Managed Services Monthly Fee",
        "IBM Expert Labs Data & AI Services Engagement",
        "IBM Garage Methodology Consulting Day Rate",
        "IBM Lab Services Implementation Professional Services Day Rate",
        "IBM Software Subscription and Support Renewal 1 Year",
        "IBM Technical Support Services per Annum",
    ],
    "IBM SOFT": [
        "IBM Aspera Enterprise 1 Gbps Install Subscription License",
        "IBM Aspera Enterprise 100 Mbps Install Subscription License",
        "IBM Aspera Enterprise On Demand Gigabyte Overage",
        "IBM Aspera on Cloud Advanced Terabyte Transmitted per Annum",
        "IBM Automation Decision Services per Authorized User per Month",
        "IBM Blueworks Live Editor Authorized User per Annum",
        "IBM Cloud Pak for Data as a Service 1 British Pound per Month",
        "IBM Cloud Pak for Security per RVU",
        "IBM Cloud Platform 1 British Pound per Month",
        "IBM Cognos Analytics Administrator per Authorized User",
        "IBM Cognos Analytics on Cloud Professional per User per Month",
        "IBM Concert App Management Essential per Month",
        "IBM Concert Intelligent Integration per Instance per Month",
        "IBM Db2 Advanced Enterprise Server Edition per PVU",
        "IBM Db2 Standard Edition per Processor Value Unit",
        "IBM Envizi ESG Suite per Module per Month",
        "IBM Envizi Scope 3 Analytics per Annum",
        "IBM Guardium Data Protection per Managed Server",
        "IBM Instana Application Performance Management per Kubernetes Node",
        "IBM Instana Observability per Host per Month",
        "IBM MaaS360 with Watson Enterprise per Device per Month",
        "IBM MaaS360 with Watson Essentials per Device per Month",
        "IBM Maximo Application Suite per AppPoint per Month",
        "IBM Maximo Visual Inspection per GPU per Month",
        "IBM OpenPages GRC Platform per Authorized User",
        "IBM OpenPages Operational Risk Management per User",
        "IBM Planning Analytics Modeler per Authorized User per Month",
        "IBM Planning Analytics User per Authorized User per Month",
        "IBM Robotic Process Automation per Bot per Month",
        "IBM SPSS Statistics Base Authorized User Annual SW Subscription",
        "IBM SPSS Statistics Premium Authorized User Annual SW Subscription",
        "IBM Security QRadar SIEM per Event per Second",
        "IBM Security QRadar SOAR per User per Year",
        "IBM Sterling B2B Integrator per RVU",
        "IBM Sterling Order Management per Order per Month",
        "IBM Turbonomic Application Resource Management per Core",
        "IBM Turbonomic Platform per Managed VM per Month",
        "IBM Watson Machine Learning Accelerated per Month",
        "IBM Watson Studio Professional per Month",
        "IBM WebSphere Application Server Network Deployment per PVU",
        "IBM WebSphere Liberty Core per PVU Annual SW Subscription",
    ],
}

# City to real postcode area, so generated addresses look plausible.
CITIES = [
    ("Aberdeen", "AB"), ("Belfast", "BT"), ("Birmingham", "B"), ("Bradford", "BD"),
    ("Bristol", "BS"), ("Cambridge", "CB"), ("Cardiff", "CF"), ("Chester", "CH"),
    ("Coventry", "CV"), ("Derby", "DE"), ("Edinburgh", "EH"), ("Exeter", "EX"),
    ("Glasgow", "G"), ("Hull", "HU"), ("Leeds", "LS"), ("Leicester", "LE"),
    ("Liverpool", "L"), ("London", "EC"), ("Manchester", "M"), ("Newcastle", "NE"),
    ("Norwich", "NR"), ("Nottingham", "NG"), ("Oxford", "OX"), ("Plymouth", "PL"),
    ("Portsmouth", "PO"), ("Reading", "RG"), ("Sheffield", "S"), ("Southampton", "SO"),
    ("Stoke-on-Trent", "ST"), ("Swansea", "SA"),
]

STREETS = [
    "Church Lane", "Green Lane", "High Street", "Station Road", "Victoria Road",
    "Mill Lane", "Park Avenue", "Queens Road", "Kings Road", "Manor Way",
    "Bridge Street", "Chapel Street", "North Road", "Grange Road", "Elm Grove",
]

# Company names are assembled from neutral word lists. No real company should
# be reachable by combining these; if one collides it is coincidence, and the
# data behind it is meaningless anyway.
NAME_FIRST = [
    "Meridian", "Apex", "Peak", "Diamond", "Falcon", "Raven", "Crest", "Galaxy",
    "Maple", "Icon", "Cobalt", "Helix", "Summit", "Vertex", "Aurora", "Quantum",
    "Northern", "Silver", "Granite", "Harbour", "Lumen", "Orbit", "Pioneer", "Sable",
]
NAME_SECOND = [
    "Beacon", "Cedar", "Wave", "Acorn", "Ibis", "Crest", "Summit", "Vertex",
    "Harbour", "Compass", "Lantern", "Meadow", "Anchor", "Bridge", "Forge", "Willow",
]
NAME_KIND = [
    "Networks", "Analytics", "Holdings", "Global", "Dynamics", "Data", "Cloud",
    "Enterprises", "Innovations", "IT", "Systems", "Partners", "Technologies",
    "Solutions", "Digital", "Consulting",
]
NAME_SUFFIX = ["Ltd", "Ltd", "Ltd", "PLC"]


def weighted_choice(rng: random.Random, options: list[tuple[str, float]]) -> str:
    """Pick one option using the given weights."""
    roll = rng.random()
    cumulative = 0.0
    for value, weight in options:
        cumulative += weight
        if roll < cumulative:
            return value
    return options[-1][0]


def make_company_names(rng: random.Random, count: int) -> list[str]:
    """Generate `count` distinct company names."""
    names: set[str] = set()
    while len(names) < count:
        name = (
            f"{rng.choice(NAME_FIRST)} {rng.choice(NAME_SECOND)} "
            f"{rng.choice(NAME_KIND)} {rng.choice(NAME_SUFFIX)}"
        )
        names.add(name)
    # Sorted so the order does not depend on set iteration, which would break
    # determinism across Python versions.
    return sorted(names)


def make_address(rng: random.Random) -> tuple[str, str, str]:
    """Return (full_address, city, postcode) for a generated UK address."""
    city, area = rng.choice(CITIES)
    postcode = f"{area}{rng.randint(1, 20)} {rng.randint(1, 9)}{rng.choice('ABDEFGHJLNPQRSTUWXYZ')}{rng.choice('ABDEFGHJLNPQRSTUWXYZ')}"
    street = f"{rng.randint(1, 200)} {rng.choice(STREETS)}"
    full = f"{street}\n{city}\n{postcode}\nUnited Kingdom"
    return full, city, postcode


def build_parties(rng: random.Random) -> tuple[list[dict], list[dict]]:
    """Build the customer and end-user reference tables."""
    customer_names = make_company_names(rng, CUSTOMER_COUNT)
    customers = []
    for index, name in enumerate(customer_names):
        address, city, postcode = make_address(rng)
        customers.append(
            {
                "number": f"501-C{20000 + index:05d}",
                "name": name,
                "address": address,
                "city": city,
                "postcode": postcode,
            }
        )

    end_user_names = make_company_names(rng, END_USER_COUNT)
    end_users = []
    for name in end_user_names:
        address, _city, postcode = make_address(rng)
        end_users.append({"name": name, "address": address, "postcode": postcode})

    return customers, end_users


def create_schema(conn: sqlite3.Connection) -> None:
    """Create the sales_data table. Column order matches the original extract."""
    conn.execute("DROP TABLE IF EXISTS sales_data")
    conn.execute(
        """
        CREATE TABLE sales_data (
            document_type               TEXT,
            customer_number             TEXT,
            customer_name               TEXT,
            document_date               TEXT,
            document_number             TEXT,
            sales_order_number          TEXT,
            customer_order_number       TEXT,
            item_group                  TEXT,
            vendor_number               TEXT,
            vendor_name                 TEXT,
            item_number                 TEXT,
            item_description            TEXT,
            multi_year_deal_flag_so     TEXT,
            line_number                 TEXT,
            item_sub_group_1            TEXT,
            item_sub_group_2            TEXT,
            item_sub_group_3            TEXT,
            item_sub_group_5            TEXT,
            brand                       TEXT,
            sub_brand                   TEXT,
            quantity                    REAL,
            revenue                     REAL,
            end_user_company_name       TEXT,
            end_user_address            TEXT,
            end_user_post_code          TEXT,
            end_user_country            TEXT,
            purchase_order_number       TEXT,
            customer_address            TEXT,
            customer_city               TEXT,
            customer_post_code          TEXT,
            customer_country            TEXT,
            serial_numbers              TEXT,
            contract_start_date         TEXT,
            contract_end_date           TEXT,
            vendor_quotation_number     TEXT,
            maintenance_contract_number TEXT,
            renewal_term_months         TEXT
        )
        """
    )


def generate_rows(rng: random.Random, rows: int, customers: list[dict], end_users: list[dict]):
    """
    Yield rows one at a time.

    Rows are grouped into documents: a document is one order, and each carries
    one to five lines, averaging a little over two. That structure matters
    because the prompt tells the model a "deal" is a document and a "line" is a
    row, and questions frequently count one or the other.
    """
    span_days = (DATE_END - DATE_START).days
    document_index = 0
    emitted = 0

    while emitted < rows:
        document_index += 1
        customer = rng.choice(customers)
        end_user = rng.choice(end_users)
        document_type = weighted_choice(rng, DOCUMENT_TYPES)
        item_group = weighted_choice(rng, ITEM_GROUPS)

        document_date = DATE_START + timedelta(days=rng.randint(0, span_days))
        # IBM SOFT is almost always brand IBA; converged hardware is IBW.
        brand = "IBW" if item_group == "IBM CCHW" else ("IBW" if rng.random() < 0.02 else "IBA")
        vendor_number, vendor_name = rng.choice(VENDORS)
        sub_group_1, sub_group_2 = rng.choice(SUB_GROUPS[item_group])

        document_number = f"501-SPC{500000 + document_index:06d}"
        sales_order_number = f"501-SO{400000 + document_index:06d}"
        purchase_order_number = f"501-PO{600000 + document_index:06d}"
        customer_order_number = f"PO-{rng.randint(1000, 99999)}"
        multi_year = "Yes" if rng.random() < 0.20 else "No"

        contract_start = document_date + timedelta(days=rng.randint(0, 60))
        contract_end = contract_start + timedelta(days=rng.choice([30, 90, 365, 730, 1095]))

        # Weighted to average roughly 2.25 lines per document, matching the
        # original extract. Most orders are one or two lines; a few are large.
        line_count = min(rng.choice([1, 1, 1, 2, 2, 3, 3, 5]), rows - emitted)

        for line in range(1, line_count + 1):
            magnitude = round(rng.uniform(20.0, 4_000_000.0), 2)
            quantity_magnitude = rng.randint(1, 50)

            if document_type == "Credit":
                revenue = -magnitude
                quantity = float(-quantity_magnitude)
            else:
                revenue = magnitude
                quantity = float(quantity_magnitude)

            yield (
                document_type,
                customer["number"],
                customer["name"],
                document_date.isoformat(),
                document_number,
                sales_order_number,
                customer_order_number,
                item_group,
                vendor_number,
                vendor_name,
                "".join(rng.choices("ABCDEFGHJKLMNPQRSTUVWXYZ0123456789", k=6)),
                rng.choice(PRODUCTS[item_group]),
                multi_year,
                f"{float(line)}",
                sub_group_1,
                sub_group_2,
                None,
                None,
                brand,
                SUB_BRAND,
                quantity,
                revenue,
                end_user["name"],
                end_user["address"],
                end_user["postcode"],
                COUNTRY,
                purchase_order_number,
                customer["address"],
                customer["city"],
                customer["postcode"],
                COUNTRY,
                None,
                contract_start.isoformat(),
                contract_end.isoformat(),
                f"{19000000 + rng.randint(1, 900000)}",
                f"{10000000 + rng.randint(1, 900000)}",
                rng.choice(RENEWAL_TERMS),
            )
            emitted += 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate the Archer synthetic sales dataset.")
    parser.add_argument("--output", default="sales.db", help="Path to write the SQLite database.")
    parser.add_argument("--rows", type=int, default=DEFAULT_ROWS, help="Number of rows to generate.")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED, help="Random seed.")
    args = parser.parse_args()

    rng = random.Random(args.seed)

    output = os.path.abspath(args.output)
    if os.path.exists(output):
        os.remove(output)

    conn = sqlite3.connect(output)
    try:
        create_schema(conn)
        customers, end_users = build_parties(rng)

        placeholders = ",".join(["?"] * 37)
        conn.executemany(
            f"INSERT INTO sales_data VALUES ({placeholders})",
            generate_rows(rng, args.rows, customers, end_users),
        )
        conn.commit()

        # Deliberately no indexes. At 100,000 rows SQLite scans the whole table
        # in a few milliseconds, while the model call takes seconds - so the
        # database is never the bottleneck, and indexes would add roughly 8MB
        # to every image pull for no measurable gain. Cold-start size matters
        # more here than query time.

        total = conn.execute("SELECT COUNT(*) FROM sales_data").fetchone()[0]
    finally:
        conn.close()

    size = os.path.getsize(output)
    print(f"Wrote {total:,} rows to {output} ({size:,} bytes), seed {args.seed}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
