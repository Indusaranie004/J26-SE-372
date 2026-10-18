CASES = {
    "2019-03-14-SC-APPEAL-42-2019": {
        "doc_id": "2019-03-14-SC-APPEAL-42-2019",
        "case_num": "SC/APPEAL/42/2019",
        "court": "SC",
        "date": "2019-03-14",
        "lang": "en",
        "in_corpus": True,
        "text_available": True,
        "ocr_required": False,
        "valid_from": "2019-03-14",
        "valid_until": None,
        "validity_status": "good_law",
        "url_pdf": "https://supremecourt.lk/images/pdf/42-2019.pdf",
        "sections": {
            "caption": {
                "text": "SC/APPEAL/42/2019\nCA No. 169/2006\nDC Mawanella No.635/L",
                "char_start": 0,
                "char_end": 180
            },
            "header": {
                "text": "Before: Wanasundara J., Fernando C.J.\nCounsel: A. Perera PC for the Petitioner",
                "char_start": 180,
                "char_end": 1840
            },
            "body": {
                "text": "The Court respectfully distinguished Silva v. Attorney General on its facts.",
                "char_start": 1840,
                "char_end": 54100
            },
            "conclusion": {
                "text": "For the foregoing reasons we hold that the appeal is dismissed.",
                "char_start": 54100,
                "char_end": 58900
            }
        },
        "entities": {
            "judges": [{"name": "Wanasundara J.", "offset": 1902}],
            "counsel": [{"name": "A. Perera PC", "offset": 2100}],
            "acts": [{"act_id": "act-48-1979",
                      "name": "Prevention of Terrorism Act No. 48 of 1979",
                      "section": "12", "offset": 12045}],
            "citations": [
                {"target": "2004-06-11-2-SLR-118",
                 "citation_type": "distinguished",
                 "evidence": "...respectfully distinguished on its facts...",
                 "offset": 18422},
                {"target": "stub-fernando-v-ag-1998",
                 "citation_type": "overruled",
                 "evidence": "...no longer good law...",
                 "offset": 22100}
            ]
        },
        "chain": [
            {"court": "DC", "num": "635/L", "place": "Mawanella", "source": "caption"},
            {"court": "CA", "num": "169/2006", "place": None, "source": "caption"}
        ],
        "provenance": {
            "source_dataset": "nuuuwan/lk_supreme_court_judgements",
            "revision": "a3f9c1e7b2d4e8f0c6a1b3d5e7f9c2a4",
            "extracted_at": "2026-10-07T10:22:00"
        }
    },

    "2004-06-11-2-SLR-118": {
        "doc_id": "2004-06-11-2-SLR-118",
        "case_num": "SC/APPEAL/118/2004",
        "court": "SC",
        "date": "2004-06-11",
        "lang": "en",
        "in_corpus": True,
        "text_available": True,
        "ocr_required": False,
        "valid_from": "2004-06-11",
        "valid_until": None,
        "validity_status": "partially_invalidated",
        "url_pdf": "https://supremecourt.lk/images/pdf/118-2004.pdf",
        "sections": {
            "caption": {"text": "SC/APPEAL/118/2004", "char_start": 0, "char_end": 120},
            "header": {"text": "Before: Fernando C.J., Silva J.S.C.", "char_start": 120, "char_end": 1200},
            "body": {"text": "The Prevention of Terrorism Act No. 48 of 1979 s.12 safeguards apply.", "char_start": 1200, "char_end": 48000},
            "conclusion": {"text": "We hold that Article 13(2) safeguards apply in full.", "char_start": 48000, "char_end": 52000}
        },
        "entities": {
            "judges": [{"name": "Fernando C.J.", "offset": 1300}],
            "counsel": [],
            "acts": [{"act_id": "act-48-1979",
                      "name": "Prevention of Terrorism Act No. 48 of 1979",
                      "section": "12", "offset": 8200}],
            "citations": [
                {"target": "stub-perera-v-silva-2001",
                 "citation_type": "followed",
                 "evidence": "...followed the principle laid down in...",
                 "offset": 15000}
            ]
        },
        "chain": [],
        "provenance": {
            "source_dataset": "nuuuwan/lk_supreme_court_judgements",
            "revision": "a3f9c1e7b2d4e8f0c6a1b3d5e7f9c2a4",
            "extracted_at": "2026-10-07T10:22:00"
        }
    },

    "2024-01-15-SC-FR-7-2023": {
        "doc_id": "2024-01-15-SC-FR-7-2023",
        "case_num": "SC/FR/7/2023",
        "court": "SC",
        "date": "2024-01-15",
        "lang": "en",
        "in_corpus": True,
        "text_available": False,
        "ocr_required": True,
        "valid_from": "2024-01-15",
        "valid_until": None,
        "validity_status": "good_law",
        "url_pdf": "https://supremecourt.lk/images/pdf/fr-7-2023.pdf",
        "sections": {},
        "entities": {},
        "chain": [],
        "provenance": {
            "source_dataset": "nuuuwan/lk_supreme_court_judgements",
            "revision": "a3f9c1e7b2d4e8f0c6a1b3d5e7f9c2a4",
            "extracted_at": "2026-10-07T10:22:00"
        }
    }
}

