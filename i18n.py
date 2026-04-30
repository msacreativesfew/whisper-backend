"""
Internationalization (i18n) system for Whisper AI Assistant.

Supports 15+ languages with:
- Dynamic language switching
- Context-aware translations
- Regional date/time formatting
- Number and currency localization
"""

from enum import Enum
from typing import Dict, Optional, Any
from datetime import datetime
import json
import os

# ============================================================================
# SUPPORTED LANGUAGES
# ============================================================================

class Language(Enum):
    """Supported languages with language codes and names."""
    ENGLISH = ("en", "English")
    SPANISH = ("es", "Español")
    FRENCH = ("fr", "Français")
    GERMAN = ("de", "Deutsch")
    ITALIAN = ("it", "Italiano")
    PORTUGUESE = ("pt", "Português")
    JAPANESE = ("ja", "日本語")
    CHINESE_SIMPLIFIED = ("zh", "简体中文")
    KOREAN = ("ko", "한국어")
    RUSSIAN = ("ru", "Русский")
    ARABIC = ("ar", "العربية")
    HINDI = ("hi", "हिन्दी")
    DUTCH = ("nl", "Nederlands")
    POLISH = ("pl", "Polski")
    TURKISH = ("tr", "Türkçe")

    def __init__(self, code: str, name: str):
        self._value_ = code
        self.code = code
        self.native_name = name


# ============================================================================
# TRANSLATION STRINGS
# ============================================================================

