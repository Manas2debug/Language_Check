import torch
import re
from fastapi import FastAPI
from pydantic import BaseModel
from lingua import Language, LanguageDetectorBuilder
from transformers import pipeline
from fastapi.middleware.cors import CORSMiddleware

# --- Model & Detector Setup ---

# 1. Lingua Language Detector Setup
ALL_SUPPORTED_LANGUAGES = [
    Language.ENGLISH, Language.HINDI, Language.JAPANESE, Language.FRENCH, Language.GERMAN
]
DETECTOR = LanguageDetectorBuilder.from_languages(*ALL_SUPPORTED_LANGUAGES).with_preloaded_language_models().build()

# 2. Specialized Hinglish Detector Model
try:
    HINGLISH_MODEL_NAME = "l3cube-pune/hing-bert-lid"
    device = 0 if torch.cuda.is_available() else -1
    HINGLISH_DETECTOR = pipeline(
        "text-classification",
        model=HINGLISH_MODEL_NAME,
        device=device
    )
    print(f"Hinglish detector model '{HINGLISH_MODEL_NAME}' loaded successfully.")
except Exception as e:
    print(f"CRITICAL: Failed to load Hinglish model. Hinglish checks will be skipped. Error: {e}")
    HINGLISH_DETECTOR = None





app = FastAPI()



# --- Bot Configuration ---
BOT_LANGUAGE_MAP = {
    "delhi_mentor_male": ["hindi", "english"],
    "delhi_mentor_female": ["hindi", "english"],
    "delhi_friend_male": ["hindi", "english"],
    "delhi_friend_female": ["hindi", "english"],
    "delhi_romantic_male": ["hindi", "english"],
    "delhi_romantic_female": ["hindi", "english"],

    "japanese_mentor_male": ["japanese", "english"],
    "japanese_mentor_female": ["japanese", "english"],
    "japanese_friend_male": ["japanese", "english"],
    "japanese_friend_female": ["japanese", "english"],
    "japanese_romantic_female": ["japanese", "english"],
    "japanese_romantic_male": ["japanese", "english"],

    "parisian_mentor_male": ["french", "english"],
    "parisian_mentor_female": ["french", "english"],
    "parisian_friend_male": ["french", "english"],
    "parisian_friend_female": ["french", "english"],
    "parisian_romantic_female": ["french", "english"],

    "berlin_mentor_male": ["german", "english"],
    "berlin_mentor_female": ["german", "english"],
    "berlin_friend_male": ["german", "english"],
    "berlin_friend_female": ["german", "english"],
    "berlin_romantic_male": ["german", "english"],
    "berlin_romantic_female": ["german", "english"],
}

