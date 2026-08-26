"""
Universal Enterprise Contact Search & Matching Engine
Intelligent fuzzy matching, typo tolerance, compound filtering, and full-field inverted indexing.
"""

import os
import json
import re
from typing import Dict, Any, List, Optional
from rapidfuzz import fuzz
from .normalizer import normalize_arabic, detect_language, DEPARTMENT_SYNONYMS, COMMON_NAME_PAIRS, strip_arabic_prefixes, transliterate_name

DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "contacts.json")

# Comprehensive filler words, verbs, and intent indicators
RAW_STOP_WORDS = {
    "مين", "عايز", "عاوز", "ابحث", "هاتلي", "جبلي", "فين", "مكان", "رقم", "تليفون",
    "ايميل", "المهندس", "الدكتور", "الاستاذ", "زميل", "اللى", "اللي", "في", "فى", "بتاع",
    # Work & Presence verbs/participles
    "شغال", "شغالة", "شغاله", "شغالين", "الشغالين", "بيشتغل", "بتشتغل", "بيشتغلوا", "بيشتغلو",
    "يعمل", "تعمل", "يعملون", "عامل", "عاملة", "عاملين", "العاملين",
    "موجود", "موجودة", "موجوده", "موجودين", "الموجودين", "متواجد", "متواجدين", "المتواجدين",
    "فيه", "فيها", "فيهم", "منهم", "عنده", "عندهم", "ضمن",
    # Roles & Team words
    "مسؤول", "مسؤولة", "مسئول", "مسئولة", "مسؤولين", "مسئولين", "ماسك", "ماسكة", "ماسكين", "مسك",
    "رئيس", "قائد", "ليدر", "مدير", "مديرين", "طاقم", "كوادر", "كادر", "افراد", "الافراد", "الأفراد",
    "ادارة", "اداره", "الادارة", "الإدارة", "ادراه", "الادراه", "قسم", "القسم", "قطاع", "القطاع", "فريق", "الفريق", "شعبة", "وحدة",
    "موظف", "موظفة", "موظفه", "موظفين", "الموظفين", "موظفي", "ناس", "الناس", "اعضاء", "الأعضاء", "شخص", "اشخاص", "كل", "جميع",
    "هات", "وريني", "طلعلي", "اريد", "بحث", "عرض", "دليل", "عن", "من", "مع",
    "find", "who", "is", "where", "search", "get", "contact", "give", "me", "show", "the", "in", "at", "for",
    "department", "dept", "team", "staff", "employees", "employee", "people", "all", "list", "lead", "head", "manager",
    "working", "works", "work"
}

NORMALIZED_STOP_WORDS = {normalize_arabic(w) for w in RAW_STOP_WORDS} | RAW_STOP_WORDS


def is_stop_word(word: str) -> bool:
    """Returns True if the word is a generic filler stop-word."""
    norm_w = normalize_arabic(word)
    if norm_w in NORMALIZED_STOP_WORDS or word in NORMALIZED_STOP_WORDS:
        return True
    variants = strip_arabic_prefixes(norm_w)
    return any(v in NORMALIZED_STOP_WORDS for v in variants)


