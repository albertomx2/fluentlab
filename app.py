import json
import os
import random
import re
import sqlite3
import unicodedata
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

ROOT = Path(__file__).parent
DB_PATH = Path("/data/english-lab.db")
app = FastAPI(title="FluentLab", version="1.0.0")

LESSONS = [
    {"id":"first","level":"B1","order":1,"title":"First conditional","subtitle":"Real future possibilities","formula":"If + present, will + infinitive","summary":"Use it for a realistic future condition and its likely result.","examples":["If I study consistently, I’ll improve.","Unless you revise, you won’t remember it."],"notes":["The if-clause normally uses present simple, not will.","Unless means if…not."]},
    {"id":"second","level":"B1","order":2,"title":"Second conditional","subtitle":"Imaginary present or future","formula":"If + past, would + infinitive","summary":"Use it for hypothetical, unlikely or impossible situations now or later.","examples":["If I had more time, I would read every day.","If I were you, I’d practise aloud."],"notes":["Were is preferred for all persons in formal English.","Could and might can replace would."]},
    {"id":"zero","level":"B2","order":3,"title":"Zero conditional","subtitle":"Facts, habits and rules","formula":"If + present, present","summary":"Use it when the condition always produces the same result.","examples":["If you heat ice, it melts.","When I meet a new word, I save it."],"notes":["When can often replace if.","Imperatives are possible in the result clause."]},
    {"id":"third","level":"B2","order":4,"title":"Third conditional","subtitle":"Unreal past and regret","formula":"If + past perfect, would have + participle","summary":"Imagine a different past and its impossible past result.","examples":["If I had revised, I would have passed.","Had she known, she might have helped."],"notes":["Both events belong to the past.","Might have and could have express different degrees of certainty."]},
    {"id":"mixed-past-present","level":"C1","order":5,"title":"Mixed: past → present","subtitle":"Past cause, present result","formula":"If + past perfect, would + infinitive","summary":"A different past condition would change the present situation.","examples":["If I had moved abroad, I would speak English fluently now."],"notes":["Condition time: past.","Result time: present."]},
    {"id":"mixed-present-past","level":"C1","order":6,"title":"Mixed: present → past","subtitle":"Present state, past consequence","formula":"If + past simple, would have + participle","summary":"A continuing present characteristic explains a different past result.","examples":["If I were more organised, I wouldn’t have missed the deadline."],"notes":["Condition time: present/general.","Result time: past."]},
    {"id":"inversion","level":"C2","order":7,"title":"Conditional inversion","subtitle":"Formal conditionals without if","formula":"Had / Were / Should + subject…","summary":"Create concise, formal conditions by inverting the auxiliary and subject.","examples":["Had I known, I would have acted differently.","Should you need help, call me."],"notes":["Do not keep if after inversion.","Were + subject + to is highly formal."]},
    {"id":"advanced","level":"C2","order":8,"title":"Advanced nuance","subtitle":"Implied, remote and blended conditions","formula":"but for · if it weren’t for · otherwise","summary":"Express conditions through implication, omission and precise modal choices.","examples":["But for your advice, I would have failed.","I was busy; otherwise, I would have joined you."],"notes":["Modal choice changes certainty and attitude.","Context can imply a condition without an if-clause."]},
]