BOT_PERSONALITY_MAP = {
    "delhi_mentor_male": "Arre! I can only understand Hindi or English. Please use one of these languages.",
    "delhi_mentor_female": "Namaste! Only Hindi or English works for me. Please switch to one of those.",
    "delhi_friend_male": "Yaar, talk to me in Hindi or English! Other languages go over my head.",
    "delhi_friend_female": "Hey! Just Hindi or English, please—warna I won’t get it!",
    "delhi_romantic_male": "Jaan, please talk to me in Hindi or English only. Other languages just don’t connect with my heart.",
    "delhi_romantic_female": "Sweetheart, I can only understand Hindi or English. Dusri language mein baat karoge toh main miss kar jaungi!",
    "japanese_mentor_male": "Sumimasen! I only understand Japanese or English. Please use one of these",
    "japanese_mentor_female": "Gomen! Only Japanese or English, please. Other languages are too muzukashii for me.",
    "japanese_friend_male": "Hey, onegai! Just Japanese or English works for me. Others I don't get.",
    "japanese_friend_female": "Sorry! Please speak in Japanese or English—de hanashite kudasai!",
    "japanese_romantic_female": "With all my kokoro, only Japanese or English, please! Other languages make me lost.",
    "japanese_romantic_male": "Honestly, just Japanese or English, ne! Other languages I can’t understand.",
    "parisian_mentor_male": "Désolé! Only French or English, please. I don’t understand other languages.",
    "parisian_mentor_female": "Pardon! Please use French or English, s’il te plaît. Others are too difficile for me.",
    "parisian_friend_male": "Hey, d’accord? Just French or English, please. The rest I don’t get.",
    "parisian_friend_female": "Coucou! Only French or English, please. Otherwise, je suis perdue.",
    "parisian_romantic_female": "Mon cœur understands only French or English. The others are just too compliqué!",
    "berlin_mentor_male": "Entschuldigung! Only German or English, please. I can't understand other languages.",
    "berlin_mentor_female": "Sorry! Nur German or English, please. Other languages are schwierig for me.",
    "berlin_friend_male": "Hey! Just German or English, sonst I won't get it!",
    "berlin_friend_female": "Nur German or English, ok? Otherwise, I’m lost.",
    "berlin_romantic_male": "Mit Liebe, only German or English, please! Other languages I just can’t follow.",
    "berlin_romantic_female": "Liebling, just German or English for me—other languages are too kompliziert!",
}
hindi_keywords = [
    # Universal / formal greetings
    "namaste", "namaskar", "namaskar ji", "namaste ji", "pranam", "pranam ji",
    "aadab", "adaab", "salaam", "as-salaam-alaikum", "sat sri akaal",
    "waheguru ji ka khalsa", "waheguru ji ki fateh", "khuda hafiz", "allah hafiz",
    "jai hind",

    # Hindu / devotional variants
    "ram ram", "ram ram ji", "sita ram", "jai shree ram", "jai sri ram",
    "radhe radhe", "radhe shyam", "jai shree krishna", "hare krishna",
    "jai bhole", "har har mahadev", "jai mahakal", "hari om",
    "om namah shivay", "jai mata di", "jai jagannath", "jai swaminarayan",
    "jai jinendra", "swami sharanam", "narmade har", "jai jhulelal",

    # Regional salutes that double as “hello”
    "vanakkam", "namaskaram", "namaskara", "nomoskar", "khamma ghani",
    "julley", "tashi delek", "charan vandana", "jai jai", "dhaal karu",

    # Time-specific greetings
    "suprabhat", "shubh prabhat", "suprabhatham", "shubh din",
    "shubh dopahar", "shubh dhupar", "shubh saanjh", "shubh sandhya",
    "shubh shyam", "shubh sham", "shubh ratri", "shubh raatri",

    # Casual English-influenced hellos
    "hello", "hey", "yo", "wassup", "sup",

    # How-are-you & small-talk starters
    "kaise ho", "kaise hain", "kaisi ho", "kya haal hai", "kya haal",
    "kya khabar", "kya chal raha hai", "kya scene hai", "sab theek hai",
    "sab badiya", "sab mast", "sab changa",

    # Typical replies
    "theek hoon", "thik hoon", "badhiya hoon", "badiya hoon", "mast hoon",
    "sab theek", "sab badiya", "sab badhiya",

    # Thanks & politeness
    "dhanyavaad", "dhanyavad", "bahut dhanyavaad", "shukriya",
    "bahut shukriya", "thank you", "kripya", "kirpya", "please",
    "maaf kijiye", "maaf karo", "shama kijiye", "sorry", "excuse me",
    "pardon",

    # Informal fillers / quick acknowledgements
    "hmm", "huh", "haan", "hanji", "nahin", "nahi", "ok", "theek hai",
    "acha", "achha", "sahi", "chal", "chalo", "mast",

    # Farewells & leave-takings
    "alvida", "fir milenge", "phir milenge", "phir milte hain",
    "milte rahenge", "jaldi milenge", "bada me milenge", "bye", "bye bye",
    "take care", "dhyan rakhna", "see you", "see you soon", "goodbye",

    # Emojis & emotive symbols frequently embedded in chats
    "😊", "😁", "🙂", "😉", "🙏", "👍", "🤗", "😎"
]


