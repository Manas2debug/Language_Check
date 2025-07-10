from fastapi import FastAPI
from pydantic import BaseModel
from lingua import Language, LanguageDetectorBuilder
from fastapi.middleware.cors import CORSMiddleware

# --- Lingua Setup ---
# 1. Define all languages that any bot might use.
ALL_SUPPORTED_LANGUAGES = [
    Language.ENGLISH,
    Language.HINDI,
    Language.JAPANESE,
    Language.FRENCH,
    Language.GERMAN
]

# 2. Build the detector once when the application starts for efficiency.
# .with_preloaded_language_models() loads models into memory for faster detection.
DETECTOR = LanguageDetectorBuilder.from_languages(
    *ALL_SUPPORTED_LANGUAGES
).with_preloaded_language_models().build()


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



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

class InputPayload(BaseModel):
    bot_id: str
    user_input: str

@app.post("/language_check")
async def language_check(payload: InputPayload):
    if payload.bot_id not in BOT_LANGUAGE_MAP:
        return {"supported": False, "message": "Invalid bot_id. Please check your bot selection."}

    # Use the Lingua detector
    detected_language_enum = DETECTOR.detect_language_of(payload.user_input)

    # Lingua returns None if it cannot reliably determine the language
    if detected_language_enum is None:
        return {
            "supported": False,
            "message": BOT_PERSONALITY_MAP[payload.bot_id] + " (Sorry, I couldn't detect your language.)"
        }

    # Convert the Lingua Enum (e.g., Language.ENGLISH) to a lowercase string ('english')
    language = detected_language_enum.name.lower()

    supported_languages = BOT_LANGUAGE_MAP[payload.bot_id]
    if language in supported_languages:
        return {"supported": True}
    else:
        return {
            "supported": False,
            "message": BOT_PERSONALITY_MAP[payload.bot_id]
        }
