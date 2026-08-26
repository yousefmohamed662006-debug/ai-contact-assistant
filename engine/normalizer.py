"""
Arabic Text Normalization & Query Preprocessing Module
Includes intelligent department prefix handling (إدارة، قسم، قطاع، فريق) and prefix stripping.
"""

import re
from typing import List

# 1. Arabic character normalizations
ARABIC_CHAR_MAP = {
    'أ': 'ا', 'إ': 'ا', 'آ': 'ا', 'ٱ': 'ا',
    'ة': 'ه',
    'ى': 'ي', 'ئ': 'ي', 'ؤ': 'و',
    'گ': 'ك', 'پ': 'ب', 'ڤ': 'ف', 'چ': 'ج'
}

TASHKEEL_REGEX = re.compile(r'[\u0617-\u061A\u064B-\u0652]')
TATWEEL_REGEX = re.compile(r'\u0640')

# 2. Comprehensive Department & Domain Keywords (Without generic words like 'ادارة' or 'قسم')
DEPARTMENT_SYNONYMS = {
    "software": [
        "سوفت وير", "سوفتوير", "سوفت", "برمجيات", "برمجه", "برمجة", "مبرمج", "مبرمجين", "مبرمجه",
        "هندسة", "هندسه", "الهندسة", "الهندسه", "هندسة البرمجيات", "مهندس", "مهندسين", "مهندسة",
        "ديفلوبر", "باك اند", "فرونت اند", "موبايل", "تطوير", "كود", "تطبيقات", "اندرويد", "فلاتر", "رياكت",
        "software", "engineering", "dev", "developer", "backend", "frontend", "mobile", "ios", "android", "fullstack"
    ],
    "finance": [
        "حسابات", "الحسابات", "ماليه", "مالية", "المالية", "محاسب", "محاسبين", "فلوس", "مرتبات", "رواتب",
        "رواتب الموظفين", "ميزانيه", "ميزانية", "ضرائب", "ضرايب", "تدقيق", "خزينه", "خزينة", "فواتير", "تكاليف", "تسعير",
        "finance", "accounting", "accountant", "payroll", "budget", "tax", "auditing", "controller", "cost"
    ],
    "hr": [
        "اتش ار", "اتش_ار", "موارد بشريه", "موارد بشرية", "الموارد البشرية", "شؤون عاملين", "شؤون موظفين",
        "توظيف", "تعيينات", "مقابلات", "اجازات", "إجازات", "تأمين طبي", "تامين", "عقود العمل", "تدريب", "تطوير مؤسسي",
        "hr", "human resources", "recruitment", "talent", "hiring", "onboarding", "leaves", "insurance", "training"
    ],
    "it": [
        "اي تي", "اي_تي", "دعم فني", "شبكات", "سيرفرات", "سيرفر", "كمبيوتر", "لابتوب", "طابعات", "طابعة",
        "بنية تحتية", "بنيه تحتيه", "البنية التحتية", "سحابه", "سحابة", "انترنت", "واي فاي", "devops", "cloud", "aws", "لينكس", "linux", "dba",
        "امن سيبراني", "أمن سيبراني", "اختراق", "سايبر سيكيورتي", "سنترال", "تحويلات",
        "it", "information technology", "tech support", "helpdesk", "infra", "infrastructure", "sysadmin", "cybersecurity"
    ],
    "marketing": [
        "تسويق", "التسويق", "ماركتنج", "ماركتينج", "اعلانات", "إعلانات", "حملات", "سوشيال ميديا", "سوشيال",
        "علاقات عامة", "علاقات عامه", "العلاقات العامة", "اعلام", "براند", "صوتيات", "فيديو", "بودكاست", "سيو", "seo",
        "marketing", "social media", "ads", "advertising", "pr", "public relations", "branding", "growth", "seo"
    ],
    "product": [
        "تصميم", "ديزاين", "ديزاينر", "يو اكس", "يو اي", "واجهات", "فيجما", "منتجات", "منتج", "بيزنس انتلجنس", "تحليل بيانات", "power bi",
        "product", "design", "designer", "ui", "ux", "ui/ux", "figma", "prototyping", "data analyst", "bi"
    ],
    "legal": [
        "قانوني", "قانونيه", "قانونية", "الشؤون القانونية", "محامي", "عقود", "اتفاقيات", "شؤون قانونيه", "شؤون قانونية", "امتثال", "مراجعة داخلية", "مراجعه داخليه", "احتيال",
        "legal", "lawyer", "contracts", "compliance", "corporate law", "audit"
    ],
    "executive": [
        "ادارة عليا", "إدارة عليا", "الادارة العليا", "الإدارة العليا", "المكتب التنفيذي", "مكتب تنفيذي", "مجلس ادارة", "مجلس إدارة", "مجلس الادارة", "مجلس الإدارة", "cto", "ceo", "cfo", "coo", "cmo", "رئيس تنفيذي", "سكرتارية", "سكرتاريه", "مستثمرين", "شراكات",
        "executive", "board", "director", "c-level", "management", "assistant", "investor relations", "partnerships"
    ],
    "operations": [
        "عمليات", "العمليات", "تشغيل", "خدمة عملاء", "خدمه عملاء", "عملاء", "شكاوى", "لوجستيات", "مشتريات", "المشتريات", "شراء", "موردين", "مبيعات", "المبيعات", "مبيعات كبار العملاء", "مرافق", "سلامة وصحة",
        "operations", "ops", "customer service", "customer support", "logistics", "procurement", "purchasing", "sales", "facilities", "hse"
    ]
}