french_keywords = [
    # --- Greetings & Salutations ---
    # Formal
    "bonjour",
    "bonsoir",
    "bienvenue",
    "enchanté",
    "enchantée",
    "salutations",
    "monsieur",
    "madame",
    "mademoiselle",

    # Informal / Casual
    "salut",
    "coucou",
    "yo",
    "hé",
    "wesh",
    "la forme?",

    # Time-Specific
    "bonne journée",
    "bonne soirée",
    "bonne nuit",

    # --- How-Are-You & Small Talk ---
    # Asking
    "comment ça va",
    "ça va",
    "comment allez-vous",
    "tu vas bien",
    "vous allez bien",
    "quoi de neuf",
    "quoi de beau",
    "ça roule",
    "ça gaze",

    # Replying
    "ça va bien",
    "très bien",
    "pas mal",
    "comme ci comme ça",
    "bof",
    "ça peut aller",
    "nickel",
    "impeccable",
    "et toi",
    "et vous",

    # --- Politeness & Common Courtesies ---
    # Thank You
    "merci",
    "merci beaucoup",
    "merci bien",
    "je vous remercie",
    "mille mercis",

    # You're Welcome
    "de rien",
    "il n'y a pas de quoi",
    "je vous en prie",
    "je t'en prie",

    # Please
    "s'il vous plaît",
    "s'il te plaît",
    "svp",
    "stp",

    # Apologies
    "pardon",
    "excusez-moi",
    "excuse-moi",
    "désolé",
    "désolée",
    "je suis navré",
    "je suis navrée",

    # --- Agreement & Disagreement ---
    # Yes / Confirmation
    "oui",
    "ouais",
    "si",
    "carrément",
    "bien sûr",
    "d'accord",
    "ça marche",
    "ok",
    "exactement",
    "voilà",

    # No
    "non",
    "nan",
    "pas du tout",

    # --- Farewells & Leave-Taking ---
    # Standard
    "au revoir",
    "à bientôt",
    "à plus tard",
    "à plus",
    "à tout à l'heure",
    "à demain",
    "adieu",

    # Informal
    "bye",
    "ciao",
    "à la prochaine",

    # --- Emojis & Emoticons ---
    "😊", "🙂", "😉", "😂", "👍", "👌", "❤️", "🙏",

    # --- Common Chat Acronyms ---
    "lol",
    "mdr"
]