class ContactMatcher:
    def __init__(self, data_path: str = DATA_PATH):
        self.data_path = data_path
        self.contacts: List[Dict[str, Any]] = []
        self.load_data()

    def load_data(self):
        """Loads employee records from JSON file."""
        if os.path.exists(self.data_path):
            with open(self.data_path, "r", encoding="utf-8") as f:
                self.contacts = json.load(f)
        else:
            self.contacts = []

    def get_all_contacts(self, lang: str = "ar") -> List[Dict[str, Any]]:
        """Returns formatted list of all contacts for directory view."""
        return [self._format_contact(c, lang) for c in self.contacts]

    def _format_contact(self, c: Dict[str, Any], lang: str) -> Dict[str, Any]:
        """Formats a single contact for the desired language view."""
        is_ar = (lang == "ar")
        return {
            "id": c["id"],
            "name": c["name_ar"] if is_ar else c["name_en"],
            "role": c["role_ar"] if is_ar else c["role_en"],
            "department": c["department_ar"] if is_ar else c["department_en"],
            "department_code": c.get("department_code", "general"),
            "email": c["email"],
            "phone": c["phone"],
            "extension": c["extension"],
            "building": c["building"],
            "floor": c["floor_ar"] if is_ar else c["floor_en"],
            "manager_name": c["manager_name_ar"] if is_ar else c["manager_name_en"],
            "responsibilities": c["responsibilities_ar"] if is_ar else c["responsibilities_en"],
            "avatar_color": c.get("avatar_color", "#2563EB"),
            "avatar_initials": c.get("avatar_initials", "EM")
        }

    def _detect_department(self, norm_query: str) -> tuple[Optional[str], List[str]]:
        """
        Intelligently identifies department mention with fuzzy typo tolerance.
        Handles typos like 'الادراه الماليه', 'اداره السوفت وير', 'الحسابات'.
        """
        q_words = norm_query.split()

        # Multi-word exact / substring check
        for dept_code, synonyms in DEPARTMENT_SYNONYMS.items():
            for syn in synonyms:
                norm_syn = normalize_arabic(syn)
                syn_words = norm_syn.split()
                if len(syn_words) > 1 and norm_syn in norm_query:
                    return dept_code, syn_words

        # Token check with prefix & typo tolerance
        for word in q_words:
            if is_stop_word(word):
                continue
            w_variants = strip_arabic_prefixes(word)
            for dept_code, synonyms in DEPARTMENT_SYNONYMS.items():
                for syn in synonyms:
                    norm_syn = normalize_arabic(syn)
                    syn_variants = strip_arabic_prefixes(norm_syn)
                    for wv in w_variants:
                        for sv in syn_variants:
                            if wv == sv or (len(wv) >= 4 and fuzz.ratio(wv, sv) >= 85):
                                return dept_code, [word]

        return None, []

    def search(self, query: str) -> Dict[str, Any]:
        """
        Universal, resilient search engine:
        - Fuzzy typo tolerance ('يحيا' -> 'يحيى', 'الادراه الماليه' -> 'المالية والحسابات').
        - Colloquial queries ('مين اللي شغالين في السوفت وير', 'اللي شغالين في السوفت وير').
        - Common name queries ('علي', 'أحمد', 'يوسف').
        - Compound intersection ('أحمد في السوفت وير').
        - Graceful department team fallback.
        """
        raw_query = query.strip()
        lang = detect_language(raw_query)
        norm_query = normalize_arabic(raw_query)
        query_words = norm_query.split()

        if not query_words:
            return {"status": "none", "matches": [], "query": raw_query, "language": lang}

        # 1. Detect Department & matched tokens
        dept_code, dept_matched_tokens = self._detect_department(norm_query)

        # 2. Detect Building & Floor Filters
        building_filter = None
        if "مبنى a" in norm_query or "مبني a" in norm_query or "building a" in raw_query.lower() or "مبنى ا" in norm_query:
            building_filter = "A"
        elif "مبنى b" in norm_query or "مبني b" in norm_query or "building b" in raw_query.lower() or "مبنى ب" in norm_query:
            building_filter = "B"

        floor_filter = None
        if "ارضي" in norm_query or "ground" in raw_query.lower():
            floor_filter = "أرضي"
        elif "اول" in norm_query or "1st" in raw_query.lower() or "الاول" in norm_query:
            floor_filter = "الأول"
        elif "تاني" in norm_query or "ثاني" in norm_query or "2nd" in raw_query.lower() or "الثاني" in norm_query:
            floor_filter = "الثاني"

        # 3. Extract pure search terms (excluding stop words and department tokens)
        name_words = []
        for w in query_words:
            if is_stop_word(w) or w in dept_matched_tokens or any(d in w for d in dept_matched_tokens):
                continue
            if w in ["مبنى", "مبني", "دور", "طابق", "a", "b", "ارضي", "اول", "تاني", "ثاني"]:
                continue
            if len(w) >= 2:
                name_words.append(w)

        # 4. Filter Candidate Pool (Intersection Filtering)
        candidate_pool = self.contacts
        dept_only_pool = []

        if dept_code:
            dept_matches = [c for c in candidate_pool if c.get("department_code") == dept_code]
            if dept_matches:
                candidate_pool = dept_matches
                dept_only_pool = dept_matches

        if building_filter:
            b_matches = [c for c in candidate_pool if c.get("building") == building_filter]
            if b_matches:
                candidate_pool = b_matches

        if floor_filter:
            f_matches = [c for c in candidate_pool if floor_filter in c.get("floor_ar", "") or floor_filter in c.get("floor_en", "")]
            if f_matches:
                candidate_pool = f_matches

        # 5. Score Candidates
        scored_contacts = []
        name_query_joined = " ".join(name_words)

        for c in candidate_pool:
            score = 0
            norm_name_ar = normalize_arabic(c["name_ar"])
            norm_name_en = c["name_en"].lower()
            role_ar = normalize_arabic(c["role_ar"])
            role_en = c["role_en"].lower()
            dept_ar = normalize_arabic(c["department_ar"])
            dept_en = c["department_en"].lower()
            email = c["email"].lower()
            phone = c["phone"]
            ext = c["extension"]
            manager_ar = normalize_arabic(c["manager_name_ar"])
            manager_en = c["manager_name_en"].lower()
            resp_ar = " ".join([normalize_arabic(r) for r in c.get("responsibilities_ar", [])])
            resp_en = " ".join([r.lower() for r in c.get("responsibilities_en", [])])

            # A) If specific name/role words exist, score them
            if name_words:
                first_name_ar = norm_name_ar.split()[0] if norm_name_ar.split() else ""
                first_name_en = norm_name_en.split()[0] if norm_name_en.split() else ""

                for nw in name_words:
                    nw_variants = strip_arabic_prefixes(nw)
                    for nwv in nw_variants:
                        trans_nw = transliterate_name(nwv)

                        # Exact first name / full name
                        if nwv == first_name_ar or trans_nw == first_name_en or nwv == norm_name_ar:
                            score += 100
                        elif nwv in norm_name_ar.split() or trans_nw in norm_name_en.split():
                            score += 90
                        else:
                            # Fuzzy name match with high tolerance
                            ratio_ar = fuzz.partial_ratio(nwv, norm_name_ar)
                            ratio_en = fuzz.partial_ratio(trans_nw, norm_name_en)
                            max_ratio = max(ratio_ar, ratio_en)
                            if max_ratio >= 75:
                                score += (max_ratio * 0.8)

                        # Role / title match
                        if nwv in role_ar or trans_nw in role_en:
                            score += 80
                        elif fuzz.partial_ratio(nwv, role_ar) >= 80:
                            score += 65

                        # Skills / Responsibilities
                        if nwv in resp_ar or trans_nw in resp_en:
                            score += 65

                        # Manager
                        if nwv in manager_ar or trans_nw in manager_en:
                            score += 50

                if name_query_joined:
                    full_ratio = max(
                        fuzz.token_set_ratio(name_query_joined, norm_name_ar),
                        fuzz.token_set_ratio(name_query_joined, norm_name_en)
                    )
                    if full_ratio >= 70:
                        score += (full_ratio * 0.5)

            elif dept_code or building_filter or floor_filter:
                # Pure department / location search (e.g. 'الاداره الماليه', 'سوفت وير', 'مين شغالين في السوفت وير')
                score = 150
            else:
                # Direct general fallback search across all fields
                for w in query_words:
                    if is_stop_word(w):
                        continue
                    w_variants = strip_arabic_prefixes(w)
                    for wv in w_variants:
                        trans_w = transliterate_name(wv)
                        if wv in norm_name_ar or trans_w in norm_name_en:
                            score += 90
                        if wv in role_ar or trans_w in role_en:
                            score += 80
                        if wv in dept_ar or trans_w in dept_en:
                            score += 75
                        if wv in resp_ar or trans_w in resp_en:
                            score += 70
                        if wv in email:
                            score += 90

            # Phone / Extension match
            for w in query_words:
                if w.isdigit():
                    if w == ext:
                        score += 200
                    elif w in phone:
                        score += 150

            # Email match
            if "@" in raw_query and raw_query.lower() in email:
                score += 200

            if score >= 40:
                scored_contacts.append((score, c))

        # Sort results by score descending
        scored_contacts.sort(key=lambda x: x[0], reverse=True)

        # 6. Graceful Department Fallback
        # If user specified a department, but name_words matched 0 people (e.g. slang filler words), return the department team!
        if not scored_contacts and dept_only_pool:
            matched_candidates = dept_only_pool[:8]
            formatted_matches = [self._format_contact(c, lang) for c in matched_candidates]
            return {
                "status": "multiple" if len(formatted_matches) > 1 else "single",
                "matches": formatted_matches,
                "query": raw_query,
                "language": lang
            }

        if not scored_contacts:
            return {
                "status": "none",
                "matches": [],
                "query": raw_query,
                "language": lang
            }

        top_score = scored_contacts[0][0]
        # Return top candidates within reasonable margin
        matched_candidates = [c for s, c in scored_contacts if s >= (top_score - 55)][:8]
        formatted_matches = [self._format_contact(c, lang) for c in matched_candidates]

        status = "single" if len(formatted_matches) == 1 else "multiple"

        return {
            "status": status,
            "matches": formatted_matches,
            "query": raw_query,
            "language": lang
        }
