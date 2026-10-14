from datetime import date

from app.models.enums import ContactType, VerificationStatus

CHECKED_ON = date(2026, 10, 14)

BMC_SITE = "https://www.mcgm.gov.in"
BMC_HELPLINE_SOURCE = "https://portal.mcgm.gov.in"
ADANI_SITE = "https://www.adanielectricity.com"
IITB_SITE = "https://www.iitb.ac.in"
IITB_SUPPORT = "https://support.iitb.ac.in/support/login.jsp"
IITB_CAMPUS_SOURCE = "https://www.openstreetmap.org/relation/8546708"
IITB_AREA_NAME = "IIT Bombay campus, Powai"

V = VerificationStatus.VERIFIED
U = VerificationStatus.UNVERIFIED


def iitb_contacts():
    return [
        (ContactType.WEBSITE, IITB_SITE, IITB_SITE, CHECKED_ON, V),
        (ContactType.COMPLAINT_PORTAL, IITB_SUPPORT, IITB_SUPPORT, CHECKED_ON, V),
    ]


def bmc_contacts():
    return [
        (ContactType.HELPLINE, "1916", BMC_HELPLINE_SOURCE, None, U),
        (ContactType.WEBSITE, BMC_SITE, BMC_SITE, CHECKED_ON, V),
    ]


# department name -> authorities responsible for it across the city
AUTHORITIES = {
    "Roads / Public Works": [
        ("BMC Roads Department", "Mumbai", bmc_contacts()),
        ("IIT Bombay Civil Maintenance", IITB_AREA_NAME, iitb_contacts()),
    ],
    "Drainage / Sewerage": [
        ("BMC Storm Water Drains and Sewerage Departments", "Mumbai", bmc_contacts()),
    ],
    "Water Supply": [
        ("BMC Hydraulic Engineer's Department", "Mumbai", bmc_contacts()),
    ],
    "Sanitation / Solid Waste": [
        ("BMC Solid Waste Management Department", "Mumbai", bmc_contacts()),
        ("IIT Bombay Public Health Office", IITB_AREA_NAME, iitb_contacts()),
    ],
    "Electricity": [
        (
            "Adani Electricity Mumbai Limited",
            "Powai, Mumbai",
            [
                (ContactType.HELPLINE, "19122", ADANI_SITE, None, U),
                (
                    ContactType.EMAIL,
                    "helpdesk.mumbaielectricity@adani.com",
                    ADANI_SITE,
                    None,
                    U,
                ),
                (ContactType.WEBSITE, ADANI_SITE, ADANI_SITE, CHECKED_ON, V),
                (
                    ContactType.LOCAL_OFFICE,
                    "Andheri Kurla Rd, Sakinaka Junction, Andheri (E), Mumbai 400072",
                    ADANI_SITE,
                    None,
                    U,
                ),
            ],
        ),
        ("IIT Bombay Electrical Maintenance", IITB_AREA_NAME, iitb_contacts()),
    ],
    "General Grievance": [
        ("Brihanmumbai Municipal Corporation", "Mumbai", bmc_contacts()),
        (
            "IIT Bombay Campus Administration",
            IITB_AREA_NAME,
            iitb_contacts()
            + [(ContactType.HELPLINE, "+91 22 2572 2545", IITB_CAMPUS_SOURCE, None, U)],
        ),
    ],
}

# authority name, label, geojson file in this folder, priority, source, status
# priority: 0 citywide default, 10 ward, 20 special bodies such as a campus
AREAS = [
    (name, "IIT Bombay campus", "iitb_campus.geojson", 20, IITB_CAMPUS_SOURCE, U)
    for name in (
        "IIT Bombay Civil Maintenance",
        "IIT Bombay Public Health Office",
        "IIT Bombay Electrical Maintenance",
        "IIT Bombay Campus Administration",
    )
]

# domain, url, department name or None, authority name or None
SOURCES = [
    ("mcgm.gov.in", BMC_SITE, None, "Brihanmumbai Municipal Corporation"),
    (
        "portal.mcgm.gov.in",
        BMC_HELPLINE_SOURCE,
        None,
        "Brihanmumbai Municipal Corporation",
    ),
    (
        "adanielectricity.com",
        ADANI_SITE,
        "Electricity",
        "Adani Electricity Mumbai Limited",
    ),
    ("iitb.ac.in", IITB_SITE, None, "IIT Bombay Campus Administration"),
    (
        "support.iitb.ac.in",
        IITB_SUPPORT,
        None,
        "IIT Bombay Campus Administration",
    ),
]