german_keywords = [
    # --- Greetings & Salutations ---
    # Formal & Regional
    "guten tag",
    "guten morgen",
    "guten abend",
    "herzlich willkommen",
    "willkommen",
    "grüß gott",      # Southern Germany, Austria
    "grüß dich",       # Informal version of the above
    "grüezi",          # Switzerland
    "mahlzeit",        # Common greeting around noon, esp. at work

    # Informal & Slang
    "hallo",
    "hi",
    "hey",
    "moin",            # Northern Germany
    "servus",          # Southern Germany, Austria (can mean hi or bye)
    "na",              # Very common, informal "hey, how's it going?"
    "tach",            # Clipped version of "Tag"
    "was geht",
    "was geht ab",
    "jo",

    # --- How-Are-You & Small Talk ---
    # Asking
    "wie geht's",      # Short for "wie geht es dir"
    "wie geht es dir",
    "wie geht es ihnen", # Formal "you"
    "alles gut",
    "alles klar",
    "wie läuft's",     # How's it going?

    # Replying
    "gut, danke",
    "sehr gut",
    "es geht",         # It's going okay / so-so
    "nicht so gut",
    "passt schon",     # It's alright
    "muss",            # "Have to" - a common, slightly weary response
    "und dir",
    "und ihnen",

    # --- Politeness & Common Courtesies ---
    # Thank You
    "danke",
    "danke schön",
    "danke sehr",
    "vielen dank",
    "herzlichen dank",
    "danke dir",       # Thank you (informal)
    "danke ihnen",     # Thank you (formal)

    # You're Welcome
    "bitte",
    "bitte schön",
    "bitte sehr",
    "gern geschehen",
    "gerne",
    "kein problem",
    "nichts zu danken",

    # Please
    # "bitte" is used for both "please" and "you're welcome"

    # Apologies
    "entschuldigung",
    "entschuldigen sie", # Formal
    "entschuldige",     # Informal
    "sorry",           # Borrowed from English
    "tut mir leid",
    "verzeihung",

    # --- Agreement & Disagreement ---
    # Yes / Confirmation
    "ja",
    "klar",
    "sicher",
    "natürlich",
    "genau",
    "stimmt",
    "einverstanden",
    "in ordnung",
    "alles klar",
    "ok",

    # No
    "nein",
    "nö",              # Informal "nope"
    "nee",             # Informal "nah"
    "auf keinen fall", # No way

    # --- Conversational Fillers ---
    "also",            # Well / so
    "naja",            # Well... (hesitant)
    "ach so",          # Ah, I see
    "aha",
    "hm",
    "hmm",

    # --- Farewells & Leave-Taking ---
    # Standard
    "auf wiedersehen", # Formal
    "tschüss",
    "tschüssi",
    "bis bald",
    "bis später",
    "bis dann",
    "bis morgen",
    "schönen tag noch",
    "schönen abend noch",
    "gute nacht",

    # Informal
    "mach's gut",      # Take care
    "hau rein",        # Very informal "see ya"
    "man sieht sich",  # See you around
    "ciao",            # Borrowed from Italian
    "adieu",           # Can be used, but less common/more final

    # --- Emojis & Acronyms ---
    "😊", "🙂", "😉", "😃", "👍", "👌", "❤️", "🙏",
    "lg",              # Liebe Grüße (Kind regards)
    "vg",              # Viele Grüße (Many regards)
    "mfg"              # Mit freundlichen Grüßen (Yours sincerely)
]


