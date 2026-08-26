"""
AI Agent Orchestrator & Conversational Layer
Executive VIP persona with dynamic, natural linguistic variation.
Ultra-crisp 1-sentence dynamic headers powered by active 2026 Google Gemini models
with zero-API deterministic local fallback.
"""

import os
import json
import re
from typing import Dict, Any, List, Optional
import requests
from .matcher import ContactMatcher
from .normalizer import detect_language, normalize_arabic

KEY_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "gemini_key.txt")

# Verified ultra-fast, high-completion active 2026 models in priority order
ACTIVE_MODELS = [
    "models/gemini-3.5-flash-lite",
    "models/gemini-3.1-flash-lite",
    "models/gemini-flash-lite-latest",
    "models/gemini-3.5-flash",
    "models/gemini-flash-latest"
]


class ContactAIAgent:
    def __init__(self, api_key: Optional[str] = None):
        self.matcher = ContactMatcher()
        self.api_key = api_key or self._load_saved_key() or os.getenv("GEMINI_API_KEY")
        self.force_mode = "offline"

    def _load_saved_key(self) -> Optional[str]:
        """Loads persistently saved API key from file if exists."""
        if os.path.exists(KEY_FILE):
            try:
                with open(KEY_FILE, "r", encoding="utf-8") as f:
                    k = f.read().strip().replace('"', '').replace("'", "")
                    return k if k else None
            except Exception:
                return None
        return None

    def set_api_key(self, api_key: str):
        """Updates and persists the Gemini API key."""
        clean_key = api_key.strip().replace('"', '').replace("'", "")
        self.api_key = clean_key
        try:
            with open(KEY_FILE, "w", encoding="utf-8") as f:
                f.write(clean_key)
        except Exception:
            pass

    def set_mode(self, mode: str):
        """Sets operating mode: 'online' or 'offline'."""
        self.force_mode = mode

    def process_query(self, user_query: str, mode: Optional[str] = None) -> Dict[str, Any]:
        """
        Processes user query:
        - If Online: Generates dynamic, varied, crisp 1-sentence headers.
        - If Offline: Fast, deterministic local fallback engine.
        """
        query_text = user_query.strip()
        lang = detect_language(query_text)
        norm_query = normalize_arabic(query_text)
        active_mode = mode or self.force_mode

        # =========================================================================
        # 1. CONVERSATIONAL INTENTS (Greetings, Thanks, How-To)
        # =========================================================================

        # A) Greetings
        greetings_ar = [
            "ازيك", "عامل ايه", "اخبارك", "ازي حضرتك", "شلونك", "كويس", "تمام",
            "اهلا", "أهلا", "مرحبا", "مرحباً", "السلام عليكم", "صباح الخير", "مساء الخير",
            "هاي", "الو", "هلا", "يا هلا", "مساء الورد", "صباح النور", "اهلا بيك", "أهلاً بك"
        ]
        greetings_en = ["hi", "hello", "hey", "good morning", "good evening", "how are you", "how are u", "what's up"]

        is_greeting = (
            any(norm_query == g or norm_query.startswith(g + " ") or norm_query.endswith(" " + g) for g in greetings_ar) or
            any(query_text.lower() == g or query_text.lower().startswith(g + " ") for g in greetings_en)
        )

        if is_greeting and len(norm_query.split()) <= 4:
            if active_mode == "online" and self.api_key:
                gemini_res = self._call_gemini_general(query_text, lang)
                if gemini_res:
                    return {
                        "reply": f"🌐 **[Gemini AI]:**\n\n{gemini_res}",
                        "language": lang,
                        "status": "greeting",
                        "contacts": [],
                        "engine_mode": "gemini_online",
                        "failover": False
                    }

            return {
                "reply": "أهلاً بحضرتك يا فندم! 👋 أنا المساعد الذكي لدليل موظفي الشركة، في خدمتكم دائماً لتيسير الوصول لأي موظف أو إدارة.",
                "language": lang,
                "status": "greeting",
                "contacts": [],
                "engine_mode": "local_offline",
                "failover": False
            }

        # B) Thanks / Gratitude
        thanks_ar = [
            "شكرا", "شكراً", "شكرا ليك", "شكرا جزيلا", "تسلم", "تسلم ايدك", "الله يخليك",
            "الف شكر", "ألف شكر", "كلك ذوق", "يعطيك العافيه", "يعطيك العافية",
            "مع السلامه", "مع السلامة", "باي", "سلام", "في رعاية الله", "حبيبي"
        ]
        thanks_en = ["thank you", "thanks", "thanks a lot", "thank u", "great", "awesome", "perfect", "bye", "goodbye", "see you"]

        is_thanks = (
            any(norm_query == t or norm_query.startswith(t + " ") or norm_query.endswith(" " + t) for t in thanks_ar) or
            any(query_text.lower() == t or query_text.lower().startswith(t + " ") for t in thanks_en)
        )

        if is_thanks and len(norm_query.split()) <= 3:
            if active_mode == "online" and self.api_key:
                gemini_res = self._call_gemini_general(query_text, lang)
                if gemini_res:
                    return {
                        "reply": f"🌐 **[Gemini AI]:**\n\n{gemini_res}",
                        "language": lang,
                        "status": "greeting",
                        "contacts": [],
                        "engine_mode": "gemini_online",
                        "failover": False
                    }

            return {
                "reply": "العفو يا فندم، دائماً في خدمتكم في أي وقت للاستعلام عن أي موظف أو قسم. 🤝",
                "language": lang,
                "status": "greeting",
                "contacts": [],
                "engine_mode": "local_offline",
                "failover": False
            }

        # C) Help Intent
        help_ar = [
            "ازاي", "ازاي يعني", "يعني ايه", "يعني", "شغال ازاي", "بتعمل ايه", "بتشتغل ازاي",
            "طريقة الاستخدام", "ساعدني", "اشرحلي", "فهمني", "مين انت", "بتعرف تعمل ايه", "كيف", "كيفية الاستخدام", "ايه ده"
        ]
        help_en = ["how", "how to use", "what do you do", "what can you do", "help", "who are you", "explain"]

        is_help = (
            any(norm_query == h or norm_query.startswith(h + " ") or norm_query.endswith(" " + h) for h in help_ar) or
            any(query_text.lower() == h or query_text.lower().startswith(h + " ") for h in help_en)
        )

        if is_help:
            return {
                "reply": (
                    "أهلاً بحضرتك يا فندم! 💡\n\n"
                    "أنا **المساعد الذكي لدليل موظفي الشركة**، ومهمتي تيسير الوصول السريع لكافة بيانات التواصل والوظائف.\n\n"
                    "**يمكنك البحث بعدة طرق:**\n"
                    "• **بالإدارة أو القسم:** *(الإدارة المالية - إدارة السوفت وير - إدارة المبيعات)*\n"
                    "• **بالاسم والوظيفة:** *(أحمد في السوفت وير - علي في الواجهات)*\n"
                    "• **بالموقع والمبنى:** *(مين في مبنى A الدور الثاني؟)*\n"
                    "• **بالأمر الصوتي 🎙️:** الضغط على زر الميكروفون والتحدث مباشرة."
                ),
                "language": lang,
                "status": "greeting",
                "contacts": [],
                "engine_mode": "local_offline",
                "failover": False
            }

        # =========================================================================
        # 2. CONTACT SEARCH (Retrieval Phase)
        # =========================================================================
        search_result = self.matcher.search(query_text)
        status = search_result["status"]
        contacts = search_result["matches"]

        # =========================================================================
        # 3. ONLINE (GEMINI LLM) VS OFFLINE (LOCAL ENGINE)
        # =========================================================================
        if active_mode == "online":
            if self.api_key:
                try:
                    gemini_reply = self._call_gemini_contacts(query_text, contacts, status, lang)
                    if gemini_reply:
                        return {
                            "reply": f"🌐 **[Gemini AI]:**\n\n{gemini_reply}",
                            "language": lang,
                            "status": status,
                            "contacts": contacts,
                            "engine_mode": "gemini_online",
                            "failover": False
                        }
                except Exception as e:
                    print(f"❌ [Gemini Error]: {e}")

                # If all online attempts fail, graceful fallback
                local_reply = self._generate_local_reply(query_text, contacts, status, lang)
                return {
                    "reply": f"⚠️ **[تحويل تلقائي للأوفلاين]:** تم استخراج البيانات محلياً:\n\n{local_reply}",
                    "language": lang,
                    "status": status,
                    "contacts": contacts,
                    "engine_mode": "local_offline",
                    "failover": True
                }
            else:
                local_reply = self._generate_local_reply(query_text, contacts, status, lang)
                return {
                    "reply": f"⚙️ **[وضع الأونلاين يحتاج API Key]:** يرجى إدخال المفتاح من الإعدادات ⚙️.\n\n{local_reply}",
                    "language": lang,
                    "status": status,
                    "contacts": contacts,
                    "engine_mode": "local_offline",
                    "failover": True
                }

        # Offline Local Result (Deterministic Template)
        local_reply = self._generate_local_reply(query_text, contacts, status, lang)
        return {
            "reply": local_reply,
            "language": lang,
            "status": status,
            "contacts": contacts,
            "engine_mode": "local_offline",
            "failover": False
        }

    def _generate_local_reply(self, query: str, contacts: List[Dict[str, Any]], status: str, lang: str) -> str:
        """Deterministic, formal executive template for zero-API local mode."""
        is_ar = (lang == "ar")

        if status == "single":
            c = contacts[0]
            if is_ar:
                return f"إليكم بيانات التواصل الخاصة بالموظف **{c['name']}** ({c['role']} - {c['department']}):"
            else:
                return f"Here are the contact details for **{c['name']}** ({c['role']} - {c['department']}):"

        elif status == "multiple":
            count = len(contacts)
            if is_ar:
                return f"تم العثور على **{count} موظفين** يطابقون مواصفات البحث، يرجى التفضل باختيار الموظف المطلوب من الكروت أدناه:"
            else:
                return f"Found **{count} employees** matching your criteria, please select a profile below to view details:"

        else: # none
            if is_ar:
                return "عذراً يا فندم، لم يتم العثور على أي موظف يطابق معايير هذا البحث في قاعدة البيانات. يمكنكم البحث بالاسم، أو الإدارة، أو المسمى الوظيفي."
            else:
                return "Sorry, no employee was found matching your search criteria in the directory. You may try searching by name, department, or job title."

    def _call_gemini_contacts(self, query: str, contacts: List[Dict[str, Any]], status: str, lang: str) -> Optional[str]:
        """Generates dynamic, naturally varied, 1-sentence executive headers directly above cards."""
        clean_key = self.api_key.strip()
        
        system_instruction = (
            "أنت المساعد الذكي لدليل موظفي الشركة. "
            "المطلوب: صياغة جملة تقديمية واحدة فقط، أنيقة، احترافية، ومكتملة تماماً، تسبق ظهور الكروت. "
            "قواعد التنوع والذكاء: "
            "1. نوّع في صياغة وبداية الجملة بشكل طبيعي وذكي بما يناسب سؤال المستخدم (مثال: 'تفضل يا فندم، هذه بيانات التواصل الخاصة بـ...' أو 'بناءً على طلبكم، تجدون أدناه تفاصيل...' أو 'إليكم بطاقة التواصل الخاصة بـ...'). "
            "2. عند العثور على موظف واحد: اذكر اسمه ومسماه وإدارته بجملة موجزة تنتهي بنقطتين أو نقطة. "
            "3. عند العثور على عدة موظفين: اذكر عدد الموظفين وإدارتهم بجملة تمهيدية لطيفة للاطلاع على الكروت أدناه. "
            "4. ممنوع أي مقدمات طويلة أو عبارات مبالغ فيها مثل 'مجلس الإدارة الموقر' أو 'السلام عليكم'. "
            "5. اكتب دائماً سطراً واحداً فقط مكتمل المعنى 100%."
        )

        contacts_summary = [
            f"{c['name']} ({c['role']} - {c['department']})"
            for c in contacts
        ]

        user_prompt = f"طلب البحث من المستخدم: '{query}'\nالحالة: {status}\nالبيانات: {json.dumps(contacts_summary, ensure_ascii=False)}\nالمطلوب: جملة تقديمية ذكية واحدة وموجزة ومكتملة."

        payload = {
            "contents": [{"parts": [{"text": f"{system_instruction}\n\n{user_prompt}"}]}],
            "generationConfig": {"temperature": 0.5, "maxOutputTokens": 200}
        }
        headers = {"Content-Type": "application/json"}

        for model in ACTIVE_MODELS:
            url = f"https://generativelanguage.googleapis.com/v1beta/{model}:generateContent?key={clean_key}"
            try:
                response = requests.post(url, json=payload, headers=headers, timeout=6)
                if response.status_code == 200:
                    data = response.json()
                    candidates_out = data.get("candidates", [])
                    if candidates_out:
                        raw_text = candidates_out[0]["content"]["parts"][0]["text"].strip()
                        # Clean any model thought artefacts or long greeting headers
                        clean_text = re.sub(r"^(السلام عليكم ورحمة الله وبركاته[،\s]*)+", "", raw_text).strip()
                        clean_text = re.sub(r"^\*?\*?\(.*?\)\*?\*?\s*", "", clean_text)
                        clean_text = re.sub(r"^\*+Attempt.*?\*+\s*", "", clean_text, flags=re.DOTALL)
                        clean_text = re.sub(r"<think>.*?</think>", "", clean_text, flags=re.DOTALL).strip()
                        
                        # Strip accidental trailing conjunctions
                        clean_text = re.sub(r"\s+(الذي|التي|وهو|وهي|ومدير|ومديرة|شاغل|منصب)$", "", clean_text).strip()
                        
                        if clean_text and len(clean_text) > 8:
                            return clean_text
            except Exception:
                continue

        return None

    def _call_gemini_general(self, query: str, lang: str) -> Optional[str]:
        """Calls Google Gemini for greetings or general questions with polite, natural, and modern elegance."""
        clean_key = self.api_key.strip()
        system_instruction = (
            "أنت المساعد الذكي لدليل موظفي الشركة. "
            "أجب بلباقة واحترافية هادئة وبسيطة بدون أي تكلف أو مبالغة وبدون ذكر مجالس إدارة أو تفاصيل غير مطلوبة (مثال: 'أهلاً بحضرتك يا فندم! يسعدني دائماً مساعدتك في الوصول لبيانات أي موظف أو قسم، تحب تبحث عن مين؟')."
        )

        headers = {"Content-Type": "application/json"}
        user_prompt = f"المستخدم يقول: '{query}'. اكتب رداً لطيفاً واحترافياً واحداً وموجزاً."
        
        payload = {
            "contents": [{"parts": [{"text": f"{system_instruction}\n\n{user_prompt}"}]}],
            "generationConfig": {"temperature": 0.4, "maxOutputTokens": 150}
        }
        
        for model in ACTIVE_MODELS:
            url = f"https://generativelanguage.googleapis.com/v1beta/{model}:generateContent?key={clean_key}"
            try:
                res = requests.post(url, json=payload, headers=headers, timeout=5)
                if res.status_code == 200:
                    data = res.json()
                    raw_text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                    clean_text = re.sub(r"^\*?\*?\(.*?\)\*?\*?\s*", "", raw_text)
                    clean_text = re.sub(r"^\*+Attempt.*?\*+\s*", "", clean_text, flags=re.DOTALL)
                    clean_text = re.sub(r"<think>.*?</think>", "", clean_text, flags=re.DOTALL).strip()
                    if clean_text and len(clean_text) > 5:
                        return clean_text
            except Exception:
                continue
        return None