TRANSLATIONS = {
    "en": {
        # General
        "welcome": "Welcome to Whisper AI Assistant",
        "connecting": "Connecting...",
        "listening": "Listening...",
        "speaking": "Speaking...",
        "offline": "Offline",
        "error": "Error",
        "success": "Success",
        "loading": "Loading...",
        
        # UI Elements
        "tap_to_speak": "Tap to speak",
        "tap_to_reconnect": "Tap to reconnect",
        "start_speaking": "Start speaking to see your transcript",
        "enable_audio": "Tap here to enable audio",
        
        # Conversation
        "you": "You",
        "assistant": "Whisper",
        "assistant_waiting": "Waiting for response...",
        "conversation_started": "Conversation started",
        "conversation_ended": "Conversation ended",
        
        # Settings
        "preferences": "Preferences",
        "language": "Language",
        "voice_speed": "Voice Speed",
        "response_length": "Response Length",
        "privacy_mode": "Privacy Mode",
        "short": "Short",
        "medium": "Medium",
        "long": "Long",
        
        # Integrations
        "integrations": "Integrations",
        "connect": "Connect",
        "disconnect": "Disconnect",
        "google_calendar": "Google Calendar",
        "gmail": "Gmail",
        "slack": "Slack",
        
        # Analytics
        "usage": "Usage",
        "tokens_used": "Tokens Used",
        "api_cost": "API Cost",
        "this_month": "This Month",
        
        # Errors
        "connection_error": "Connection Error",
        "audio_blocked": "Audio Blocked",
        "microphone_not_available": "Microphone not available",
        "backend_error": "Backend error",
    },
    
    "es": {
        "welcome": "Bienvenido a Whisper AI Assistant",
        "connecting": "Conectando...",
        "listening": "Escuchando...",
        "speaking": "Hablando...",
        "offline": "Desconectado",
        "tap_to_speak": "Toca para hablar",
        "you": "Tú",
        "assistant": "Whisper",
        "preferences": "Preferencias",
        "language": "Idioma",
    },
    
    "fr": {
        "welcome": "Bienvenue sur Whisper AI Assistant",
        "connecting": "Connexion en cours...",
        "listening": "À l'écoute...",
        "speaking": "En train de parler...",
        "offline": "Hors ligne",
        "tap_to_speak": "Appuyez pour parler",
        "you": "Vous",
        "assistant": "Whisper",
        "preferences": "Préférences",
        "language": "Langue",
    },
    
    "de": {
        "welcome": "Willkommen bei Whisper AI Assistant",
        "connecting": "Wird verbunden...",
        "listening": "Hört zu...",
        "speaking": "Spricht...",
        "offline": "Offline",
        "tap_to_speak": "Zum Sprechen tippen",
        "you": "Sie",
        "assistant": "Whisper",
        "preferences": "Einstellungen",
        "language": "Sprache",
    },
    
    "it": {
        "welcome": "Benvenuto in Whisper AI Assistant",
        "connecting": "Connessione in corso...",
        "listening": "In ascolto...",
        "speaking": "Parlando...",
        "offline": "Non in linea",
        "tap_to_speak": "Tocca per parlare",
        "you": "Tu",
        "assistant": "Whisper",
        "preferences": "Preferenze",
        "language": "Lingua",
    },
    
    "pt": {
        "welcome": "Bem-vindo ao Whisper AI Assistant",
        "connecting": "Conectando...",
        "listening": "Ouvindo...",
        "speaking": "Falando...",
        "offline": "Desconectado",
        "tap_to_speak": "Toque para falar",
        "you": "Você",
        "assistant": "Whisper",
        "preferences": "Preferências",
        "language": "Idioma",
    },
    
    "ja": {
        "welcome": "Whisper AI アシスタントへようこそ",
        "connecting": "接続中...",
        "listening": "リッスン中...",
        "speaking": "スピーキング中...",
        "offline": "オフライン",
        "tap_to_speak": "タップして話す",
        "you": "あなた",
        "assistant": "ウィスパー",
        "preferences": "設定",
        "language": "言語",
    },
    
    "zh": {
        "welcome": "欢迎使用 Whisper AI 助手",
        "connecting": "连接中...",
        "listening": "聆听中...",
        "speaking": "说话中...",
        "offline": "离线",
        "tap_to_speak": "点击说话",
        "you": "你",
        "assistant": "Whisper",
        "preferences": "偏好设置",
        "language": "语言",
    },
    
    "ko": {
        "welcome": "Whisper AI 어시스턴트에 오신 것을 환영합니다",
        "connecting": "연결 중...",
        "listening": "듣는 중...",
        "speaking": "말하는 중...",
        "offline": "오프라인",
        "tap_to_speak": "탭하여 말하기",
        "you": "당신",
        "assistant": "Whisper",
        "preferences": "환경설정",
        "language": "언어",
    },
    
    "ru": {
        "welcome": "Добро пожаловать в Whisper AI Assistant",
        "connecting": "Подключение...",
        "listening": "Прослушивание...",
        "speaking": "Говорю...",
        "offline": "Не в сети",
        "tap_to_speak": "Нажмите, чтобы говорить",
        "you": "Вы",
        "assistant": "Whisper",
        "preferences": "Предпочтения",
        "language": "Язык",
    },
    
    "ar": {
        "welcome": "مرحبا بك في مساعد Whisper AI",
        "connecting": "جاري الاتصال...",
        "listening": "الاستماع...",
        "speaking": "الكلام...",
        "offline": "غير متصل",
        "tap_to_speak": "اضغط للتحدث",
        "you": "أنت",
        "assistant": "Whisper",
        "preferences": "التفضيلات",
        "language": "اللغة",
    },
    
    "hi": {
        "welcome": "Whisper AI सहायक में आपका स्वागत है",
        "connecting": "जुड़ रहे हैं...",
        "listening": "सुन रहे हैं...",
        "speaking": "बोल रहे हैं...",
        "offline": "ऑफ़लाइन",
        "tap_to_speak": "बोलने के लिए टैप करें",
        "you": "आप",
        "assistant": "Whisper",
        "preferences": "वरीयताएं",
        "language": "भाषा",
    },
    
    "nl": {
        "welcome": "Welkom bij Whisper AI Assistant",
        "connecting": "Verbinden...",
        "listening": "Luisteren...",
        "speaking": "Spreken...",
        "offline": "Offline",
        "tap_to_speak": "Tik om te spreken",
        "you": "Jij",
        "assistant": "Whisper",
        "preferences": "Voorkeuren",
        "language": "Taal",
    },
    
    "pl": {
        "welcome": "Witaj w Whisper AI Assistant",
        "connecting": "Łączenie...",
        "listening": "Słuchanie...",
        "speaking": "Mówienie...",
        "offline": "Offline",
        "tap_to_speak": "Naciśnij, aby mówić",
        "you": "Ty",
        "assistant": "Whisper",
        "preferences": "Preferencje",
        "language": "Język",
    },
    
    "tr": {
        "welcome": "Whisper AI Asistanına Hoş Geldiniz",
        "connecting": "Bağlanıyor...",
        "listening": "Dinliyor...",
        "speaking": "Konuşuyor...",
        "offline": "Çevrimdışı",
        "tap_to_speak": "Konuşmak için dokunun",
        "you": "Sen",
        "assistant": "Whisper",
        "preferences": "Tercihler",
        "language": "Dil",
    },
}