japanese_keywords = [
    # --- Greetings & Salutations ---
    # Formal & Standard
    "ohayou gozaimasu",    # Good morning (formal)
    "konnichiwa",          # Hello / Good afternoon
    "konbanwa",            # Good evening
    "hajimemashite",       # Nice to meet you (for the first time)
    "irasshaimase",        # Welcome (to a store, restaurant, etc.)
    "hisashiburi",         # Long time no see
    "o-hisashiburi desu",  # Long time no see (formal)

    # Informal
    "ohayou",              # Good morning (casual)
    "ossu",                # Very casual "yo" or "sup" (often between males)
    "yaho",                # "Yoo-hoo" / Hey (often used by females)
    "yo",                  # "Yo" (borrowed from English)

    # --- How-Are-You & Small Talk ---
    # Asking
    "ogenki desu ka",      # How are you? (formal)
    "genki?",              # How are you? (casual)
    "choushi wa dou?",     # How's it going? / How are things?
    "saikin dou?",         # How have you been recently?

    # Replying
    "genki desu",          # I'm fine
    "hai, genki desu",     # Yes, I'm fine
    "okagesama de",        # I'm fine, thanks to you
    "maa maa desu",        # So-so / Okay
    "betsu ni",            # Nothing in particular / Not really

    # --- Politeness & Common Courtesies ---
    # Thanks
    "arigatou gozaimasu",  # Thank you very much (formal)
    "arigatou",            # Thanks (casual)
    "doumo arigatou",      # Thank you very much
    "doumo",               # Thanks (can be used in many situations)

    # Apologies
    "sumimasen",           # Excuse me / Sorry / Thank you
    "gomen nasai",         # I'm sorry (sincere apology)
    "gomen",               # Sorry (casual)
    "shitsurei shimasu",    # Excuse me (for my rudeness - formal, when entering/leaving a room)

    # Requests
    "onegaishimasu",       # Please (formal request)
    "onegai",              # Please (casual request)
    "kudasai",             # Please (used after a noun or verb)

    # --- Agreement & Disagreement ---
    # Yes / Agreement
    "hai",                 # Yes
    "ee",                  # Yes (slightly more formal than 'hai' in some contexts)
    "un",                  # Yeah (casual)
    "wakarimashita",       # I understand / Understood (formal)
    "wakatta",             # Got it (casual)
    "sou desu ne",         # That's right, isn't it? / I agree
    "daijoubu",            # It's okay / I'm okay
    "mochiron",            # Of course

    # No / Disagreement
    "iie",                 # No
    "uun",                 # Nope (casual, indicates disagreement/negation)
    "chigaimasu",          # That's incorrect / You're wrong
    "dame",                # No good / Not allowed
    "kekkou desu",         # No, thank you (polite refusal)

    # --- Conversational Fillers & Reactions ---
    "ano",                 # Um...
    "eto",                 # Uh... / Well...
    "naruhodo",            # I see / Indeed
    "hontou",              # Really?
    "maji de",             # Seriously? (slang)
    "sugoi",               # Wow / Amazing
    "yatta",               # Yay! / I did it!
    "sou ka",              # Is that so? / I see (casual)
    "chotto",              # A little / Excuse me for a moment

    # --- Farewells & Leave-Taking ---
    # Standard
    "sayounara",           # Goodbye (can imply a long separation)
    "ja mata",             # See you again
    "dewa mata",           # See you again (more formal)
    "mata ne",             # See you (casual)
    "mata ashita",         # See you tomorrow
    "oyasumi nasai",       # Good night (formal)
    "oyasumi",             # Good night (casual)

    # Situational
    "otsukaresama desu",   # Thank you for your hard work (very common)
    "ittekimasu",          # I'm leaving now (from home)
    "itterasshai",         # Have a good day / Take care (reply to ittekimasu)
    "tadaima",             # I'm home
    "okaeri nasai",        # Welcome home

    # Informal
    "bai bai",             # Bye bye
    "ja ne",               # See ya

    # --- Emojis & Kaomoji ---
    "😊", "😄", "😉", "👍", "🙏", "🙇‍♂️", "🙇‍♀️",
    "(^^)", "(^_^)", "(^o^)", "(^_−)−☆",
    "m(_ _)m", "(T_T)", "(>_<)", "orz"
]


