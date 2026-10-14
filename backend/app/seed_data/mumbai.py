from datetime import date

from app.models.enums import ContactType, VerificationStatus

CHECKED_ON = date(2026, 10, 14)

BMC_SITE = "https://www.mcgm.gov.in"
BMC_HELPLINE_SOURCE = "https://portal.mcgm.gov.in"
ADANI_SITE = "https://www.adanielectricity.com"

V = VerificationStatus.VERIFIED
U = VerificationStatus.UNVERIFIED


def bmc_contacts():
    return [
        (ContactType.HELPLINE, "1916", BMC_HELPLINE_SOURCE, None, U),
        (ContactType.WEBSITE, BMC_SITE, BMC_SITE, CHECKED_ON, V),
    ]


# department name -> authorities responsible for it across the city
AUTHORITIES = {
    "Roads / Public Works": [
        ("BMC Roads Department", "Mumbai", bmc_contacts()),
    ],
    "Drainage / Sewerage": [
        ("BMC Storm Water Drains and Sewerage Departments", "Mumbai", bmc_contacts()),
    ],
    "Water Supply": [
        ("BMC Hydraulic Engineer's Department", "Mumbai", bmc_contacts()),
    ],
    "Sanitation / Solid Waste": [
        ("BMC Solid Waste Management Department", "Mumbai", bmc_contacts()),
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
    ],
    "General Grievance": [
        ("Brihanmumbai Municipal Corporation", "Mumbai", bmc_contacts()),
    ],
}

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
]
