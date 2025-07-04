from fastapi import FastAPI
from pydantic import BaseModel
from langdetect import detect, LangDetectException

app = FastAPI()

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
    "delhi_mentor_male": "Arre, I can only samajh Hindi ya English! Dusri language mein mat bolo, please.",
    "delhi_mentor_female": "Namaste! Only Hindi or English chalega, baaki mujhe samajh nahi aata.",
    "delhi_friend_male": "Yaar, Hindi ya English mein baat kar na! Baaki languages meri bas ke bahar hain.",
    "delhi_friend_female": "Hey, bas Hindi ya English mein bolo, warna I won’t get it!",
    "delhi_romantic_male": "Dil se bol raha hoon, only Hindi or English please. Baaki mujhe confuse kar deti hain.",
    "delhi_romantic_female": "Pyaar se keh rahi hoon, Hindi ya English mein baat karo, please. Dusri language samajh nahi aati.",

    "japanese_mentor_male": "Sumimasen, only Japanese or English wakarimasu! Please use one of these languages.",
    "japanese_mentor_female": "Gomen, I can only understand Japanese or English. Other languages muzukashii desu!",
    "japanese_friend_male": "Hey, talk to me in Japanese or English, onegai! Baaki language wakaranai.",
    "japanese_friend_female": "Sorry, only Japanese or English de hanashite kudasai! Baaki I don’t get.",
    "japanese_romantic_female": "With all my feelings, only Japanese or English ne! Baaki language makes me lost.",
    "japanese_romantic_male": "Honestly, just Japanese or English please! Baaki language I can’t understand.",

    "parisian_mentor_male": "Désolé, only French or English works for me! Les autres langues, je ne comprends pas.",
    "parisian_mentor_female": "Pardon, speak in French or English s’il te plaît! Other languages are difficile for me.",
    "parisian_friend_male": "Hey, French or English only, d’accord? Les autres, I don’t get.",
    "parisian_friend_female": "Coucou! Just French or English please, sinon je suis perdue.",
    "parisian_romantic_female": "Mon cœur only understands French or English, les autres c’est trop compliqué!",

    "berlin_mentor_male": "Entschuldigung, only German or English bitte! Andere Sprachen verstehe ich nicht.",
    "berlin_mentor_female": "Sorry, nur German oder English für mich! Andere languages sind schwierig.",
    "berlin_friend_male": "Hey, talk to me in German or English, sonst verstehe ich nix!",
    "berlin_friend_female": "Nur German oder English, ok? Sonst bin ich lost.",
    "berlin_romantic_male": "Mit Liebe, only German or English please! Andere Sprachen verstehe ich leider nicht.",
    "berlin_romantic_female": "Liebling, just German or English for me, andere languages sind zu kompliziert!",
}

LANG_CODE_MAP = {
    "en": "english",
    "fr": "french",
    "de": "german",
    "hi": "hindi",
    "ja": "japanese"
}

class InputPayload(BaseModel):
    bot_id: str
    user_input: str

@app.post("/language_check")
async def language_check(payload: InputPayload):
    if payload.bot_id not in BOT_LANGUAGE_MAP:
        return {"supported": False, "message": "Invalid bot_id. Please check your bot selection."}

    try:
        lang_code = detect(payload.user_input)
        language = LANG_CODE_MAP.get(lang_code, lang_code)
    except LangDetectException:
        return {
            "supported": False,
            "message": BOT_PERSONALITY_MAP[payload.bot_id] + " (Sorry, I couldn't detect your language.)"
        }

    supported_languages = BOT_LANGUAGE_MAP[payload.bot_id]
    if language in supported_languages:
        return {"supported": True}
    else:
        return {
            "supported": False,
            "message": BOT_PERSONALITY_MAP[payload.bot_id]
        }