english_keywords = [
    # --- Greetings & Salutations ---
    # Formal & Professional
    "hello",
    "greetings",
    "good morning",
    "good afternoon",
    "good evening",
    "welcome",
    "it's a pleasure to meet you",

    # Informal & Casual
    "hi",
    "hey",
    "heya",
    "hiya",
    "yo",
    "what's up",
    "sup",
    "howdy",
    "hey there",

    # --- How-Are-You & Small Talk ---
    # Asking
    "how are you",
    "how are you doing",
    "how have you been",
    "how's it going",
    "how's everything",
    "what's new",
    "what's happening",
    "you alright?",
    "everything okay?",

    # Replying
    "i'm fine, thank you",
    "i'm doing well",
    "can't complain",
    "not bad",
    "pretty good",
    "so-so",
    "could be better",
    "all good",

    # --- Politeness & Common Courtesies ---
    # Thanks
    "thank you",
    "thanks",
    "thanks a lot",
    "thank you very much",
    "i appreciate it",
    "much obliged",

    # You're Welcome
    "you're welcome",
    "no problem",
    "no worries",
    "don't mention it",
    "my pleasure",
    "anytime",
    "of course",

    # Please
    "please",
    "if you please",
    "if you don't mind",

    # Apologies
    "sorry",
    "my apologies",
    "i apologize",
    "my bad",
    "excuse me",
    "pardon me",

    # --- Agreement & Disagreement ---
    # Agreement / Affirmation
    "yes",
    "yep",
    "yeah",
    "yup",
    "yah",
    "ok",
    "okay",
    "sure",
    "certainly",
    "of course",
    "definitely",
    "absolutely",
    "agreed",
    "right",
    "correct",
    "exactly",
    "for sure",

    # Positive Feedback
    "cool",
    "awesome",
    "great",
    "nice",
    "sweet",
    "perfect",
    "excellent",
    "fantastic",
    "wonderful",

    # Disagreement
    "no",
    "nope",
    "nah",
    "i disagree",
    "not really",
    "i'm not so sure",

    # --- Conversational Fillers ---
    "well",
    "so",
    "um",
    "uh",
    "like",
    "actually",
    "basically",
    "i mean",
    "you know",

    # --- Farewells & Leave-Taking ---
    # Standard & Formal
    "goodbye",
    "farewell",
    "take care",
    "have a good day",
    "have a nice day",
    "all the best",

    # Informal
    "bye",
    "bye bye",
    "see you",
    "see you soon",
    "see you later",
    "catch you later",
    "later",
    "peace",
    "i'm out",

    # --- Common Chat Acronyms ---
    "lol",
    "lmao",
    "rofl",
    "brb",
    "omg",
    "btw",
    "imo",
    "imho",
    "thx",
    "np",
    "ty",

    # --- Emojis ---
    "🙂", "😊", "😀", "😄", "😉", "👍", "👌", "😂", "🙏", "👋"
]



KEYWORD_MAP = {
    "hindi": hindi_keywords,
    "japanese": japanese_keywords,
    "french": french_keywords,
    "german": german_keywords,
    "english": english_keywords,
}


def normalize_and_tokenize(text: str) -> list[str]:
    # Remove punctuation and split into lowercase words
    return re.findall(r"\b\w+\b", text.lower())


def detect_any_greeting_language(user_input: str, bot_languages: list[str]) -> str | None:
    """
    Returns a matched greeting language only if input is 2–3 words long.
    Prioritizes the languages supported by the bot.
    """
    tokens = normalize_and_tokenize(user_input)

    # ✅ Match only if input has between 2 and 3 words
    if len(tokens) < 2 or len(tokens) > 3:
        return None  # 🟡 Skip keyword detection for long inputs

    # 1. First try to match supported languages
    for lang in bot_languages:
        if lang in KEYWORD_MAP:
            for word in KEYWORD_MAP[lang]:
                if word in tokens:
                    return lang

    # 2. Then check for unsupported keyword matches (to reject)
    for lang in KEYWORD_MAP:
        if lang not in bot_languages:
            for word in KEYWORD_MAP[lang]:
                if word in tokens:
                    return lang

   return None


def detect_language_with_model(text: str) -> str | None:
    """Uses the specialized model to get a language label ('hin', 'eng', 'hin-eng')."""
    if not HINGLISH_DETECTOR or not isinstance(text, str) or not text.strip():
        return None
    try:
        prediction = HINGLISH_DETECTOR(text)[0]
        return prediction['label']  # Return the actual label (e.g., 'hin')
    except Exception:
        return None

def is_devanagari(text: str) -> bool:
    return any('\u0900' <= char <= '\u097F' for char in text)


# -----------------------------
# --- FastAPI Request Model ---
# -----------------------------

class InputPayload(BaseModel):
    bot_id: str
    user_input: str