# ============================================================================
# LOCALE CONFIGURATIONS
# ============================================================================

LOCALES = {
    "en": {
        "currency": "USD",
        "currency_symbol": "$",
        "date_format": "%m/%d/%Y",
        "time_format": "%I:%M %p",
        "decimal_separator": ".",
        "thousands_separator": ",",
        "rtl": False,  # Right-to-left languages
    },
    "es": {"currency": "EUR", "currency_symbol": "€", "date_format": "%d/%m/%Y", "time_format": "%H:%M", "rtl": False},
    "fr": {"currency": "EUR", "currency_symbol": "€", "date_format": "%d/%m/%Y", "time_format": "%H:%M", "rtl": False},
    "de": {"currency": "EUR", "currency_symbol": "€", "date_format": "%d.%m.%Y", "time_format": "%H:%M", "rtl": False},
    "it": {"currency": "EUR", "currency_symbol": "€", "date_format": "%d/%m/%Y", "time_format": "%H:%M", "rtl": False},
    "pt": {"currency": "EUR", "currency_symbol": "€", "date_format": "%d/%m/%Y", "time_format": "%H:%M", "rtl": False},
    "ja": {"currency": "JPY", "currency_symbol": "¥", "date_format": "%Y/%m/%d", "time_format": "%H:%M", "rtl": False},
    "zh": {"currency": "CNY", "currency_symbol": "¥", "date_format": "%Y/%m/%d", "time_format": "%H:%M", "rtl": False},
    "ko": {"currency": "KRW", "currency_symbol": "₩", "date_format": "%Y.%m.%d", "time_format": "%H:%M", "rtl": False},
    "ru": {"currency": "RUB", "currency_symbol": "₽", "date_format": "%d.%m.%Y", "time_format": "%H:%M", "rtl": False},
    "ar": {"currency": "SAR", "currency_symbol": "﷼", "date_format": "%d/%m/%Y", "time_format": "%H:%M", "rtl": True},
    "hi": {"currency": "INR", "currency_symbol": "₹", "date_format": "%d/%m/%Y", "time_format": "%H:%M", "rtl": False},
    "nl": {"currency": "EUR", "currency_symbol": "€", "date_format": "%d-%m-%Y", "time_format": "%H:%M", "rtl": False},
    "pl": {"currency": "PLN", "currency_symbol": "zł", "date_format": "%d.%m.%Y", "time_format": "%H:%M", "rtl": False},
    "tr": {"currency": "TRY", "currency_symbol": "₺", "date_format": "%d.%m.%Y", "time_format": "%H:%M", "rtl": False},
}


# ============================================================================
# TRANSLATOR CLASS
# ============================================================================