STUBS = {
    "stub-fernando-v-ag-1998": {
        "doc_id": "stub-fernando-v-ag-1998",
        "case_name": "Fernando v. Attorney General",
        "reporter": "3 SLR 210",
        "year": 1998,
        "court": "SC",
        "in_corpus": False,
        "text_available": False,
        "valid_from": "1998-01-01",
        "valid_until": "2019-03-14",
        "validity_status": "no_longer_good_law",
        "invalidated_by": "2019-03-14-SC-APPEAL-42-2019"
    },
    "stub-perera-v-silva-2001": {
        "doc_id": "stub-perera-v-silva-2001",
        "case_name": "Perera v. Silva",
        "reporter": "1 SLR 44",
        "year": 2001,
        "court": "SC",
        "in_corpus": False,
        "text_available": False,
        "valid_from": "2001-01-01",
        "valid_until": None,
        "validity_status": "good_law",
        "invalidated_by": None
    }
}

CITATIONS = {
    "2019-03-14-SC-APPEAL-42-2019": [
        {
            "target_doc_id": "2004-06-11-2-SLR-118",
            "target_case_num": "SC/APPEAL/118/2004",
            "target_case_name": "Silva v. Attorney General",
            "in_corpus": True,
            "citation_type": "distinguished",
            "effective_date": "2019-03-14",
            "scope": "s.12 detention review only",
            "evidence": "...respectfully distinguished on its facts...",
            "char_offset": 18422
        },
        {
            "target_doc_id": "stub-fernando-v-ag-1998",
            "target_case_num": "3 SLR 210",
            "target_case_name": "Fernando v. Attorney General",
            "in_corpus": False,
            "citation_type": "overruled",
            "effective_date": "2019-03-14",
            "scope": None,
            "evidence": "...held to have been wrongly decided...",
            "char_offset": 22100
        }
    ],
    "2004-06-11-2-SLR-118": [
        {
            "target_doc_id": "stub-perera-v-silva-2001",
            "target_case_num": "1 SLR 44",
            "target_case_name": "Perera v. Silva",
            "in_corpus": False,
            "citation_type": "followed",
            "effective_date": "2004-06-11",
            "scope": None,
            "evidence": "...followed the principle laid down in...",
            "char_offset": 15000
        }
    ],
    "2024-01-15-SC-FR-7-2023": []
}

VALIDITY = {
    "2019-03-14-SC-APPEAL-42-2019": {
        "doc_id": "2019-03-14-SC-APPEAL-42-2019",
        "validity_status": "good_law",
        "valid_from": "2019-03-14",
        "valid_until": None,
        "treatments_received": [],
        "safe_to_cite": True,
        "summary": "No negative treatment recorded. Good law."
    },
    "2004-06-11-2-SLR-118": {
        "doc_id": "2004-06-11-2-SLR-118",
        "validity_status": "partially_invalidated",
        "valid_from": "2004-06-11",
        "valid_until": None,
        "treatments_received": [
            {
                "by": "2019-03-14-SC-APPEAL-42-2019",
                "type": "distinguished",
                "date": "2019-03-14",
                "scope": "s.12 detention review only"
            }
        ],
        "safe_to_cite": True,
        "summary": "Distinguished on s.12 scope only. Good law outside that scope."
    },
    "stub-fernando-v-ag-1998": {
        "doc_id": "stub-fernando-v-ag-1998",
        "validity_status": "no_longer_good_law",
        "valid_from": "1998-01-01",
        "valid_until": "2019-03-14",
        "treatments_received": [
            {
                "by": "2019-03-14-SC-APPEAL-42-2019",
                "type": "overruled",
                "date": "2019-03-14",
                "scope": None
            }
        ],
        "safe_to_cite": False,
        "summary": "Overruled by SC/APPEAL/42/2019 on 14 March 2019. Do not cite."
    }
}

CHAINS = {
    "2019-03-14-SC-APPEAL-42-2019": {
        "doc_id": "2019-03-14-SC-APPEAL-42-2019",
        "chain": [
            {"court": "DC", "num": "635/L", "place": "Mawanella",
             "in_corpus": False, "source": "caption"},
            {"court": "CA", "num": "169/2006", "place": None,
             "in_corpus": False, "source": "caption"},
            {"court": "SC", "num": "SC/APPEAL/42/2019", "place": None,
             "in_corpus": True, "source": "caption"}
        ]
    },
    "2004-06-11-2-SLR-118": {
        "doc_id": "2004-06-11-2-SLR-118",
        "chain": [{"court": "SC", "num": "SC/APPEAL/118/2004",
                   "in_corpus": True, "source": "caption"}]
    },
    "2024-01-15-SC-FR-7-2023": {
        "doc_id": "2024-01-15-SC-FR-7-2023",
        "chain": []
    }
}

SEARCH_RESULTS = {
    "pta detention": [
        {"doc_id": "2019-03-14-SC-APPEAL-42-2019", "score": 0.91,
         "case_num": "SC/APPEAL/42/2019",
         "snippet": "...detention beyond the statutory review period..."},
        {"doc_id": "2004-06-11-2-SLR-118", "score": 0.84,
         "case_num": "SC/APPEAL/118/2004",
         "snippet": "...Article 13(2) safeguards apply in full..."}
    ],
    "wrongful termination": [
        {"doc_id": "2019-03-14-SC-APPEAL-42-2019", "score": 0.72,
         "case_num": "SC/APPEAL/42/2019",
         "snippet": "...employer stated reason scrutinised..."}
    ]
}