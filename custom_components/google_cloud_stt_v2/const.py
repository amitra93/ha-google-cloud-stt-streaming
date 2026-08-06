"""Constants for Google Cloud STT V2 integration."""

DOMAIN = "google_cloud_stt_v2"
TITLE = "Google Cloud Speech-to-Text V2"

CONF_SERVICE_ACCOUNT_INFO = "service_account_info"
CONF_REGION = "region"
CONF_MODEL = "model"
CONF_PUNCTUATION = "punctuation"
CONF_PHRASE_HINTS = "phrase_hints"
CONF_SPEECH_START_TIMEOUT = "speech_start_timeout"
CONF_SPEECH_END_TIMEOUT = "speech_end_timeout"
CONF_RECOGNIZER = "recognizer"

DEFAULT_PUNCTUATION = True
DEFAULT_SPEECH_START_TIMEOUT = 5.0
DEFAULT_SPEECH_END_TIMEOUT = 1.0
DEFAULT_RECOGNIZER = "_"

EVENT_TRANSCRIPT = "google_cloud_stt_v2_transcript"
EVENT_ERROR = "google_cloud_stt_v2_error"

SUPPORTED_REGIONS = [
    "us-central1",
    "us-east1",
    "us",
    "europe-west4",
    "eu",
    "asia-southeast1",
    "global",
]

SUPPORTED_MODELS = [
    "chirp_2",
    "chirp_3",
    "latest_short",
    "latest_long",
    "telephony",
]

HA_TO_GCP_LANG_MAP = {
    "en": "en-US",
    "es": "es-ES",
    "fr": "fr-FR",
    "de": "de-DE",
    "it": "it-IT",
    "ja": "ja-JP",
    "zh": "zh-CN",
    "pt": "pt-BR",
}

STT_LANGUAGES = [
    "af-ZA", "am-ET", "ar-AE", "ar-BH", "ar-DZ", "ar-EG", "ar-IL", "ar-IQ", "ar-JO",
    "ar-KW", "ar-LB", "ar-MA", "ar-OM", "ar-QA", "ar-SA", "ar-PS", "ar-SY", "ar-TN",
    "az-AZ", "bg-BG", "bn-BD", "bn-IN", "bs-BA", "ca-ES", "cs-CZ", "da-DK", "de-AT",
    "de-CH", "de-DE", "el-GR", "en-AU", "en-CA", "en-GB", "en-GH", "en-IE", "en-IN",
    "en-KE", "en-NG", "en-NZ", "en-PH", "en-TZ", "en-UG", "en-US", "en-ZA", "es-AR",
    "es-BO", "es-CL", "es-CO", "es-CR", "es-DO", "es-EC", "es-ES", "es-GT", "es-HN",
    "es-MX", "es-NI", "es-PA", "es-PE", "es-PR", "es-PY", "es-SV", "es-US", "es-UY",
    "es-VE", "et-EE", "eu-ES", "fa-IR", "fi-FI", "fil-PH", "fr-BE", "fr-CA", "fr-CH",
    "fr-FR", "gl-ES", "gu-IN", "he-IL", "hi-IN", "hr-HR", "hu-HU", "hy-AM", "id-ID",
    "is-IS", "it-CH", "it-IT", "ja-JP", "jv-ID", "ka-GE", "km-KH", "kn-IN", "ko-KR",
    "lo-LA", "lt-LT", "lv-LV", "mk-MK", "ml-IN", "mn-MN", "mr-IN", "ms-MY", "my-MM",
    "ne-NP", "nl-BE", "nl-NL", "no-NO", "pa-Guru-IN", "pl-PL", "pt-BR", "pt-PT",
    "ro-RO", "ru-RU", "si-LK", "sk-SK", "sl-SI", "sq-AL", "sr-RS", "su-ID", "sv-SE",
    "sw-KE", "sw-TZ", "ta-IN", "ta-LK", "ta-MY", "ta-SG", "te-IN", "th-TH", "tr-TR",
    "uk-UA", "ur-IN", "ur-PK", "uz-UZ", "vi-VN", "yue-Hant-HK", "zh", "zh-TW", "zu-ZA"
]