class Translator:
    """Multi-language translator for Whisper AI Assistant."""
    
    def __init__(self, language: str = "en"):
        """Initialize with a specific language."""
        self.current_language = language if language in TRANSLATIONS else "en"
        self.locale = LOCALES.get(self.current_language, LOCALES["en"])
    
    def set_language(self, language: str) -> bool:
        """Switch to a different language."""
        if language in TRANSLATIONS:
            self.current_language = language
            self.locale = LOCALES.get(language, LOCALES["en"])
            return True
        return False
    
    def get_language(self) -> str:
        """Get current language code."""
        return self.current_language
    
    def translate(self, key: str, default: str = "") -> str:
        """Translate a key to the current language."""
        return TRANSLATIONS[self.current_language].get(key, default)
    
    def t(self, key: str) -> str:
        """Short alias for translate()."""
        return self.translate(key)
    
    def format_date(self, date: datetime) -> str:
        """Format date according to locale."""
        return date.strftime(self.locale["date_format"])
    
    def format_time(self, date: datetime) -> str:
        """Format time according to locale."""
        return date.strftime(self.locale["time_format"])
    
    def format_datetime(self, date: datetime) -> str:
        """Format date and time according to locale."""
        date_str = self.format_date(date)
        time_str = self.format_time(date)
        return f"{date_str} {time_str}"
    
    def format_currency(self, amount: float) -> str:
        """Format amount as currency."""
        symbol = self.locale["currency_symbol"]
        sep = self.locale["thousands_separator"]
        decimal = self.locale["decimal_separator"]
        
        # Format the number
        formatted = f"{amount:,.2f}".replace(",", sep).replace(".", decimal)
        
        # Add currency symbol (left for most, right for some)
        if self.current_language in ["ar"]:
            return f"{formatted}{symbol}"
        return f"{symbol}{formatted}"
    
    def format_number(self, num: float, decimals: int = 2) -> str:
        """Format number according to locale."""
        sep = self.locale["thousands_separator"]
        decimal = self.locale["decimal_separator"]
        
        format_str = f"{{:,.{decimals}f}}"
        formatted = format_str.format(num)
        formatted = formatted.replace(",", sep).replace(".", decimal)
        return formatted
    
    def get_all_languages(self) -> Dict[str, str]:
        """Get all available languages."""
        return {lang.code: lang.native_name for lang in Language}
    
    def is_rtl(self) -> bool:
        """Check if current language is right-to-left."""
        return self.locale.get("rtl", False)


# ============================================================================
# GLOBAL TRANSLATOR INSTANCE
# ============================================================================

_translator: Optional[Translator] = None

def init_translator(language: str = "en") -> Translator:
    """Initialize the global translator."""
    global _translator
    _translator = Translator(language)
    return _translator

def get_translator() -> Translator:
    """Get the global translator instance."""
    global _translator
    if _translator is None:
        _translator = Translator()
    return _translator

def t(key: str) -> str:
    """Global translate function."""
    return get_translator().translate(key)

def set_language(language: str) -> bool:
    """Set global language."""
    return get_translator().set_language(language)


# ============================================================================
# FASTAPI INTEGRATION
# ============================================================================

from fastapi import APIRouter, Query

i18n_router = APIRouter(prefix="/api/i18n", tags=["localization"])

@i18n_router.get("/languages")
async def get_available_languages():
    """Get all available languages."""
    translator = get_translator()
    return {
        "current": translator.get_language(),
        "available": translator.get_all_languages(),
    }

@i18n_router.post("/language")
async def set_user_language(language: str = Query(...)):
    """Set the user's language."""
    translator = get_translator()
    if translator.set_language(language):
        return {
            "status": "success",
            "language": translator.get_language(),
        }
    return {
        "status": "error",
        "message": f"Language '{language}' not supported",
    }

@i18n_router.get("/translations")
async def get_translations(language: str = Query("en")):
    """Get all translations for a language."""
    if language not in TRANSLATIONS:
        language = "en"
    
    return {
        "language": language,
        "translations": TRANSLATIONS[language],
        "locale": LOCALES[language],
    }