EXERCISES = [
    {"id":"b1-1","lesson":"first","level":"B1","type":"complete","prompt":"If you ___ (practise) every day, you will become more fluent.","answers":["practise","practice"],"explanation":"The first conditional uses present simple in the condition and will in the likely future result.","hint":"The if-clause needs present simple."},
    {"id":"b1-2","lesson":"first","level":"B1","type":"complete","prompt":"Unless she ___ (review) the words, she won’t remember them.","answers":["reviews"],"explanation":"Unless means ‘if she does not’; use present simple after it.","hint":"Third-person singular present."},
    {"id":"b1-3","lesson":"second","level":"B1","type":"complete","prompt":"If I ___ (be) you, I would record myself speaking.","answers":["were"],"explanation":"Were is the standard hypothetical form in ‘If I were you’.","hint":"Use the hypothetical form of be."},
    {"id":"b1-4","lesson":"second","level":"B1","type":"identify","prompt":"If we lived in London, we would use English every day.","options":["Zero conditional","First conditional","Second conditional","Third conditional"],"answers":["Second conditional"],"explanation":"Past simple + would describes an unreal or hypothetical present situation."},
    {"id":"b2-1","lesson":"zero","level":"B2","type":"identify","prompt":"When learners review at intervals, they remember more.","options":["Zero conditional","First conditional","Second conditional","Third conditional"],"answers":["Zero conditional"],"explanation":"Both clauses use present simple to express a general result."},
    {"id":"b2-2","lesson":"zero","level":"B2","type":"complete","prompt":"If a word ___ (appear) in several contexts, it becomes easier to recall.","answers":["appears"],"explanation":"This is a general truth, so both clauses use present simple."},
    {"id":"b2-3","lesson":"third","level":"B2","type":"complete","prompt":"If they had left earlier, they ___ (not miss) the presentation.","answers":["would not have missed","wouldn't have missed"],"explanation":"An unreal past condition takes would have + past participle in the result."},
    {"id":"b2-4","lesson":"third","level":"B2","type":"complete","prompt":"She might have understood if you ___ (explain) it more clearly.","answers":["had explained"],"explanation":"The past condition precedes the imagined past result, so use past perfect."},
    {"id":"b2-5","lesson":"third","level":"B2","type":"identify","prompt":"If I had saved the word, I would have reviewed it later.","options":["First conditional","Second conditional","Third conditional","Mixed conditional"],"answers":["Third conditional"],"explanation":"Both the unreal condition and result refer to the past."},
    {"id":"c1-1","lesson":"mixed-past-present","level":"C1","type":"complete","prompt":"If I had accepted that job abroad, I ___ (speak) English confidently now.","answers":["would speak"],"explanation":"The condition is an unreal past decision; the result describes the present."},
    {"id":"c1-2","lesson":"mixed-past-present","level":"C1","type":"timeline","prompt":"If she had studied linguistics, she would understand this distinction now.","options":["past condition → present result","present condition → past result","past condition → past result","present condition → future result"],"answers":["past condition → present result"],"explanation":"Had studied points to the past; would understand now points to the present."},
    {"id":"c1-3","lesson":"mixed-present-past","level":"C1","type":"complete","prompt":"If he were less impulsive, he ___ (not make) that mistake yesterday.","answers":["would not have made","wouldn't have made"],"explanation":"A present characteristic explains an unreal past consequence."},
    {"id":"c1-4","lesson":"mixed-present-past","level":"C1","type":"timeline","prompt":"If I weren’t afraid of flying, I would have visited you last summer.","options":["past condition → present result","present condition → past result","past condition → past result","future condition → present result"],"answers":["present condition → past result"],"explanation":"The fear is a continuing present state; the missed visit belongs to the past."},
    {"id":"c1-5","lesson":"mixed-past-present","level":"C1","type":"identify","prompt":"If they had invested in training, the team would be stronger now.","options":["Third conditional","Second conditional","Mixed: past → present","Mixed: present → past"],"answers":["Mixed: past → present"],"explanation":"The investment is past, but the strength is evaluated now."},
    {"id":"c2-1","lesson":"inversion","level":"C2","type":"transform","prompt":"Rewrite without ‘if’: If I had realised the risk, I would have refused.","answers":["had i realised the risk, i would have refused","had i realized the risk, i would have refused"],"explanation":"Third-conditional inversion begins with Had + subject + past participle.","hint":"Begin with Had I…"},
    {"id":"c2-2","lesson":"inversion","level":"C2","type":"complete","prompt":"___ you require further clarification, please contact me.","answers":["should"],"explanation":"Should + subject creates a formal, tentative future condition."},
    {"id":"c2-3","lesson":"advanced","level":"C2","type":"transform","prompt":"Complete with two words: ___ ___ your support, the project would have collapsed.","answers":["but for"],"explanation":"But for means ‘if it had not been for’ and introduces the decisive condition."},
    {"id":"c2-4","lesson":"advanced","level":"C2","type":"identify","prompt":"I was abroad at the time; otherwise, I would have attended the hearing.","options":["An explicit first conditional","An implied third conditional","A zero conditional","A mixed present-to-past conditional"],"answers":["An implied third conditional"],"explanation":"Otherwise implies ‘if I had not been abroad’, followed by an unreal past result."},
    {"id":"c2-5","lesson":"advanced","level":"C2","type":"timeline","prompt":"Were it not for her patience, the negotiations would have failed months ago.","options":["present state → past result","past event → present result","future possibility → future result","past event → past result"],"answers":["present state → past result"],"explanation":"Her patience is treated as a continuing condition; the imagined failure is in the past."},
]