# 3. Transliteration Name Pairs
COMMON_NAME_PAIRS = {
    "yousef": ["يوسف", "جوزيف"],
    "ahmed": ["احمد", "أحمد", "إحمد"],
    "yehia": ["يحي", "يحيى", "يحيا"],
    "samir": ["سمير"],
    "mahmoud": ["محمود"],
    "tarek": ["طارق"],
    "sara": ["ساره", "سارة"],
    "mariam": ["مريم", "مريام"],
    "mona": ["مني", "منى"],
    "karim": ["كريم"],
    "omar": ["عمر"],
    "fatma": ["فاطمه", "فاطمة"],
    "ali": ["علي", "على"],
    "hassan": ["حسن"],
    "hoda": ["هدي", "هدى"],
    "ebrahim": ["ابراهيم", "إبراهيم", "دسوقي", "الدسوقي"],
    "mostafa": ["مصطفي", "مصطفى"],
    "khaled": ["خالد"],
    "ziad": ["زياد"],
    "dina": ["دينا"],
    "samia": ["ساميه", "سامية"],
    "hossam": ["حسام"],
    "eman": ["ايمان", "إيمان"],
    "amr": ["عمرو"],
    "yasmine": ["ياسمين"],
    "anas": ["انس", "أنس"],
    "hesham": ["هشام"],
    "belal": ["بلال"],
    "nour": ["نور"],
    "maged": ["ماجد"],
    "basma": ["بسمه", "بسمة"],
    "waleed": ["وليد"],
    "sherif": ["شريف"],
    "gihan": ["جيهان"],
    "tamer": ["تامر"],
    "salma": ["سلمي", "سلمى"],
    "ramy": ["رامي", "رامى"],
    "hend": ["هند"],
    "lojain": ["لجين"],
    "manar": ["منار"],
    "samer": ["سامر"],
    "shorouk": ["شروق"],
    "assem": ["عاصم"],
    "nada": ["ندي", "ندى"]
}


def normalize_arabic(text: str) -> str:
    """Normalizes Arabic text by unifying letters, removing diacritics, and trimming spaces."""
    if not text:
        return ""
    
    text = text.strip().lower()
    text = TASHKEEL_REGEX.sub('', text)
    text = TATWEEL_REGEX.sub('', text)
    
    normalized_chars = [ARABIC_CHAR_MAP.get(ch, ch) for ch in text]
    text = "".join(normalized_chars)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def strip_arabic_prefixes(word: str) -> List[str]:
    """Generates variants of the word stripping common Arabic prefixes (الـ، و، ب، ل)."""
    variants = [word]
    if word.startswith("ال") and len(word) > 3:
        variants.append(word[2:])
    if (word.startswith("وال") or word.startswith("بال") or word.startswith("كال") or word.startswith("فال")) and len(word) > 4:
        variants.append(word[3:])
        variants.append(word[1:])
    if word.startswith("لل") and len(word) > 3:
        variants.append(word[2:])
    return list(set(variants))


def detect_language(text: str) -> str:
    """Detects whether the given text is primarily Arabic ('ar') or English ('en')."""
    if not text:
        return 'ar'
    arabic_chars_count = len(re.findall(r'[\u0600-\u06FF]', text))
    english_chars_count = len(re.findall(r'[a-zA-Z]', text))
    if arabic_chars_count >= english_chars_count:
        return 'ar'
    return 'en'


def extract_department_from_query(query: str) -> tuple[str | None, str | None]:
    """
    Extracts department code and matched synonym from query.
    Handles department prefixes like 'ادارة الحسابات' -> ('finance', 'حسابات').
    """
    norm_q = normalize_arabic(query)
    
    # Strip generic department words from query for extraction
    clean_q = norm_q
    generic_dept_prefixes = ["اداره ", "إدارة ", "الاداره ", "الإدارة ", "قسم ", "القسم ", "قطاع ", "القطاع ", "فريق ", "الفريق ", "department of ", "team of "]
    for g in generic_dept_prefixes:
        if clean_q.startswith(g):
            clean_q = clean_q[len(g):].strip()
        clean_q = clean_q.replace(f" {g}", " ").strip()

    for dept_code, synonyms in DEPARTMENT_SYNONYMS.items():
        for syn in synonyms:
            norm_syn = normalize_arabic(syn)
            syn_variants = strip_arabic_prefixes(norm_syn)
            
            # Test against clean_q and norm_q
            for target_q in [clean_q, norm_q]:
                if target_q == norm_syn or any(target_q == v for v in syn_variants):
                    return dept_code, syn
                
                if f" {norm_syn} " in f" {target_q} " or target_q.startswith(norm_syn + " ") or target_q.endswith(" " + norm_syn):
                    return dept_code, syn

                for v in syn_variants:
                    if f" {v} " in f" {target_q} " or target_q.startswith(v + " ") or target_q.endswith(" " + v):
                        return dept_code, syn
                
    return None, None


def transliterate_name(word: str) -> str:
    """Returns English transliterated version of an Arabic name if found in the dictionary."""
    norm_w = normalize_arabic(word)
    for en_name, ar_variants in COMMON_NAME_PAIRS.items():
        for ar_v in ar_variants:
            if norm_w == normalize_arabic(ar_v) or any(v == normalize_arabic(ar_v) for v in strip_arabic_prefixes(norm_w)):
                return en_name
    return word
