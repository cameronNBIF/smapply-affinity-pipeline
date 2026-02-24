# config.py
AFFINITY_IVF_LIST_ID = "339266"

FIELD_MAPPING = {
    # MANDATORY: The hidden anchor for duplicate checking
    'SMApply_ID': {'field_id': 'field-5592720', 'type': 'number'}, 
    
    # Text Fields (Ensure RefNum and Fiscal Year are set to 'Text' in Affinity)
    'RefNum': {'field_id': 'field-5594972', 'type': 'text'}, 
    'CurrentStage': {'field_id': 'field-5592487', 'type': 'text'},
    'FiscalYear': {'field_id': 'field-5594978', 'type': 'text'},
    'ApplTitle': {'field_id': 'field-5592700', 'type': 'text'},
    'ExecSum': {'field_id': 'field-5592493', 'type': 'text'},
    'NBIFSectorID': {'field_id': 'field-5592623', 'type': 'text'},
    'AwardResult': {'field_id': 'field-5592628', 'type': 'text'},
    'Application_ID': {'field_id': 'field-5596491', 'type': 'text'},

    
    # Currency / Number Fields
    'AmtRqstd': {'field_id': 'field-5592495', 'type': 'number'},
    'AmtAwarded': {'field_id': 'field-5592629', 'type': 'number'},
    
    # Date/Time Fields
    'ApplDate': {'field_id': 'field-5592490', 'type': 'datetime'},
    'DateStart': {'field_id': 'field-5592626', 'type': 'datetime'},
    'AnticipatedCompletionDate': {'field_id': 'field-5592627', 'type': 'datetime'},
    'IncorporationDate': {'field_id': 'field-5592635', 'type': 'datetime'},

    'LocationPayload': {'field_id': 'field-5592634', 'type': 'location'},

    'Company_Entity_ID': {'field_id': 'field-5592625', 'type': 'company'},
    'PI_Entity_ID': {'field_id': 'field-5592624', 'type': 'person'},
    'Contact_Entity_ID': {'field_id': 'field-5592633', 'type': 'person'},
}

NUMERIC_COLUMNS = ['FedLeverage', 'OtherLeverage', 'FTE', 'PTE']

SECTOR_MAPPING = {
    "Environment & Agriculture - Select Sector": [
        "Environmental Technology & Resource Management",
        "Fisheries & Marine Sciences",
        "Agriculture, Forestry, Food & Beverage"
    ],
    "Information Technology - Select Sector": [
        "ICT",
        "Energy & Electronics",
        "Manufacturing & Materials",
        "Aerospace & Defense",
        "Precision Sciences"
    ],
    "BioScience and Health - Select Sector": [
        "Bioscience & Biotechnology",
        "Health & Medicine"
    ],
    "Business Operations - Select Sector": [
        "Statistics & Data Analytics",
        "Finance, Economics & Business Sciences",
        "Consumer Goods & Services",
        "Media, Tourism & Entertainment"
    ],
    "Social Sciences - Select Sector": [
        "Social Sciences & Humanities, Psychology"
    ]
}

CITY_TO_REGION_MAPPING = {
    "Fredericton": "SW",
    "Moncton": "SE",
    "Saint John": "SW",
    "Bathurst": "NE",
    "Campbellton": "NE",
    "Miramichi": "NE",
    "Edmundston": "NW",
    "Caraquet": "NE",
    "Shippagan": "NE",
    "Dieppe": "SE",
    "Riverview": "SE",
    "Tracadie-Sheila": "NE",
    "Sackville": "SE",
    "St. Stephen": "SW",
    "Sussex": "SE",
    "Quispamsis": "SW",
    "Rothesay": "SW",
    "Hanwell": "SW",
    "Clair": "NW",
    "St. Andrews": "SW",
}

PROVINCE_MAPPING = {
    0: "AB",
    1: "BC",
    2: "MB",
    3: "NB",
    4: "NL",
    5: "NT",
    6: "NS",
    7: "NU",
    8: "ON",
    9: "PE",
    10: "QC",
    11: "SK",
    12: "YK"
}

TABLE_CONFIGS = {
    'staging.Investment': {
        'unique_column': 'RefNum',
        'filter_column': 'ResearchFundID',
        'columns': [
            'RefNum', 'ApplTitle', 'ExecSum', 'FiscalYear', 'ResearchFundID',
            'ApplDate', 'DecisionDate', 'AmtRqstd', 'AmtAwarded', 'TotalLevAmt',
            'PrivSectorLev', 'FedLeverage', 'OtherLeverage', 'FTE', 'PTE',
            'NBIFSectorID', 'Notes', 'BatchID', 'LoadedAt'
        ]
    },
    'staging.VoucherCompany': {
        'unique_column': 'CompanyName',
        'filter_column': None,
        'columns': [
            'CompanyName', 'Address', 'City', 'Province',
            'PostalCode', 'Country', 'Region', 'IncorporationDate',
            'BatchID', 'LoadedAt'
        ]
    }
    ,
    'staging.PeopleInfo': {
        'unique_column': 'Email',
        'filter_column': None,
        'columns': [
            'LastName', 'FirstName', 'Email', 'Phone', 
            'Note', 'CommOptOut', 'BatchID', 'LoadedAt'
        ]
    }
}

YEARS = [
    "2026",
    "2025",
    "2024",
    "2023-2024",
    "2022-2023",
    "2021-2022",
    "2020-2021",
    "2019-2020",
    "2018-2019",
    "2017-2018",
    "2016-2017",
    "2015-2016",
    "2014-2015",
    "2013-2014",
    "2012-2013",
    "2011-2012"
]

REGIONS = [
    "SW",
    "SE",
    "NW",
    "NE"
]

STATE_FILE = "sync_state.json"