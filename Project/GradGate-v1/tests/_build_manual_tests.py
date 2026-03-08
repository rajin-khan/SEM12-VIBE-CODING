#!/usr/bin/env python3
"""One-time script to generate all manual test case CSV files."""
import csv, os

DIR = os.path.dirname(os.path.abspath(__file__))

def w(name, rows):
    with open(os.path.join(DIR, name), "w", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(["Course_Code","Credits","Grade","Semester"])
        for r in rows:
            wr.writerow(r)

# ── Helper course sets ─────────────────────────────────────────────
CSE_GED = [
    ("ENG102",3,"A","Spring 2019"),("ENG103",3,"A-","Spring 2019"),
    ("ENG111",3,"B+","Spring 2019"),("BEN205",3,"B","Summer 2019"),
    ("HIS102",3,"A","Summer 2019"),("HIS103",3,"B+","Fall 2019"),
    ("PHI104",3,"B","Fall 2019"),("BIO103",3,"B+","Fall 2019"),
    ("BIO103L",0,"A","Fall 2019"),("POL101",3,"A-","Spring 2020"),
    ("ECO101",3,"B","Spring 2020"),("SOC101",3,"B+","Spring 2020"),
]
CSE_SCHOOL = [
    ("MAT112",3,"B","Spring 2019"),("MAT116",0,"B","Spring 2019"),
    ("MAT120",3,"B+","Summer 2019"),("MAT125",3,"B","Summer 2019"),
    ("MAT130",3,"A-","Fall 2019"),("MAT250",3,"B","Spring 2020"),
    ("MAT350",3,"B-","Summer 2020"),("MAT361",3,"C+","Summer 2020"),
    ("PHY107",3,"B","Fall 2019"),("PHY107L",1,"B+","Fall 2019"),
    ("PHY108",3,"B-","Spring 2020"),("PHY108L",1,"B","Spring 2020"),
    ("CHE101",3,"C+","Summer 2020"),("CHE101L",1,"B","Summer 2020"),
    ("EEE452",3,"B","Fall 2020"),("EEE154",1,"A","Fall 2020"),
    ("CSE115",3,"A","Spring 2019"),("CSE115L",1,"A","Spring 2019"),
]
CSE_MAJOR = [
    ("CSE173",3,"A-","Summer 2019"),("CSE215",3,"A","Fall 2019"),
    ("CSE215L",1,"A","Fall 2019"),("CSE225",3,"B+","Spring 2020"),
    ("CSE225L",0,"A","Spring 2020"),("CSE231",3,"B","Spring 2020"),
    ("CSE231L",0,"B+","Spring 2020"),("EEE141",3,"B","Summer 2020"),
    ("EEE141L",1,"B+","Summer 2020"),("EEE111",3,"B-","Fall 2020"),
    ("EEE111L",1,"B","Fall 2020"),("CSE311",3,"A-","Fall 2020"),
    ("CSE311L",0,"A","Fall 2020"),("CSE332",3,"B+","Spring 2021"),
    ("CSE332L",0,"B","Spring 2021"),("CSE323",3,"B","Summer 2021"),
    ("CSE327",3,"A-","Summer 2021"),("CSE331",3,"B","Fall 2021"),
    ("CSE331L",0,"B+","Fall 2021"),("CSE373",3,"B+","Fall 2021"),
    ("CSE425",3,"A","Spring 2022"),
]
CSE_CAP = [
    ("CSE299",1,"A","Spring 2021"),("CSE499A",1.5,"A","Fall 2022"),
    ("CSE499B",1.5,"A","Spring 2023"),
]
CSE_INTERN = [("CSE498R",1,"A","Spring 2023")]
CSE_TRAIL = [
    ("CSE440",3,"B+","Fall 2022"),("CSE445",3,"A-","Spring 2023"),
    ("CSE422",3,"B","Spring 2022"),
]
CSE_OPEN = [("PSY101",3,"B","Spring 2022")]
CSE_EXTRA_PAD = [("SOC201",3,"A-","Summer 2022")]

CSE_ALL = CSE_GED + CSE_SCHOOL + CSE_MAJOR + CSE_CAP + CSE_INTERN + CSE_TRAIL + CSE_OPEN + CSE_EXTRA_PAD

# BBA full set
BBA_GED = [
    ("ENG102",3,"A","Spring 2019"),("ENG103",3,"A-","Spring 2019"),
    ("HIS103",3,"B+","Summer 2019"),("PHI101",3,"B","Summer 2019"),
    ("BEN205",3,"B+","Fall 2019"),("ENV203",3,"A","Fall 2019"),
    ("PSY101",3,"B","Fall 2019"),
]
BBA_CORE_BIZ = [
    ("ACT201",3,"B+","Spring 2020"),("ACT202",3,"B","Spring 2020"),
    ("BUS172",3,"B","Spring 2020"),("ECO101",3,"A-","Summer 2020"),
    ("ECO104",3,"B+","Summer 2020"),("FIN254",3,"B","Fall 2020"),
    ("MGT210",3,"A","Fall 2020"),("MGT314",3,"B","Spring 2021"),
    ("MGT368",3,"B+","Spring 2021"),("MKT202",3,"A-","Summer 2021"),
    ("MIS205",3,"B","Summer 2021"),("LAW200",3,"B+","Fall 2021"),
]
BBA_MAJOR = [
    ("BUS101",3,"A","Spring 2019"),("BUS112",3,"A-","Spring 2019"),
    ("BUS134",3,"B+","Summer 2019"),("BUS251",3,"B","Fall 2020"),
    ("BUS401",3,"B+","Spring 2022"),("BUS498",4,"A","Fall 2022"),
    ("MGT321",3,"B","Fall 2021"),("MGT489",3,"A-","Spring 2022"),
    ("QM212",3,"B","Summer 2020"),
]
BBA_CONC_FIN = [
    ("FIN410",3,"B+","Fall 2021"),("FIN433",3,"A-","Spring 2022"),
    ("FIN435",3,"B","Spring 2022"),("FIN440",3,"B+","Summer 2022"),
    ("FIN444",3,"A","Fall 2022"),("FIN455",3,"B","Fall 2022"),
]
BBA_MAT = [("MAT112",3,"B","Spring 2019")]
BBA_ELECTIVE_PAD = [
    ("HRM340",3,"B+","Fall 2022"),("SOC101",3,"A","Spring 2020"),
    ("POL101",3,"B","Summer 2020"),("HIS205",3,"A-","Spring 2023"),
    ("INB350",3,"B","Spring 2023"),("MKT330",3,"A","Spring 2023"),
    ("SCM310",3,"B+","Summer 2023"),
]
BBA_ALL = BBA_GED + BBA_CORE_BIZ + BBA_MAJOR + BBA_CONC_FIN + BBA_MAT + BBA_ELECTIVE_PAD

# EEE full set
EEE_GED = [
    ("ENG102",3,"A","Spring 2019"),("ENG103",3,"B+","Spring 2019"),
    ("ENG111",3,"B","Summer 2019"),("HIS101",3,"A-","Summer 2019"),
    ("PHI104",3,"B","Fall 2019"),("POL101",3,"B+","Fall 2019"),
    ("ECO101",3,"A","Fall 2019"),("ENV203",3,"B","Spring 2020"),
]
EEE_MATH = [
    ("MAT116",0,"B","Spring 2019"),("MAT120",3,"B+","Summer 2019"),
    ("MAT125",3,"B","Summer 2019"),("MAT130",3,"A-","Fall 2019"),
    ("MAT250",3,"B","Spring 2020"),("MAT350",3,"B+","Summer 2020"),
    ("MAT361",3,"B","Summer 2020"),
]
EEE_SCI = [
    ("PHY107",3,"B+","Fall 2019"),("PHY107L",1,"A","Fall 2019"),
    ("PHY108",3,"B","Spring 2020"),("PHY108L",1,"B+","Spring 2020"),
    ("CHE101",3,"B","Summer 2020"),("CHE101L",1,"A","Summer 2020"),
    ("BIO103",3,"B","Fall 2019"),
]
EEE_MAJOR = [
    ("CSE115",3,"A","Spring 2019"),("CSE115L",1,"A","Spring 2019"),
    ("EEE141",3,"B+","Fall 2019"),("EEE141L",1,"B","Fall 2019"),
    ("EEE241",3,"B","Spring 2020"),("EEE241L",1,"B+","Spring 2020"),
    ("EEE111",3,"A-","Summer 2020"),("EEE111L",1,"A","Summer 2020"),
    ("EEE211",3,"B","Fall 2020"),("EEE211L",1,"B+","Fall 2020"),
    ("EEE311",3,"B","Spring 2021"),("EEE311L",1,"B+","Spring 2021"),
    ("EEE221",3,"A-","Fall 2020"),("EEE361",3,"B","Spring 2021"),
    ("EEE342",3,"B+","Summer 2021"),("EEE342L",1,"A","Summer 2021"),
    ("EEE363",3,"B","Fall 2021"),("EEE363L",1,"B+","Fall 2021"),
    ("EEE312",3,"A-","Spring 2022"),("EEE312L",1,"A","Spring 2022"),
    ("EEE299",1,"A","Summer 2021"),("EEE321",3,"B","Fall 2021"),
    ("EEE321L",1,"B+","Fall 2021"),
    ("EEE499A",3,"A","Fall 2022"),("EEE499B",3,"A","Spring 2023"),
]
EEE_ELECTIVE_PAD = [
    ("SOC101",3,"B","Spring 2020"),("PSY101",3,"A-","Summer 2020"),
    ("HIS205",3,"B+","Fall 2020"),("EEE362",3,"B","Spring 2022"),
    ("EEE362L",1,"A","Spring 2022"),("EEE461",3,"B+","Summer 2022"),
    ("EEE462",3,"A","Fall 2022"),("BEN205",3,"B","Summer 2023"),
]
EEE_ALL = EEE_GED + EEE_MATH + EEE_SCI + EEE_MAJOR + EEE_ELECTIVE_PAD

# ETE full set
ETE_GED = [
    ("ENG102",3,"A","Spring 2019"),("ENG103",3,"B+","Spring 2019"),
    ("ENG111",3,"B","Summer 2019"),("HIS103",3,"A-","Summer 2019"),
    ("PHI101",3,"B","Fall 2019"),("POL101",3,"B+","Fall 2019"),
    ("SOC101",3,"A","Fall 2019"),("ENV203",3,"B","Spring 2020"),
]
ETE_MATH = [
    ("MAT116",0,"B","Spring 2019"),("MAT120",3,"B+","Summer 2019"),
    ("MAT125",3,"B","Summer 2019"),("MAT130",3,"A-","Fall 2019"),
    ("MAT350",3,"B","Spring 2020"),("MAT361",3,"B+","Summer 2020"),
]
ETE_SCI = [
    ("PHY107",3,"B+","Fall 2019"),("PHY107L",1,"A","Fall 2019"),
    ("PHY108",3,"B","Spring 2020"),("PHY108L",1,"B+","Spring 2020"),
    ("CHE101",3,"B","Summer 2020"),("CHE101L",1,"A","Summer 2020"),
]
ETE_MAJOR = [
    ("ETE131",3,"B+","Fall 2019"),("ETE131L",1,"A","Fall 2019"),
    ("ETE132",3,"A","Spring 2020"),("ETE132L",1,"A","Spring 2020"),
    ("ETE211",3,"B","Summer 2020"),("ETE211L",1,"B+","Summer 2020"),
    ("ETE212",3,"A-","Fall 2020"),("ETE212L",1,"A","Fall 2020"),
    ("ETE221",3,"B","Fall 2020"),("ETE283",2,"B+","Spring 2021"),
    ("ETE311",3,"B","Spring 2021"),("ETE311L",1,"A","Spring 2021"),
    ("ETE331",3,"B+","Summer 2021"),("ETE331L",1,"A","Summer 2021"),
    ("ETE361",3,"B","Fall 2021"),("ETE381",2,"A-","Fall 2021"),
    ("ETE423",3,"B+","Spring 2022"),("ETE424",3,"B","Spring 2022"),
    ("ETE481",2,"A","Fall 2022"),
    ("ETE499A",2,"A","Fall 2022"),("ETE499B",2,"A","Spring 2023"),
]
ETE_EXTRA = [
    ("PSY101",3,"B","Summer 2022"),("SOC201",3,"B+","Fall 2022"),
    ("HIS205",3,"A-","Spring 2022"),("ETE334",3,"B","Spring 2023"),
    ("ETE334L",1,"A","Spring 2023"),("ETE411",3,"B+","Fall 2022"),
    ("POL202",3,"A","Summer 2023"),("ETH201",3,"B","Summer 2023"),
    ("BEN205",3,"B+","Fall 2023"),("ECO101",3,"A","Fall 2023"),
    ("PAD201",3,"B","Spring 2024"),("ANT101",3,"A-","Spring 2024"),
]
ETE_ALL = ETE_GED + ETE_MATH + ETE_SCI + ETE_MAJOR + ETE_EXTRA

# CEE full set
CEE_GED = [
    ("ENG102",3,"A","Spring 2019"),("ENG103",3,"B+","Spring 2019"),
    ("HIS103",3,"A-","Summer 2019"),("PHI101",3,"B","Summer 2019"),
    ("POL101",3,"B+","Fall 2019"),("SOC101",3,"A","Fall 2019"),
    ("ENV203",3,"B","Spring 2020"),
]
CEE_MATH = [
    ("MAT116",0,"B","Spring 2019"),("MAT120",3,"B+","Summer 2019"),
    ("MAT125",3,"B","Summer 2019"),("MAT130",3,"A-","Fall 2019"),
    ("MAT250",3,"B","Spring 2020"),("MAT350",3,"B+","Summer 2020"),
    ("MAT361",3,"B","Summer 2020"),
]
CEE_SCI = [
    ("PHY107",3,"B+","Fall 2019"),("PHY107L",1,"A","Fall 2019"),
    ("PHY108",3,"B","Spring 2020"),("PHY108L",1,"B+","Spring 2020"),
    ("CHE101",3,"B","Summer 2020"),("CHE101L",1,"A","Summer 2020"),
]
CEE_MAJOR = [
    ("CEE110",3,"B","Fall 2019"),("CEE210",3,"B+","Spring 2020"),
    ("CEE211",3,"A-","Spring 2020"),("CEE214",3,"B","Summer 2020"),
    ("CEE215",3,"B+","Summer 2020"),("CEE250",3,"A","Fall 2020"),
    ("CEE311",3,"B","Fall 2020"),("CEE311L",1,"B+","Fall 2020"),
    ("CEE312",3,"A-","Spring 2021"),("CEE313",3,"B","Spring 2021"),
    ("CEE313L",1,"B+","Spring 2021"),("CEE314",3,"B","Summer 2021"),
    ("CEE315",3,"A","Summer 2021"),("CEE320",3,"B+","Fall 2021"),
    ("CEE330",3,"B","Fall 2021"),("CEE330L",1,"A","Fall 2021"),
    ("CEE335",3,"B","Spring 2022"),("CEE335L",1,"B+","Spring 2022"),
    ("CEE350",3,"A-","Spring 2022"),("CEE360",3,"B","Summer 2022"),
    ("CEE370",3,"B+","Summer 2022"),("CEE410",3,"A","Fall 2022"),
    ("CEE470",3,"B","Fall 2022"),
    ("CEE498",3,"A","Spring 2023"),("CEE499",3,"A","Spring 2023"),
]
CEE_ELECTIVE_PAD = [
    ("CSE115",3,"B","Spring 2019"),("CSE115L",1,"A","Spring 2019"),
    ("CEE340",3,"B+","Fall 2022"),("CEE431",3,"A","Spring 2023"),
    ("CEE373",3,"B","Spring 2023"),("CEE415",3,"A-","Fall 2022"),
    ("SOC201",3,"B","Summer 2022"),("PSY101",3,"A","Summer 2022"),
    ("HIS205",3,"B+","Spring 2023"),("POL202",3,"B","Summer 2023"),
    ("BEN205",3,"A-","Fall 2023"),
]
CEE_ALL = CEE_GED + CEE_MATH + CEE_SCI + CEE_MAJOR + CEE_ELECTIVE_PAD

# ENV full set
ENV_GED = [
    ("ENG103",3,"A","Spring 2019"),("ENG105",3,"B+","Fall 2019"),
    ("HIS103",3,"B","Summer 2019"),("PHI101",3,"A-","Summer 2019"),
]
ENV_MATH = [
    ("MAT120",3,"B+","Spring 2019"),("ENV172",3,"B","Fall 2019"),
    ("ENV173",3,"A-","Spring 2020"),
]
ENV_SCI = [
    ("CHE101",3,"B","Summer 2019"),("CHE101L",1,"A","Summer 2019"),
    ("BIO103",3,"B+","Fall 2019"),("BIO103L",1,"A","Fall 2019"),
]
ENV_MAJOR = [
    ("ENV102",3,"B","Spring 2020"),("ENV107",3,"A-","Spring 2020"),
    ("ENV203",3,"B+","Summer 2020"),("ENV205",3,"B","Summer 2020"),
    ("ENV207",3,"A","Fall 2020"),("ENV208",3,"B","Fall 2020"),
    ("ENV209",3,"B+","Spring 2021"),("ENV214",3,"A-","Spring 2021"),
    ("ENV215",4,"B","Summer 2021"),("ENV260",3,"B+","Summer 2021"),
    ("ENV307",3,"A","Fall 2021"),("ENV315",3,"B","Fall 2021"),
    ("ENV316",3,"B+","Spring 2022"),("ENV373",3,"A-","Spring 2022"),
    ("ENV375",3,"B","Summer 2022"),("ENV405",3,"B+","Fall 2022"),
    ("ENV408",3,"A","Fall 2022"),("ENV409",3,"B","Spring 2023"),
    ("ENV410",3,"B+","Spring 2023"),("ENV414",3,"A-","Spring 2023"),
    ("ENV455",3,"B","Summer 2023"),
    ("ENV498",3,"A","Fall 2023"),("ENV499",3,"A","Fall 2023"),
]
ENV_ELECTIVE_PAD = [
    ("ENG102",3,"B","Spring 2019"),("BEN205",3,"A","Summer 2019"),
    ("POL101",3,"B+","Fall 2019"),("SOC101",3,"A-","Spring 2020"),
    ("PSY101",3,"B","Summer 2020"),("ECO101",3,"B+","Fall 2020"),
    ("ENV303",3,"A","Spring 2021"),("ENV311",3,"B","Summer 2021"),
    ("ENV318",3,"A-","Fall 2021"),("ENV402",3,"B+","Spring 2022"),
    ("HIS205",3,"A","Summer 2023"),
]
ENV_ALL = ENV_GED + ENV_MATH + ENV_SCI + ENV_MAJOR + ENV_ELECTIVE_PAD

# ENG full set
ENG_GED = [
    ("HIS103",3,"A","Spring 2019"),("PHI101",3,"B+","Spring 2019"),
    ("SOC101",3,"B","Summer 2019"),("ENV203",3,"A-","Summer 2019"),
    ("POL101",3,"B","Fall 2019"),
]
ENG_MATH = [("MIS105",3,"B+","Spring 2019")]
ENG_SCI = [("SCI101",3,"B","Spring 2019")]
ENG_MAJOR = [
    ("ENG109",3,"A","Spring 2019"),("ENG110",3,"A-","Summer 2019"),
    ("ENG111",3,"B+","Summer 2019"),("ENG115",3,"A","Fall 2019"),
    ("ENG210",3,"B+","Spring 2020"),("ENG220",3,"A","Spring 2020"),
    ("ENG230",3,"A-","Summer 2020"),("ENG260",3,"B+","Summer 2020"),
    ("ENG311",3,"A","Fall 2020"),("ENG312",3,"B+","Fall 2020"),
    ("ENG321",3,"A-","Spring 2021"),("ENG322",3,"A","Fall 2021"),
    ("ENG331",3,"B+","Spring 2021"),("ENG401",3,"A","Fall 2021"),
    ("ENG402",3,"A-","Spring 2022"),("ENG499",3,"A","Fall 2022"),
]
ENG_EXTRA = [
    ("ENG216",3,"B+","Summer 2021"),("ENG302",3,"A","Spring 2022"),
    ("ENG307",3,"B","Summer 2022"),("ENG341",3,"A-","Fall 2022"),
    ("ENG346",3,"B+","Spring 2023"),("ENG351",3,"A","Spring 2023"),
    ("ENG361",3,"B","Summer 2023"),("ENG377",3,"A-","Summer 2023"),
    ("ENG381",3,"B+","Fall 2023"),("ENG417",3,"A","Fall 2023"),
    ("ENG431",3,"B","Spring 2024"),("ENG441",3,"A-","Spring 2024"),
    ("ENG446",3,"B+","Summer 2024"),("ENG481",3,"A","Summer 2024"),
    ("ENG102",3,"B","Spring 2019"),("ENG103",3,"A-","Summer 2019"),
    ("BEN205",3,"B+","Fall 2020"),("ECO101",3,"B","Spring 2023"),
]
ENG_ALL = ENG_GED + ENG_MATH + ENG_SCI + ENG_MAJOR + ENG_EXTRA

# ECO full set
ECO_GED = [
    ("ENG103",3,"A","Spring 2019"),("ENG105",3,"B+","Fall 2019"),
    ("BEN205",3,"B","Summer 2019"),("HIS103",3,"A-","Summer 2019"),
    ("PHI101",3,"B","Fall 2019"),("POL101",3,"B+","Fall 2019"),
]
ECO_MATH = [
    ("MAT125",3,"B+","Spring 2019"),("ECO172",3,"B","Fall 2019"),
    ("ECO173",3,"A-","Spring 2020"),
]
ECO_SCI = [("MIS107",3,"B","Spring 2019")]
ECO_MAJOR = [
    ("ECO101",3,"A","Spring 2019"),("ECO104",3,"B+","Summer 2019"),
    ("ECO201",3,"A-","Spring 2020"),("ECO204",3,"B+","Summer 2020"),
    ("ECO317",3,"A","Fall 2020"),("ECO328",3,"B","Fall 2020"),
    ("ECO349",3,"B+","Spring 2021"),("ECO354",3,"A-","Spring 2021"),
    ("ECO372",3,"B","Summer 2021"),("ECO414",3,"B+","Fall 2021"),
    ("ECO490",3,"A","Spring 2022"),
]
ECO_EXTRA = [
    ("ECO245",3,"B","Summer 2020"),("ECO301",3,"A","Fall 2021"),
    ("ECO304",3,"B+","Spring 2022"),("ECO309",3,"A-","Summer 2022"),
    ("ECO348",3,"B","Fall 2022"),("ECO406",3,"A","Spring 2023"),
    ("ECO415",3,"B+","Spring 2023"),("ECO492",3,"A-","Summer 2023"),
    ("ECO496",3,"B","Summer 2023"),("SOC101",3,"B+","Fall 2019"),
    ("PSY101",3,"A","Spring 2020"),("ENG102",3,"B","Spring 2019"),
    ("ENV203",3,"A-","Summer 2019"),("HIS205",3,"B+","Fall 2022"),
    ("BEN205",3,"A","Summer 2023"),("PAD201",3,"B","Fall 2023"),
    ("LAW200",3,"A-","Spring 2024"),("TNM201",3,"B+","Spring 2024"),
    ("WMS201",3,"A","Summer 2024"),
]
ECO_ALL = ECO_GED + ECO_MATH + ECO_SCI + ECO_MAJOR + ECO_EXTRA

# ═══════════════════════════════════════════════════════════════════
# DELIVERABLES
# ═══════════════════════════════════════════════════════════════════

# test_L1.csv – credit tally test (F, W, I, retake, 0-credit)
w("test_L1.csv", [
    ("ENG102",3,"A","Spring 2023"),
    ("MAT116",0,"B","Spring 2023"),
    ("CSE115",3,"A-","Spring 2023"),
    ("CSE115L",1,"A","Spring 2023"),
    ("HIS103",3,"F","Summer 2023"),
    ("PHY107",3,"C+","Fall 2023"),
    ("PHY107L",1,"B","Fall 2023"),
    ("CSE173",3,"W","Fall 2023"),
    ("MAT120",3,"B-","Spring 2024"),
    ("HIS103",3,"B+","Spring 2024"),
    ("CSE215",3,"A","Summer 2024"),
    ("CSE215L",1,"A","Summer 2024"),
    ("CSE225",3,"F","Fall 2024"),
    ("CSE225L",0,"I","Fall 2024"),
    ("MAT125",3,"B","Fall 2024"),
])

# test_L2.csv – CGPA test across 5 semesters
w("test_L2.csv", [
    ("ENG102",3,"A","Spring 2023"),("MAT116",0,"B","Spring 2023"),
    ("CSE115",3,"B+","Spring 2023"),("CSE115L",1,"A","Spring 2023"),
    ("HIS103",3,"F","Summer 2023"),("PHY107",3,"C+","Summer 2023"),
    ("MAT120",3,"C","Fall 2023"),("PHY107L",1,"B","Fall 2023"),
    ("CSE173",3,"B-","Fall 2023"),
    ("HIS103",3,"B+","Spring 2024"),("MAT125",3,"B","Spring 2024"),
    ("CSE215",3,"A-","Spring 2024"),
    ("MAT130",3,"C+","Summer 2024"),("CSE215L",1,"A","Summer 2024"),
    ("CSE225",3,"D","Fall 2024"),("CSE231",3,"C-","Fall 2024"),
])

# test_L3.csv – deficiency test (CSE student missing many courses)
w("test_L3.csv", [
    ("ENG102",3,"A","Spring 2023"),("MAT116",0,"B","Spring 2023"),
    ("CSE115",3,"A-","Spring 2023"),("CSE115L",1,"A","Spring 2023"),
    ("ENG103",3,"B+","Summer 2023"),("PHY107",3,"C+","Summer 2023"),
    ("PHY107L",1,"B","Summer 2023"),("CSE173",3,"B","Fall 2023"),
    ("MAT120",3,"B-","Fall 2023"),("MAT125",3,"B","Fall 2023"),
    ("HIS103",3,"A","Spring 2024"),("CSE215",3,"A","Spring 2024"),
    ("CSE215L",1,"A","Spring 2024"),("MAT130",3,"B+","Spring 2024"),
    ("CSE225",3,"F","Summer 2024"),("PHI104",3,"B","Summer 2024"),
    ("CSE231",3,"B","Fall 2024"),("CSE231L",0,"B+","Fall 2024"),
    ("EEE141",3,"C+","Fall 2024"),("EEE141L",1,"B","Fall 2024"),
])

# test_retake.csv – retake scenarios
w("test_retake.csv", [
    ("ENG102",3,"A","Spring 2023"),("MAT116",0,"B","Spring 2023"),
    ("CSE115",3,"A-","Spring 2023"),("CSE115L",1,"A","Spring 2023"),
    ("CSE173",3,"F","Summer 2023"),
    ("CSE173",3,"D","Fall 2023"),
    ("CSE173",3,"B+","Spring 2024"),
    ("HIS103",3,"F","Summer 2023"),
    ("HIS103",3,"B","Spring 2024"),
    ("CSE225",3,"F","Fall 2023"),
    ("CSE225",3,"F","Spring 2024"),
    ("MAT120",3,"C-","Summer 2023"),
    ("MAT120",3,"B","Fall 2024"),
])

# ═══════════════════════════════════════════════════════════════════
# NAMED TEST CASES
# ═══════════════════════════════════════════════════════════════════

# tc01 – CSE all pass (eligible)
w("tc01_cse_all_pass.csv", CSE_ALL)

# tc02 – BBA all pass (eligible)
w("tc02_bba_all_pass.csv", BBA_ALL)

# tc03 – EEE all pass
w("tc03_eee_all_pass.csv", EEE_ALL)

# tc04 – ETE all pass
w("tc04_ete_all_pass.csv", ETE_ALL)

# tc05 – CEE all pass
w("tc05_cee_all_pass.csv", CEE_ALL)

# tc06 – ENV all pass
w("tc06_env_all_pass.csv", ENV_ALL)

# tc07 – ENG all pass
w("tc07_eng_all_pass.csv", ENG_ALL)

# tc08 – ECO all pass
w("tc08_eco_all_pass.csv", ECO_ALL)

# tc09 – CSE extra credits
w("tc09_cse_extra_credits.csv", CSE_ALL + [
    ("SOC201",3,"A","Summer 2022"),("HIS205",3,"B+","Fall 2022"),
    ("POL202",3,"A-","Spring 2023"),("PAD201",3,"B","Spring 2023"),
    ("ETH201",3,"B+","Summer 2022"),
])

# tc10 – BBA extra credits
w("tc10_bba_extra_credits.csv", BBA_ALL + [
    ("SOC101",3,"A","Spring 2020"),("HIS205",3,"B+","Summer 2022"),
    ("POL101",3,"B","Fall 2022"),("MKT330",3,"A-","Spring 2023"),
])

# tc11 – CSE with F grades
w("tc11_cse_with_F.csv", [
    ("ENG102",3,"A","Spring 2023"),("MAT116",0,"B","Spring 2023"),
    ("CSE115",3,"A-","Spring 2023"),("CSE115L",1,"A","Spring 2023"),
    ("HIS103",3,"B+","Spring 2023"),("PHY107",3,"F","Summer 2023"),
    ("MAT120",3,"B-","Summer 2023"),("CSE173",3,"F","Fall 2023"),
    ("MAT125",3,"B","Fall 2023"),("CSE215",3,"A","Spring 2024"),
    ("CSE215L",1,"A","Spring 2024"),("CSE225",3,"F","Summer 2024"),
    ("PHI104",3,"B","Summer 2024"),
])

# tc12 – BBA with F grades
w("tc12_bba_with_F.csv", [
    ("ENG102",3,"A","Spring 2023"),("ENG103",3,"B+","Spring 2023"),
    ("BUS101",3,"A","Spring 2023"),("BUS112",3,"B","Spring 2023"),
    ("HIS103",3,"B+","Summer 2023"),("ACT201",3,"F","Summer 2023"),
    ("ECO101",3,"B","Fall 2023"),("MGT210",3,"F","Fall 2023"),
    ("PHI101",3,"B+","Fall 2023"),("MKT202",3,"A-","Spring 2024"),
])

# tc13 – CSE with Incomplete
w("tc13_cse_with_I.csv", [
    ("ENG102",3,"A","Spring 2023"),("MAT116",0,"B","Spring 2023"),
    ("CSE115",3,"A-","Spring 2023"),("CSE115L",1,"A","Spring 2023"),
    ("HIS103",3,"I","Summer 2023"),("PHY107",3,"B","Summer 2023"),
    ("MAT120",3,"B-","Fall 2023"),("CSE173",3,"I","Fall 2023"),
    ("MAT125",3,"B","Fall 2023"),("CSE215",3,"A","Spring 2024"),
])

# tc14 – BBA with Incomplete
w("tc14_bba_with_I.csv", [
    ("ENG102",3,"A","Spring 2023"),("ENG103",3,"B+","Spring 2023"),
    ("BUS101",3,"A","Spring 2023"),("BUS112",3,"B","Spring 2023"),
    ("HIS103",3,"I","Summer 2023"),("ACT201",3,"B+","Summer 2023"),
    ("ECO101",3,"B","Fall 2023"),("MGT210",3,"A","Fall 2023"),
])

# tc15 – CSE with Withdrawals
w("tc15_cse_with_W.csv", [
    ("ENG102",3,"A","Spring 2023"),("MAT116",0,"B","Spring 2023"),
    ("CSE115",3,"A-","Spring 2023"),("CSE115L",1,"A","Spring 2023"),
    ("HIS103",3,"W","Summer 2023"),("PHY107",3,"W","Summer 2023"),
    ("MAT120",3,"B-","Fall 2023"),("CSE173",3,"W","Fall 2023"),
    ("MAT125",3,"B","Fall 2023"),("CSE215",3,"A","Spring 2024"),
])

# tc16 – BBA with Withdrawals
w("tc16_bba_with_W.csv", [
    ("ENG102",3,"A","Spring 2023"),("ENG103",3,"B+","Spring 2023"),
    ("BUS101",3,"A","Spring 2023"),("BUS112",3,"B","Spring 2023"),
    ("HIS103",3,"W","Summer 2023"),("ACT201",3,"W","Summer 2023"),
    ("ECO101",3,"B","Fall 2023"),("MGT210",3,"A","Fall 2023"),
])

# tc17 – CSE mixed F/I/W
w("tc17_cse_mixed_FIW.csv", [
    ("ENG102",3,"A","Spring 2023"),("MAT116",0,"B","Spring 2023"),
    ("CSE115",3,"A-","Spring 2023"),("CSE115L",1,"A","Spring 2023"),
    ("HIS103",3,"F","Summer 2023"),("PHY107",3,"I","Summer 2023"),
    ("MAT120",3,"W","Fall 2023"),("CSE173",3,"F","Fall 2023"),
    ("MAT125",3,"B","Fall 2023"),("HIS103",3,"B+","Spring 2024"),
    ("PHY107",3,"B","Spring 2024"),("CSE215",3,"A","Summer 2024"),
])

# tc18 – BBA mixed F/I/W
w("tc18_bba_mixed_FIW.csv", [
    ("ENG102",3,"A","Spring 2023"),("ENG103",3,"B+","Spring 2023"),
    ("BUS101",3,"F","Spring 2023"),("BUS112",3,"W","Spring 2023"),
    ("HIS103",3,"I","Summer 2023"),("ACT201",3,"F","Summer 2023"),
    ("ECO101",3,"B","Fall 2023"),("MGT210",3,"A","Fall 2023"),
    ("BUS101",3,"B","Fall 2023"),("ACT201",3,"B+","Spring 2024"),
])

# tc19 – no waivers (ENG102 + MAT112 both taken, 136 credits needed)
no_waiver = [r for r in CSE_ALL]
w("tc19_no_waivers.csv", no_waiver)

# tc20 – ENG102 waived
eng102_waived = [r for r in CSE_ALL if r[0] != "ENG102"]
eng102_waived.insert(0, ("ENG102",3,"T","Spring 2019"))
w("tc20_eng102_waived.csv", eng102_waived)

# tc21 – MAT112 waived
mat112_waived = [r for r in CSE_ALL if r[0] != "MAT112"]
mat112_waived.insert(0, ("MAT112",3,"T","Spring 2019"))
w("tc21_mat112_waived.csv", mat112_waived)

# tc22 – both waived
both_waived = [r for r in CSE_ALL if r[0] not in ("ENG102","MAT112")]
both_waived.insert(0, ("ENG102",3,"T","Spring 2019"))
both_waived.insert(1, ("MAT112",3,"T","Spring 2019"))
w("tc22_both_waived.csv", both_waived)

# tc23 – retake pass
w("tc23_retake_pass.csv", [
    ("ENG102",3,"A","Spring 2023"),("MAT116",0,"B","Spring 2023"),
    ("CSE115",3,"A-","Spring 2023"),("CSE115L",1,"A","Spring 2023"),
    ("CSE225",3,"F","Summer 2023"),("HIS103",3,"F","Summer 2023"),
    ("MAT120",3,"B-","Fall 2023"),("CSE173",3,"B","Fall 2023"),
    ("CSE225",3,"B","Spring 2024"),("HIS103",3,"B+","Spring 2024"),
    ("MAT125",3,"B","Spring 2024"),
])

# tc24 – retake still fail
w("tc24_retake_still_fail.csv", [
    ("ENG102",3,"A","Spring 2023"),("MAT116",0,"B","Spring 2023"),
    ("CSE115",3,"A-","Spring 2023"),("CSE115L",1,"A","Spring 2023"),
    ("CSE225",3,"F","Summer 2023"),
    ("CSE225",3,"F","Fall 2023"),
    ("MAT120",3,"B","Fall 2023"),
])

# tc25 – multiple retakes (F -> D -> B+)
w("tc25_multiple_retakes.csv", [
    ("ENG102",3,"A","Spring 2023"),("MAT116",0,"B","Spring 2023"),
    ("CSE115",3,"A-","Spring 2023"),("CSE115L",1,"A","Spring 2023"),
    ("CSE225",3,"F","Summer 2023"),
    ("CSE225",3,"D","Fall 2023"),
    ("CSE225",3,"B+","Spring 2024"),
    ("MAT120",3,"B","Fall 2023"),("CSE173",3,"A-","Fall 2023"),
])

# tc26 – transfer T grade
w("tc26_transfer_T_grade.csv", [
    ("ENG102",3,"T","Spring 2023"),("MAT116",0,"B","Spring 2023"),
    ("CSE115",3,"A-","Spring 2023"),("CSE115L",1,"A","Spring 2023"),
    ("HIS103",3,"T","Summer 2023"),("PHY107",3,"T","Summer 2023"),
    ("PHY107L",1,"T","Summer 2023"),
    ("MAT120",3,"B-","Fall 2023"),("CSE173",3,"B","Fall 2023"),
])

# tc27 – non-NSU courses
w("tc27_non_nsu_courses.csv", [
    ("ENG102",3,"A","Spring 2023"),("MAT116",0,"B","Spring 2023"),
    ("CSE115",3,"A-","Spring 2023"),("CSE115L",1,"A","Spring 2023"),
    ("XYZ999",3,"B","Summer 2023"),("ABC123",3,"A","Summer 2023"),
    ("MAT120",3,"B-","Fall 2023"),
])

# tc28 – invalid grades
w("tc28_invalid_grades.csv", [
    ("ENG102",3,"A","Spring 2023"),("MAT116",0,"B","Spring 2023"),
    ("CSE115",3,"Z","Spring 2023"),("CSE115L",1,"A","Spring 2023"),
    ("HIS103",3,"X","Summer 2023"),
])

# tc29 – empty transcript
w("tc29_empty_transcript.csv", [])

# tc30 – probation P1 (first semester below 2.0)
w("tc30_probation_P1.csv", [
    ("ENG102",3,"F","Spring 2023"),("MAT116",0,"D","Spring 2023"),
    ("CSE115",3,"D","Spring 2023"),("CSE115L",1,"F","Spring 2023"),
    ("HIS103",3,"D+","Spring 2023"),
    ("ENG103",3,"B","Summer 2023"),("MAT120",3,"B+","Summer 2023"),
    ("CSE173",3,"A-","Summer 2023"),
])

# tc31 – probation P2 (two consecutive semesters below 2.0)
w("tc31_probation_P2.csv", [
    ("ENG102",3,"D","Spring 2023"),("MAT116",0,"F","Spring 2023"),
    ("CSE115",3,"F","Spring 2023"),("HIS103",3,"D","Spring 2023"),
    ("MAT120",3,"F","Summer 2023"),("CSE173",3,"D","Summer 2023"),
    ("PHY107",3,"D+","Summer 2023"),
    ("ENG103",3,"A","Fall 2023"),("MAT125",3,"B+","Fall 2023"),
])

# tc32 – dismissal (3+ consecutive semesters below 2.0)
w("tc32_dismissal.csv", [
    ("ENG102",3,"D","Spring 2023"),("CSE115",3,"F","Spring 2023"),
    ("HIS103",3,"D","Spring 2023"),
    ("MAT120",3,"F","Summer 2023"),("CSE173",3,"D","Summer 2023"),
    ("PHY107",3,"F","Fall 2023"),("MAT125",3,"D","Fall 2023"),
    ("CSE215",3,"D+","Spring 2024"),
])

# tc33 – BBA concentration FIN
w("tc33_bba_concentration_FIN.csv", BBA_ALL)

# tc34 – BBA undeclared (courses spread across multiple concentrations)
bba_undecl = [r for r in BBA_GED + BBA_CORE_BIZ + BBA_MAJOR + BBA_MAT + BBA_ELECTIVE_PAD]
bba_undecl += [
    ("FIN410",3,"B+","Fall 2021"),("MKT330",3,"A","Spring 2022"),
    ("HRM340",3,"B","Spring 2022"),("ACT310",3,"B+","Summer 2022"),
    ("MGT330",3,"A-","Summer 2022"),("SCM310",3,"B","Fall 2022"),
]
w("tc34_bba_undeclared.csv", bba_undecl)

# tc35 – prerequisite violation (CSE215 without CSE173)
w("tc35_prereq_violation.csv", [
    ("ENG102",3,"A","Spring 2023"),("MAT116",0,"B","Spring 2023"),
    ("CSE115",3,"A-","Spring 2023"),("CSE115L",1,"A","Spring 2023"),
    ("CSE215",3,"B+","Summer 2023"),
    ("CSE173",3,"A","Fall 2023"),
    ("CSE225",3,"B","Fall 2023"),
    ("MAT120",3,"B-","Spring 2024"),
])

# tc36 – zero credit labs only
w("tc36_zero_credit_labs_only.csv", [
    ("CSE115L",0,"A","Spring 2023"),("CSE225L",0,"B+","Summer 2023"),
    ("CSE231L",0,"A","Fall 2023"),("CSE311L",0,"B","Spring 2024"),
    ("BIO103L",0,"A-","Spring 2024"),
])

# tc37 – perfect 4.0 CGPA
w("tc37_high_cgpa_4.0.csv", [
    ("ENG102",3,"A","Spring 2023"),("MAT116",0,"A","Spring 2023"),
    ("CSE115",3,"A","Spring 2023"),("CSE115L",1,"A","Spring 2023"),
    ("HIS103",3,"A","Summer 2023"),("PHY107",3,"A","Summer 2023"),
    ("PHY107L",1,"A","Summer 2023"),("MAT120",3,"A","Fall 2023"),
    ("MAT125",3,"A","Fall 2023"),("CSE173",3,"A","Fall 2023"),
    ("CSE215",3,"A","Spring 2024"),("CSE215L",1,"A","Spring 2024"),
    ("ENG103",3,"A","Spring 2024"),
])

# tc38 – borderline 2.0 CGPA
w("tc38_borderline_2.0.csv", [
    ("ENG102",3,"C","Spring 2023"),("MAT116",0,"C","Spring 2023"),
    ("CSE115",3,"C","Spring 2023"),("CSE115L",1,"C","Spring 2023"),
    ("HIS103",3,"C","Summer 2023"),("PHY107",3,"C","Summer 2023"),
    ("PHY107L",1,"C","Summer 2023"),("MAT120",3,"C","Fall 2023"),
    ("MAT125",3,"D+","Fall 2023"),("CSE173",3,"C+","Fall 2023"),
    ("CSE215",3,"C","Spring 2024"),("CSE215L",1,"C","Spring 2024"),
    ("ENG103",3,"C-","Spring 2024"),
])

# ═══════════════════════════════════════════════════════════════════
# ERROR / ROBUSTNESS TESTS (tc39–tc44)
# ═══════════════════════════════════════════════════════════════════

# tc39 – malformed CSV columns (wrong column names)
with open(os.path.join(DIR, "tc39_malformed_columns.csv"), "w", newline="") as f:
    wr = csv.writer(f)
    wr.writerow(["Course Code", "Credit Hours", "Letter Grade", "Term"])
    wr.writerow(["ENG102", 3, "A", "Spring 2023"])
    wr.writerow(["CSE115", 3, "B+", "Summer 2023"])

# tc40 – empty fields (empty course code, empty grade, empty credits)
with open(os.path.join(DIR, "tc40_empty_fields.csv"), "w", newline="") as f:
    wr = csv.writer(f)
    wr.writerow(["Course_Code","Credits","Grade","Semester"])
    wr.writerow(["ENG102", 3, "A", "Spring 2023"])
    wr.writerow(["", 3, "B", "Spring 2023"])
    wr.writerow(["CSE115", "", "A-", "Summer 2023"])
    wr.writerow(["MAT120", 3, "", "Fall 2023"])
    wr.writerow(["HIS103", 3, "B+", "Spring 2024"])

# tc41 – negative credits
w("tc41_negative_credits.csv", [
    ("ENG102",3,"A","Spring 2023"),
    ("CSE115",-3,"B+","Summer 2023"),
    ("MAT120",-1,"B","Fall 2023"),
    ("HIS103",3,"A-","Spring 2024"),
])

# tc42 – whitespace in grades (should be trimmed by parser)
with open(os.path.join(DIR, "tc42_whitespace_grades.csv"), "w", newline="") as f:
    wr = csv.writer(f)
    wr.writerow(["Course_Code","Credits","Grade","Semester"])
    wr.writerow(["ENG102", 3, " A ", "Spring 2023"])
    wr.writerow(["CSE115", 3, " b+ ", "Summer 2023"])
    wr.writerow(["MAT120", 3, " B- ", "Fall 2023"])
    wr.writerow(["HIS103", 3, "A-", "Spring 2024"])

# tc43 – same course twice in same semester
w("tc43_duplicate_same_semester.csv", [
    ("ENG102",3,"A","Spring 2023"),
    ("CSE115",3,"B+","Spring 2023"),
    ("CSE115",3,"A-","Spring 2023"),
    ("MAT120",3,"B","Fall 2023"),
])

# tc44 – P (Pass) grade
w("tc44_p_grade.csv", [
    ("ENG102",3,"A","Spring 2023"),
    ("MAT116",0,"B","Spring 2023"),
    ("CSE115",3,"P","Summer 2023"),
    ("CSE115L",1,"P","Summer 2023"),
    ("HIS103",3,"B+","Fall 2023"),
    ("MAT120",3,"A-","Fall 2023"),
])

# tc52 – retake with worse grade (best grade should be kept)
w("tc52_retake_worse_grade.csv", [
    ("ENG102",3,"A","Spring 2023"),
    ("MAT116",0,"B","Spring 2023"),
    ("CSE115",3,"B","Spring 2023"),
    ("CSE115",3,"D","Fall 2023"),
    ("MAT120",3,"C+","Summer 2023"),
    ("MAT120",3,"C-","Fall 2023"),
    ("HIS103",3,"D","Summer 2023"),
    ("HIS103",3,"B-","Fall 2023"),
    ("CSE173",3,"C","Fall 2023"),
    ("CSE173",3,"F","Spring 2024"),
])

# tc53 – retake of B+ or above (ineligible per NSU policy)
w("tc53_retake_ineligible.csv", [
    ("ENG102",3,"A","Spring 2023"),
    ("MAT116",0,"B","Spring 2023"),
    ("CSE115",3,"A","Spring 2023"),
    ("CSE115",3,"A-","Fall 2023"),
    ("HIS103",3,"B+","Summer 2023"),
    ("HIS103",3,"A","Fall 2023"),
    ("MAT120",3,"A-","Summer 2023"),
    ("MAT120",3,"B+","Fall 2023"),
])

# ═══════════════════════════════════════════════════════════════════
# PREREQUISITE TESTS (tc45–tc48)
# ═══════════════════════════════════════════════════════════════════

# tc45 – credit-based prerequisite violation (CSE299 requires 60 credits, student has ~20)
w("tc45_credit_prereq_violation.csv", [
    ("ENG102",3,"A","Spring 2023"),
    ("MAT116",0,"B","Spring 2023"),
    ("CSE115",3,"A-","Spring 2023"),
    ("CSE115L",1,"A","Spring 2023"),
    ("CSE173",3,"B+","Summer 2023"),
    ("CSE299",1,"A","Summer 2023"),
    ("MAT120",3,"B","Fall 2023"),
    ("MAT125",3,"B+","Fall 2023"),
])

# tc46 – co-requisite same semester (CSE115 + CSE115L in same semester — should NOT be violation)
w("tc46_corequisite_same_semester.csv", [
    ("ENG102",3,"A","Spring 2023"),
    ("MAT116",0,"B","Spring 2023"),
    ("CSE115",3,"A-","Summer 2023"),
    ("CSE115L",1,"A","Summer 2023"),
    ("CSE173",3,"B+","Fall 2023"),
    ("CSE215",3,"A","Spring 2024"),
    ("CSE215L",1,"A","Spring 2024"),
])

# tc47 – EEE prerequisite violation (EEE211 before EEE111)
w("tc47_eee_prereq_violation.csv", [
    ("ENG102",3,"A","Spring 2019"),
    ("MAT120",3,"B+","Spring 2019"),
    ("CSE115",3,"A-","Spring 2019"),
    ("CSE115L",1,"A","Spring 2019"),
    ("EEE211",3,"B+","Summer 2019"),
    ("EEE211L",1,"A","Summer 2019"),
    ("EEE111",3,"B","Fall 2019"),
    ("EEE111L",1,"B+","Fall 2019"),
    ("EEE141",3,"A-","Fall 2019"),
    ("EEE141L",1,"A","Fall 2019"),
])

# tc48 – BBA prerequisite violation (FIN254 before ACT201)
w("tc48_bba_prereq_violation.csv", [
    ("ENG102",3,"A","Spring 2023"),
    ("BUS101",3,"B+","Spring 2023"),
    ("BUS112",3,"B","Spring 2023"),
    ("FIN254",3,"A-","Summer 2023"),
    ("ACT201",3,"B+","Fall 2023"),
    ("ECO101",3,"B","Fall 2023"),
    ("MGT210",3,"A","Spring 2024"),
])

# ═══════════════════════════════════════════════════════════════════
# ADVANCED TESTS (tc49–tc51)
# ═══════════════════════════════════════════════════════════════════

# tc49 – CSE student with BBA courses (cross-program, should be electives)
w("tc49_cross_program_courses.csv", [
    ("ENG102",3,"A","Spring 2023"),
    ("MAT116",0,"B","Spring 2023"),
    ("CSE115",3,"A-","Spring 2023"),
    ("CSE115L",1,"A","Spring 2023"),
    ("CSE173",3,"B+","Summer 2023"),
    ("ACT201",3,"B","Summer 2023"),
    ("FIN254",3,"A-","Fall 2023"),
    ("MKT202",3,"B+","Fall 2023"),
    ("MAT120",3,"B","Spring 2024"),
])

# tc50 – BBA with FIN courses but --concentration MKT (mismatch)
bba_mkt_test = BBA_GED + BBA_CORE_BIZ + BBA_MAJOR + BBA_MAT + [
    ("FIN410",3,"B+","Fall 2021"),("FIN433",3,"A-","Spring 2022"),
    ("FIN435",3,"B","Spring 2022"),("FIN440",3,"B+","Summer 2022"),
    ("MKT330",3,"A","Fall 2022"),("MKT340",3,"B","Fall 2022"),
]
w("tc50_bba_wrong_concentration.csv", bba_mkt_test)

# tc51 – I grade resolved later (I in one semester, real grade in next = retake)
w("tc51_i_grade_resolved.csv", [
    ("ENG102",3,"A","Spring 2023"),
    ("MAT116",0,"B","Spring 2023"),
    ("CSE115",3,"A-","Spring 2023"),
    ("CSE115L",1,"A","Spring 2023"),
    ("CSE173",3,"I","Summer 2023"),
    ("CSE173",3,"B+","Fall 2023"),
    ("HIS103",3,"I","Summer 2023"),
    ("HIS103",3,"A","Spring 2024"),
    ("MAT120",3,"B","Spring 2024"),
])

# ═══════════════════════════════════════════════════════════════════
# MINOR PROGRAM TESTS (tc54–tc57)
# ═══════════════════════════════════════════════════════════════════

# tc54 – CSE student with complete Math Minor (all 3 electives from pool + prereqs met)
w("tc54_cse_math_minor_complete.csv", [
    ("ENG102",3,"A","Spring 2021"),
    ("MAT116",0,"B+","Spring 2021"),
    ("MAT120",3,"A-","Summer 2021"),
    ("MAT125",3,"B+","Summer 2021"),
    ("MAT130",3,"A","Fall 2021"),
    ("MAT250",3,"B","Spring 2022"),
    ("CSE115",3,"A","Spring 2021"),
    ("CSE115L",1,"A","Spring 2021"),
    ("CSE173",3,"B+","Fall 2021"),
    ("PHY107",3,"B","Fall 2021"),
    ("PHY107L",1,"A-","Fall 2021"),
    ("MAT370",3,"A","Fall 2022"),
    ("MAT480",3,"A-","Spring 2023"),
    ("MAT485",3,"B+","Spring 2023"),
])

# tc55 – CSE student with complete Physics Minor (4 required + 1 optional + prereqs met)
w("tc55_cse_physics_minor_complete.csv", [
    ("ENG102",3,"A","Spring 2021"),
    ("MAT116",0,"B","Spring 2021"),
    ("CSE115",3,"A-","Spring 2021"),
    ("CSE115L",1,"A","Spring 2021"),
    ("CSE173",3,"B+","Summer 2021"),
    ("PHY107",3,"A","Fall 2021"),
    ("PHY107L",1,"A-","Fall 2021"),
    ("PHY108",3,"B+","Spring 2022"),
    ("PHY108L",1,"A","Spring 2022"),
    ("MAT120",3,"B","Summer 2021"),
    ("PHY230",3,"A","Fall 2022"),
    ("PHY240",3,"A-","Fall 2022"),
    ("PHY250",3,"B+","Spring 2023"),
    ("PHY260",3,"B","Spring 2023"),
    ("PHY108",3,"A","Summer 2023"),
])

# tc56 – CSE student with partial Math Minor (only 1 of 3 needed electives)
w("tc56_cse_math_minor_partial.csv", [
    ("ENG102",3,"A","Spring 2021"),
    ("MAT116",0,"B","Spring 2021"),
    ("MAT120",3,"B+","Summer 2021"),
    ("MAT125",3,"A-","Summer 2021"),
    ("MAT130",3,"B","Fall 2021"),
    ("MAT250",3,"B+","Spring 2022"),
    ("CSE115",3,"A-","Spring 2021"),
    ("CSE115L",1,"A","Spring 2021"),
    ("CSE173",3,"B+","Fall 2021"),
    ("MAT370",3,"A","Fall 2022"),
])

# tc57 – CSE student with minor electives but missing prerequisites
w("tc57_cse_minor_missing_prereqs.csv", [
    ("ENG102",3,"A","Spring 2021"),
    ("MAT116",0,"B","Spring 2021"),
    ("CSE115",3,"A-","Spring 2021"),
    ("CSE115L",1,"A","Spring 2021"),
    ("MAT120",3,"B+","Summer 2021"),
    ("CSE173",3,"B+","Fall 2021"),
    ("MAT370",3,"A","Spring 2022"),
    ("MAT480",3,"A-","Fall 2022"),
    ("MAT485",3,"B+","Spring 2023"),
])

print(f"Generated {len([f for f in os.listdir(DIR) if f.endswith('.csv')])} test files in {DIR}")