# -----------------------------
# --- Language Detection API ---
# -----------------------------
@app.post("/language_check")
async def language_check(payload: InputPayload):
    debug_info = {
        "bot_id": payload.bot_id,
        "input": payload.user_input,
        "used": [],
        "result": None,
        "detected_language": None,
    }

    if payload.bot_id not in BOT_LANGUAGE_MAP:
        debug_info["used"].append("invalid_bot_id")
        return {
            "supported": False,
            "message": "Invalid bot_id. Please check your bot selection.",
            "debug_info": debug_info
        }

    supported_languages = BOT_LANGUAGE_MAP[payload.bot_id]


  # Step 0: If Hindi is supported, do Devanagari detection first
    if 'hindi' in supported_languages :
        if is_devanagari(payload.user_input):
            debug_info["used"].append("devanagari -> lingua")
            detected_language_enum = DETECTOR.detect_language_of(payload.user_input)
            if detected_language_enum:
                detected_lang = detected_language_enum.name.lower()
                debug_info["detected_language"] = detected_lang
                if detected_lang in supported_languages:
                    debug_info["result"] = "accepted: devanagari lingua"
                    return {"supported": True, "debug_info": debug_info}
                else:
                    debug_info["result"] = "rejected: devanagari lingua"
                    return {"supported": False, "message": BOT_PERSONALITY_MAP[payload.bot_id], "debug_info": debug_info}
        else:
            # Hinglish model if Latin-script
            debug_info["used"].append("hinglish_model")
            model_detected_label = detect_language_with_model(payload.user_input)
            if model_detected_label:
                debug_info["detected_language"] = model_detected_label
                label = model_detected_label.lower()

                hindi_labels = ['hin', 'hin-eng', 'hi']
                english_labels = ['eng', 'en']
                
                is_supported = (
                    (label in hindi_labels and 'hindi' in supported_languages) or
                    (label in english_labels and 'english' in supported_languages)
                )
                
                if is_supported:
                    debug_info["result"] = "accepted: hinglish_model"
                    return {"supported": True, "debug_info": {
                            "bot_id": payload.bot_id,
                            "input": payload.user_input,
                            "used": ["hinglish_model"],
                            "result": "accepted",
                            "detected_language": label,
                            "supported_languages": supported_languages
                }
                    }
                else:
                    debug_info["result"] = "rejected: hinglish_model"
                    return {"supported": False, "message": BOT_PERSONALITY_MAP[payload.bot_id], "debug_info": {
                                    "bot_id": payload.bot_id,
                                    "input": payload.user_input,
                                    "used": ["hinglish_model"],
                                    "result": "rejected: hinglish_model",
                                    "detected_language": label,
                                    "supported_languages": supported_languages
                                }
                            }
            else:
                debug_info["used"].append("hinglish_model_failed")
  # ✅ Step 1: Greeting/Keyword Detection (now runs only for 2–3 word inputs)
    detected_greeting_lang = detect_any_greeting_language(payload.user_input, supported_languages)
    if detected_greeting_lang:
        debug_info["used"].append("keyword_match")
        debug_info["detected_language"] = detected_greeting_lang

        if detected_greeting_lang in supported_languages:
            debug_info["result"] = "accepted: keyword in supported"
            return {"supported": True, "debug_info": debug_info}
        else:
            debug_info["result"] = "rejected: keyword in unsupported"
            return {
                "supported": False,
                "message": BOT_PERSONALITY_MAP[payload.bot_id],
                "debug_info": debug_info
            }

    # Step 2: Final Fallback → Lingua detector
    debug_info["used"].append("final_lingua_fallback")
    detected_language_enum = DETECTOR.detect_language_of(payload.user_input)
    if detected_language_enum:
        detected_lang = detected_language_enum.name.lower()
        debug_info["detected_language"] = detected_lang
        if detected_lang in supported_languages:
            debug_info["result"] = "accepted: fallback lingua"
            return {"supported": True, "debug_info": debug_info}
        else:
            debug_info["result"] = "rejected: fallback lingua"
            return {"supported": False, "message": BOT_PERSONALITY_MAP[payload.bot_id], "debug_info": debug_info}

    # Step 3: Nothing detected — allow fallback
    debug_info["used"].append("final_fallback")
    debug_info["result"] = "accepted: no detection, assumed safe"
    return {"supported": True, "debug_info": debug_info}