LEVEL_RANK = {"B1":1,"B2":2,"C1":3,"C2":4}
POS_NAMES = {"n":"noun","v":"verb","adj":"adjective","adv":"adverb","u":"other"}
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:1.5b")

def db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.on_event("startup")
def startup():
    with db() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS vocabulary(
          id INTEGER PRIMARY KEY, word TEXT UNIQUE COLLATE NOCASE, lemma TEXT, part_of_speech TEXT,
          definition TEXT, example TEXT, phonetic TEXT, audio_url TEXT, synonyms TEXT DEFAULT '[]',
          level TEXT, frequency REAL DEFAULT 0, mastery INTEGER DEFAULT 0,
          next_review TEXT, created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS attempts(
          id INTEGER PRIMARY KEY, exercise_id TEXT, level TEXT, exercise_type TEXT,
          correct INTEGER NOT NULL, answer TEXT, created_at TEXT NOT NULL
        );
        """)
        columns = {row["name"] for row in conn.execute("PRAGMA table_info(vocabulary)")}
        if "kind" not in columns: conn.execute("ALTER TABLE vocabulary ADD COLUMN kind TEXT DEFAULT 'word'")
        if "ai_enriched" not in columns: conn.execute("ALTER TABLE vocabulary ADD COLUMN ai_enriched INTEGER DEFAULT 0")
        if "ai_note" not in columns: conn.execute("ALTER TABLE vocabulary ADD COLUMN ai_note TEXT DEFAULT ''")

def clean_answer(value: str) -> str:
    value = unicodedata.normalize("NFKC", value or "").lower().strip()
    value = value.replace("’", "'")
    return re.sub(r"[.!?]+$", "", re.sub(r"\s+", " ", value))

def estimate_level(frequency: float, word: str) -> str:
    if " " in word:
        return "C1"
    if frequency >= 45: return "B1"
    if frequency >= 8: return "B2"
    if frequency >= 1: return "C1"
    return "C2"

async def enrich_word(word: str):
    lookup_word = re.sub(r"^to\s+", "", word).strip()
    lemma = lookup_word
    definition, example, phonetic, audio, synonyms, pos = "", "", "", "", [], "other"
    frequency = 0.0
    async with httpx.AsyncClient(timeout=3, follow_redirects=True) as client:
        try:
            response = await client.get(f"https://api.dictionaryapi.dev/api/v2/entries/en/{lookup_word}")
            if response.status_code == 200:
                entry = response.json()[0]
                phonetic = entry.get("phonetic") or next((p.get("text") for p in entry.get("phonetics",[]) if p.get("text")), "")
                audio = next((p.get("audio") for p in entry.get("phonetics",[]) if p.get("audio")), "")
                meanings = entry.get("meanings") or []
                if word.startswith("to "):
                    verb_meaning = next((meaning for meaning in meanings if meaning.get("partOfSpeech") == "verb"), None)
                    if verb_meaning: meanings = [verb_meaning]
                if meanings:
                    pos = meanings[0].get("partOfSpeech") or pos
                    defs = meanings[0].get("definitions") or []
                    if defs:
                        definition = defs[0].get("definition") or ""
                        example = defs[0].get("example") or ""
                        synonyms = (defs[0].get("synonyms") or meanings[0].get("synonyms") or [])[:6]
        except (httpx.HTTPError, ValueError, KeyError):
            pass
        try:
            response = await client.get("https://api.datamuse.com/words", params={"sp":lookup_word,"md":"dpf","max":1})
            if response.status_code == 200 and response.json():
                item = response.json()[0]
                lemma = item.get("word") or lemma
                tags = item.get("tags") or []
                pos_tag = next((tag for tag in tags if tag in POS_NAMES), None)
                if pos == "other" and pos_tag: pos = POS_NAMES[pos_tag]
                if not definition and item.get("defs"):
                    raw_definition = item["defs"][0]
                    definition = raw_definition.split("\t", 1)[-1].strip()
                freq_tag = next((tag for tag in tags if tag.startswith("f:")), "f:0")
                frequency = float(freq_tag.split(":",1)[1])
        except (httpx.HTTPError, ValueError, IndexError):
            pass
    if not definition:
        definition = "Definition unavailable. Add a personal note when you review this word."
    if not example:
        example = f"I want to use the word “{word}” naturally in conversation."
    return {"lemma":lemma,"part_of_speech":pos,"definition":definition,"example":example,
            "phonetic":phonetic,"audio_url":audio,"synonyms":synonyms,
            "frequency":frequency,"level":estimate_level(frequency, word)}

def fallback_kind(word: str, pos: str) -> str:
    if word.startswith("to "): return "verb" if len(word.split()) == 2 else "phrasal verb"
    if " " in word: return "expression"
    return pos if pos in {"noun", "verb", "adjective", "adverb"} else "word"

async def ai_enrich(word: str, evidence: dict) -> dict:
    typed_base = re.sub(r"^to\s+", "", word).strip()
    corrected = evidence.get("lemma", typed_base).lower() != typed_base.lower()
    analysis_entry = evidence["lemma"] if corrected else word
    prompt_evidence = {key:value for key,value in evidence.items() if key not in {"example", "audio_url", "synonyms"}}
    if word.startswith("to ") or evidence.get("definition", "").startswith("Definition unavailable"):
        forced_pos = "verb" if word.startswith("to ") else evidence.get("part_of_speech", "other")
        prompt_evidence = {"part_of_speech":forced_pos,"frequency":evidence.get("frequency",0),"level_hint":evidence.get("level")}
    prompt = f"""You are a careful English lexicographer for Spanish-speaking learners. The learner typed {word!r}. Analyse this entry: {analysis_entry!r}.
The learner may write infinitives as 'to + verb'. If the entry begins with 'to ', it MUST be analysed as a verb or phrasal verb: define the action, never the related noun. If the evidence lemma differs from the entry, treat it as a likely spelling correction and analyse the corrected lemma.
Distinguish a word, verb, phrasal verb, idiom, collocation, expression, compound noun or compound adjective. Choose the most specific category: use expression only when idiom, collocation and compound do not fit.
Return ONLY JSON with keys canonical_form, kind, part_of_speech, definition, example, level, note. Definition and example must be natural concise English. The example MUST be a grammatically correct real sentence that demonstrates the entry's meaning, never a sentence about wanting to learn the entry and never an incorrect double negative. level must be B1, B2, C1 or C2. Analyse the complete expression. Evidence (only a hint; correct it when needed): {json.dumps(prompt_evidence, ensure_ascii=False)}"""
    try:
        async with httpx.AsyncClient(timeout=90) as client:
            response = await client.post(f"{OLLAMA_URL}/api/generate", json={"model":OLLAMA_MODEL,"prompt":prompt,"stream":False,"format":"json","options":{"temperature":0.1,"num_predict":260}})
            response.raise_for_status()
            result = json.loads(response.json()["response"])
        level = str(result.get("level", "")).upper()
        if level not in LEVEL_RANK: level = evidence["level"]
        allowed = {"word","verb","phrasal verb","idiom","collocation","expression","compound noun","compound adjective"}
        kind = str(result.get("kind", "")).lower().strip()
        if kind not in allowed: kind = fallback_kind(word, result.get("part_of_speech", evidence["part_of_speech"]))
        note = str(result.get("note", ""))
        pos = str(result.get("part_of_speech") or evidence["part_of_speech"]).lower()
        context = f"{note} {evidence.get('definition','')}".lower()
        if kind == "expression" and ("idiom" in context or "figurative" in context): kind = "idiom"
        elif kind == "expression" and "collocation" in context: kind = "collocation"
        elif kind in {"expression", "collocation"} and pos == "noun" and "-" in word: kind = "compound noun"
        elif kind == "expression" and pos in {"phrase", "noun phrase"} and len(word.split()) >= 3: kind = "collocation"
        example = result.get("example") or evidence["example"]
        example_overrides = {
            "by no means":"The task is by no means easy, but we can finish it together.",
            "literacy":"Improving digital literacy helps people navigate information more confidently.",
            "silver bullet":"There is no silver bullet for becoming fluent; steady practice matters most."
        }
        example = example_overrides.get(analysis_entry.lower(), example)
        return {**evidence,"lemma":evidence["lemma"] if corrected else (result.get("canonical_form") or evidence["lemma"]),"kind":kind,
                "part_of_speech":pos,
                "definition":result.get("definition") or evidence["definition"],"example":example,
                "level":level,"ai_note":note,"ai_enriched":1}
    except (httpx.HTTPError, ValueError, KeyError, TypeError):
        return {**evidence,"kind":fallback_kind(word, evidence["part_of_speech"]),"ai_note":"","ai_enriched":0}

class WordIn(BaseModel):
    word: str = Field(min_length=1, max_length=80)

class CheckIn(BaseModel):
    exercise_id: str
    answer: str

class ReviewIn(BaseModel):
    rating: int = Field(ge=0, le=3)

@app.get("/api/dashboard")
def dashboard():
    with db() as conn:
        words = conn.execute("SELECT COUNT(*) count, COALESCE(AVG(mastery),0) avg FROM vocabulary").fetchone()
        attempts = conn.execute("SELECT COUNT(*) count, COALESCE(SUM(correct),0) correct FROM attempts").fetchone()
        due = conn.execute("SELECT COUNT(*) count FROM vocabulary WHERE next_review IS NULL OR next_review<=?", (datetime.now(timezone.utc).isoformat(),)).fetchone()["count"]
        recent = [dict(row) for row in conn.execute("SELECT * FROM vocabulary ORDER BY id DESC LIMIT 5")]
    accuracy = round(attempts["correct"] * 100 / attempts["count"]) if attempts["count"] else 0
    return {"words":words["count"],"mastery":round(words["avg"]),"attempts":attempts["count"],"accuracy":accuracy,"due":due,"recent":recent}

@app.get("/api/lessons")
def lessons(level: str = "B1"):
    return LESSONS

def personalised_exercise(level: str):
    with db() as conn:
        row = conn.execute("SELECT word FROM vocabulary ORDER BY RANDOM() LIMIT 1").fetchone()
    if not row: return None
    word = row["word"]
    templates = {
      "B1":("If you practise using “%s” today, you ___ (remember) it tomorrow.", ["will remember"], "first", "The first conditional links a realistic present action to its future result."),
      "B2":("If I had reviewed “%s”, I ___ (use) it correctly yesterday.", ["would have used"], "third", "This unreal past situation needs would have + past participle."),
      "C1":("If I had learned “%s” earlier, I ___ (feel) more confident now.", ["would feel"], "mixed-past-present", "A past cause produces an imagined present result."),
      "C2":("Had I not encountered “%s”, I ___ (not add) it to my corpus.", ["would not have added","wouldn't have added"], "inversion", "Had + subject replaces if + past perfect."),
    }
    prompt, answers, lesson, explanation = templates.get(level, templates["B1"])
    return {"id":f"personal-{level}-{word}","lesson":lesson,"level":level,"type":"complete","prompt":prompt % word,"answers":answers,"explanation":explanation,"personalised":True,"word":word}

@app.get("/api/exercises")
def exercises(level: str = "B1", lesson: str | None = None, type: str | None = Query(default=None)):
    pool = [item for item in EXERCISES if item["level"] == level.upper()]
    if lesson: pool = [item for item in pool if item["lesson"] == lesson]
    if type: pool = [item for item in pool if item["type"] == type]
    custom = personalised_exercise(level.upper())
    if custom and not lesson and not type: pool.append(custom)
    random.shuffle(pool)
    return [{k:v for k,v in item.items() if k != "answers"} for item in pool]

@app.post("/api/exercises/check")
def check_exercise(payload: CheckIn):
    exercise = next((item for item in EXERCISES if item["id"] == payload.exercise_id), None)
    if not exercise and payload.exercise_id.startswith("personal-"):
        parts = payload.exercise_id.split("-", 2)
        level = parts[1]
        exercise = personalised_exercise(level)
        if exercise:
            exercise["id"] = payload.exercise_id
    if not exercise: raise HTTPException(404, "Exercise not found")
    given = clean_answer(payload.answer)
    correct = any(given == clean_answer(answer) for answer in exercise["answers"])
    with db() as conn:
        conn.execute("INSERT INTO attempts(exercise_id,level,exercise_type,correct,answer,created_at) VALUES(?,?,?,?,?,?)",
                     (exercise["id"],exercise["level"],exercise["type"],int(correct),payload.answer,datetime.now(timezone.utc).isoformat()))
    return {"correct":correct,"accepted":exercise["answers"],"explanation":exercise["explanation"]}

@app.get("/api/vocabulary")
def vocabulary(level: str | None = None):
    with db() as conn:
        query = "SELECT * FROM vocabulary" + (" WHERE level=?" if level else "") + " ORDER BY created_at DESC"
        rows = conn.execute(query, (level,) if level else ()).fetchall()
    return [{**dict(row),"synonyms":json.loads(row["synonyms"] or "[]")} for row in rows]

@app.post("/api/vocabulary", status_code=201)
async def add_word(payload: WordIn):
    word = re.sub(r"\s+", " ", payload.word.strip().lower())
    if not re.fullmatch(r"[a-zA-Z][a-zA-Z '\-]*", word):
        raise HTTPException(400, "Introduce una palabra o expresión en inglés")
    data = await ai_enrich(word, await enrich_word(word))
    now = datetime.now(timezone.utc).isoformat()
    try:
        with db() as conn:
            cursor = conn.execute("""INSERT INTO vocabulary(word,lemma,part_of_speech,definition,example,phonetic,audio_url,synonyms,level,frequency,next_review,created_at,kind,ai_enriched,ai_note)
              VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (word,data["lemma"],data["part_of_speech"],data["definition"],data["example"],data["phonetic"],data["audio_url"],json.dumps(data["synonyms"]),data["level"],data["frequency"],now,now,data["kind"],data["ai_enriched"],data["ai_note"]))
            item_id = cursor.lastrowid
            row = conn.execute("SELECT * FROM vocabulary WHERE id=?",(item_id,)).fetchone()
    except sqlite3.IntegrityError:
        raise HTTPException(409, "Esta palabra ya está en tu corpus")
    result = dict(row); result["synonyms"] = json.loads(result["synonyms"])
    return result

@app.post("/api/vocabulary/{word_id}/reanalyze")
async def reanalyze_word(word_id: int):
    with db() as conn: row = conn.execute("SELECT * FROM vocabulary WHERE id=?", (word_id,)).fetchone()
    if not row: raise HTTPException(404, "Word not found")
    data = await ai_enrich(row["word"], await enrich_word(row["word"]))
    with db() as conn:
        conn.execute("""UPDATE vocabulary SET lemma=?,part_of_speech=?,definition=?,example=?,phonetic=?,audio_url=?,synonyms=?,level=?,frequency=?,kind=?,ai_enriched=?,ai_note=? WHERE id=?""",
          (data["lemma"],data["part_of_speech"],data["definition"],data["example"],data["phonetic"],data["audio_url"],json.dumps(data["synonyms"]),data["level"],data["frequency"],data["kind"],data["ai_enriched"],data["ai_note"],word_id))
        updated = conn.execute("SELECT * FROM vocabulary WHERE id=?", (word_id,)).fetchone()
    result = dict(updated); result["synonyms"] = json.loads(result["synonyms"] or "[]")
    return result

@app.get("/api/ai/status")
async def ai_status():
    try:
        async with httpx.AsyncClient(timeout=3) as client:
            response = await client.get(f"{OLLAMA_URL}/api/tags"); response.raise_for_status()
        names = [m.get("name", "") for m in response.json().get("models", [])]
        return {"ready":any(name.startswith(OLLAMA_MODEL) for name in names),"model":OLLAMA_MODEL}
    except httpx.HTTPError:
        return {"ready":False,"model":OLLAMA_MODEL}

@app.delete("/api/vocabulary/{word_id}", status_code=204)
def delete_word(word_id: int):
    with db() as conn: conn.execute("DELETE FROM vocabulary WHERE id=?",(word_id,))

@app.get("/api/vocabulary/practice")
def vocabulary_practice(level: str | None = None):
    with db() as conn:
        query = "SELECT * FROM vocabulary" + (" WHERE level=?" if level else "") + " ORDER BY RANDOM() LIMIT 12"
        rows = conn.execute(query,(level,) if level else ()).fetchall()
    result=[]
    for row in rows:
        sentence = row["example"] or f"I want to use the word {row['word']} naturally."
        masked = re.sub(re.escape(row["word"]), "_____", sentence, flags=re.I)
        if masked == sentence: masked = f"Choose the word that matches: {row['definition']}"
        result.append({"id":row["id"],"word":row["word"],"prompt":masked,"definition":row["definition"],"level":row["level"],"part_of_speech":row["part_of_speech"]})
    return result

@app.post("/api/vocabulary/{word_id}/review")
def review_word(word_id: int, payload: ReviewIn):
    with db() as conn:
        row=conn.execute("SELECT * FROM vocabulary WHERE id=?",(word_id,)).fetchone()
        if not row: raise HTTPException(404,"Word not found")
        change=[-15,0,10,20][payload.rating]
        mastery=max(0,min(100,row["mastery"]+change))
        days=[0,1,max(2,mastery//15),max(4,mastery//8)][payload.rating]
        next_review=(datetime.now(timezone.utc)+timedelta(days=days)).isoformat()
        conn.execute("UPDATE vocabulary SET mastery=?,next_review=? WHERE id=?",(mastery,next_review,word_id))
    return {"mastery":mastery,"next_review":next_review}

app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")

@app.get("/{path:path}")
def frontend(path: str):
    return FileResponse(ROOT / "static" / "index.html")
