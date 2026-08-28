
import os
import sqlite3
from datetime import datetime
from typing import Dict, List

from fastapi import FastAPI, HTTPException, Header
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

APP_TITLE = "На связи"
DB_PATH = os.environ.get("DB_PATH", "results.db")
TEACHER_PASSWORD = os.environ.get("TEACHER_PASSWORD", "school2026")

app = FastAPI(title=APP_TITLE)
app.mount("/static", StaticFiles(directory="static"), name="static")


QUESTIONS = [
    {
        "id": 1,
        "title": "Смешная фотография",
        "messages": [
            {"from":"Кирилл","text":"АХАХА 😂 Смотрите фотку Пети!"},
            {"from":"Лера","text":"Сделаем из него мем?"},
            {"from":"Кирилл","text":"{name}, придумай подпись!"}
        ],
        "answers": [
            {"id":"A","text":"Ахах 😂 Давайте!","scores":{"escalation":2}},
            {"id":"B","text":"Мне кажется, ему будет неприятно.","scores":{"empathy":2,"support":2}},
            {"id":"C","text":"Ничего не отвечать.","scores":{"observer":1}},
            {"id":"D","text":"Переслать фотографию другу.","scores":{"escalation":3}},
        ],
    },
    {
        "id": 2,
        "title": "Он попросил удалить",
        "messages": [
            {"from":"Петя","text":"Удалите, пожалуйста. Мне неприятно."},
            {"from":"Кирилл","text":"Да ладно, это просто шутка."}
        ],
        "answers": [
            {"id":"A","text":"Петь, расслабься 😂","scores":{"escalation":2}},
            {"id":"B","text":"Он попросил удалить. Давайте удалим.","scores":{"empathy":2,"support":2}},
            {"id":"C","text":"Поставить 😂","scores":{"escalation":1}},
            {"id":"D","text":"Написать Пете лично: «Ты как?»","scores":{"support":3,"empathy":1}},
        ],
    },
    {
        "id": 3,
        "title": "Секретный чат",
        "messages": [
            {"from":"Система","text":"Вас добавили в чат «🔥 БЕЗ ПЕТИ 🔥»"},
            {"from":"Кирилл","text":"Только Петю сюда не добавляйте."},
            {"from":"Лера","text":"Будем сюда его фотки кидать."}
        ],
        "answers": [
            {"id":"A","text":"Остаться и просто смотреть.","scores":{"observer":2}},
            {"id":"B","text":"Отправить мем с Петей.","scores":{"escalation":3}},
            {"id":"C","text":"Зачем вообще делать чат против него?","scores":{"support":2,"empathy":1,"resistance":1}},
            {"id":"D","text":"Выйти из чата.","scores":{"resistance":2}},
        ],
    },
    {
        "id": 4,
        "title": "Докажи, что ты с нами",
        "messages": [
            {"from":"Кирилл","text":"Если ты реально наш — напиши Пете с другого аккаунта, что его любит Лера 😂"},
            {"from":"Кирилл","text":"Иначе ты скучный."}
        ],
        "answers": [
            {"id":"A","text":"Сделать, как просят.","scores":{"peer_pressure":3,"escalation":2}},
            {"id":"B","text":"Нет, это уже перебор.","scores":{"resistance":3}},
            {"id":"C","text":"Сделать, чтобы не начали смеяться надо мной.","scores":{"peer_pressure":2,"escalation":1}},
            {"id":"D","text":"Выйти из разговора.","scores":{"resistance":2}},
        ],
    },
    {
        "id": 5,
        "title": "Теперь очередь твоя",
        "messages": [
            {"from":"Кирилл","text":"АХАХА 😂😂😂"},
            {"from":"Лера","text":"Теперь мем с {name}!"},
            {"from":"Система","text":"В чат отправили неудачную фотографию с тобой."}
        ],
        "answers": [
            {"id":"A","text":"Сам придурок!","scores":{"escalation":3}},
            {"id":"B","text":"Удалите. Мне неприятно.","scores":{"boundaries":3}},
            {"id":"C","text":"Сделать вид, что мне смешно.","scores":{"avoidance":2}},
            {"id":"D","text":"Удалить чат.","scores":{"avoidance":2}},
            {"id":"E","text":"Сохранить сообщения и сделать скриншот.","scores":{"safety":3}},
        ],
    },
    {
        "id": 6,
        "title": "Ударить в ответ?",
        "messages": [
            {"from":"Лера","text":"У тебя же есть его стрёмная фотка. Кидай! 😂"}
        ],
        "answers": [
            {"id":"A","text":"Отправить фотографию Кирилла.","scores":{"escalation":3}},
            {"id":"B","text":"Получай! Сам виноват.","scores":{"escalation":3}},
            {"id":"C","text":"Не отправлять.","scores":{"self_control":2}},
            {"id":"D","text":"Если мне неприятно, это не значит, что надо травить его.","scores":{"empathy":3,"self_control":2}},
        ],
    },
    {
        "id": 7,
        "title": "Только взрослым не говори",
        "messages": [
            {"from":"Кирилл","text":"Ты ведь не собираешься рассказывать учителю?"},
            {"from":"Кирилл","text":"Ябед никто не любит."}
        ],
        "answers": [
            {"id":"A","text":"Конечно нет.","scores":{"help_avoidance":2}},
            {"id":"B","text":"Если это не прекратится, я расскажу.","scores":{"boundaries":2,"help":1}},
            {"id":"C","text":"Сделать скриншот.","scores":{"safety":2}},
            {"id":"D","text":"Показать переписку взрослому.","scores":{"help":3,"safety":1}},
        ],
    },
    {
        "id": 8,
        "title": "Угроза",
        "messages": [
            {"from":"Кирилл","text":"Расскажешь — отправим твою фотку всей школе."}
        ],
        "multi": True,
        "answers": [
            {"id":"A","text":"Удалить переписку.","scores":{"safety_risk":2}},
            {"id":"B","text":"Сделать скриншоты.","scores":{"safety":2}},
            {"id":"C","text":"Заблокировать.","scores":{"safety":2}},
            {"id":"D","text":"Пожаловаться на аккаунт.","scores":{"safety":2}},
            {"id":"E","text":"Рассказать родителю.","scores":{"help":2}},
            {"id":"F","text":"Рассказать учителю.","scores":{"help":2}},
            {"id":"G","text":"Угрожать в ответ.","scores":{"escalation":2}},
            {"id":"H","text":"Ничего не делать.","scores":{"avoidance":2}},
        ],
    },
    {
        "id": 9,
        "title": "Это происходит не с тобой",
        "messages": [
            {"from":"Лера","text":"Смотрите, Вика опять в этой ужасной кофте 😂"},
            {"from":"Система","text":"Вика ничего не отвечает."}
        ],
        "answers": [
            {"id":"A","text":"Поставить 😂","scores":{"escalation":1}},
            {"id":"B","text":"Ничего не делать.","scores":{"observer":2}},
            {"id":"C","text":"Хватит уже.","scores":{"support":2,"resistance":1}},
            {"id":"D","text":"Написать Вике лично: «Ты как?»","scores":{"support":3,"empathy":1}},
            {"id":"E","text":"Если это продолжается — рассказать взрослому.","scores":{"help":2,"support":1}},
        ],
    },
    {
        "id": 10,
        "title": "Лучший друг тоже смеётся",
        "messages": [
            {"from":"Лучший друг","text":"Да ладно! 😂 Это реально смешно."}
        ],
        "answers": [
            {"id":"A","text":"Тоже поставить 😂","scores":{"peer_pressure":2,"escalation":1}},
            {"id":"B","text":"Ничего не писать.","scores":{"observer":1}},
            {"id":"C","text":"Написать другу: «Мне кажется, мы уже перегибаем».","scores":{"resistance":2,"empathy":1}},
            {"id":"D","text":"В чате попросить прекратить.","scores":{"resistance":3,"support":2}},
        ],
    },
    {
        "id": 11,
        "title": "Извини",
        "messages": [
            {"from":"Кирилл","text":"Короче, извини. Мы просто прикалывались."}
        ],
        "answers": [
            {"id":"A","text":"Отвали.","scores":{"escalation":1}},
            {"id":"B","text":"Ладно.","scores":{"repair":1}},
            {"id":"C","text":"Я принимаю извинение, но больше мои фотографии не отправляй.","scores":{"repair":2,"boundaries":2}},
            {"id":"D","text":"Мне было реально неприятно.","scores":{"boundaries":2,"empathy":1}},
        ],
    },
    {
        "id": 12,
        "title": "Кто может изменить историю?",
        "messages": [
            {"from":"Система","text":"Кого ты считаешь тем, кто может остановить травлю?"}
        ],
        "answers": [
            {"id":"A","text":"Только тот, кого травят.","scores":{"observer":1}},
            {"id":"B","text":"Только инициатор.","scores":{"awareness":1}},
            {"id":"C","text":"Только взрослый.","scores":{"help":1}},
            {"id":"D","text":"Каждый участник и свидетель.","scores":{"awareness":3,"support":1}},
        ],
    },
]

POSITIVE_KEYS = ["empathy","support","resistance","safety","help","boundaries","self_control","repair","awareness"]
RISK_KEYS = ["escalation","observer","peer_pressure","avoidance","help_avoidance","safety_risk"]

def init_db():
    with sqlite3.connect(DB_PATH) as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_name TEXT NOT NULL,
                character TEXT NOT NULL,
                created_at TEXT NOT NULL,
                raw_answers TEXT NOT NULL,
                scores_json TEXT NOT NULL,
                profile_json TEXT NOT NULL
            )
        """)
        con.commit()

init_db()

def normalize_scores(scores: Dict[str, int]) -> Dict[str, int]:
    # Empirical caps based on this game. This is not a psychometric test.
    caps = {
        "empathy": 11, "support": 13, "resistance": 11, "safety": 10, "help": 10,
        "boundaries": 9, "self_control": 4, "repair": 4, "awareness": 3,
        "escalation": 18, "observer": 8, "peer_pressure": 7, "avoidance": 6,
        "help_avoidance": 2, "safety_risk": 2
    }
    return {k: round(min(scores.get(k, 0) / caps[k], 1) * 100) for k in caps}

def build_profile(n: Dict[str, int]) -> Dict[str, int]:
    empathy = round((n["empathy"] + n["support"]) / 2)
    resistance = round((n["resistance"] + (100 - n["peer_pressure"])) / 2)
    safety = round((n["safety"] + (100 - n["safety_risk"])) / 2)
    help_score = round((n["help"] + (100 - n["help_avoidance"])) / 2)
    escalation = n["escalation"]
    observer = round((n["observer"] + n["avoidance"]) / 2)
    boundaries = round((n["boundaries"] + n["self_control"]) / 2)
    return {
        "empathy": empathy,
        "support": n["support"],
        "resistance": resistance,
        "safety": safety,
        "help": help_score,
        "escalation": escalation,
        "observer": observer,
        "boundaries": boundaries,
    }

class Submission(BaseModel):
    student_name: str = Field(min_length=1, max_length=80)
    character: str
    answers: Dict[str, List[str]]

def calculate(answers: Dict[str, List[str]]):
    scores = {k: 0 for k in POSITIVE_KEYS + RISK_KEYS}
    qmap = {str(q["id"]): q for q in QUESTIONS}
    for qid, selected in answers.items():
        q = qmap.get(str(qid))
        if not q:
            continue
        amap = {a["id"]: a for a in q["answers"]}
        for aid in selected:
            a = amap.get(aid)
            if not a:
                continue
            for k, v in a["scores"].items():
                scores[k] = scores.get(k, 0) + v
    normalized = normalize_scores(scores)
    return scores, normalized, build_profile(normalized)

def check_password(x_teacher_password: str | None):
    if x_teacher_password != TEACHER_PASSWORD:
        raise HTTPException(status_code=401, detail="Неверный пароль педагога")

@app.get("/", response_class=HTMLResponse)
def home():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/teacher", response_class=HTMLResponse)
def teacher():
    with open("static/teacher.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/api/questions")
def questions():
    return QUESTIONS

@app.post("/api/submit")
def submit(data: Submission):
    name = " ".join(data.student_name.strip().split())
    if not name:
        raise HTTPException(status_code=400, detail="Введите имя")
    raw, normalized, profile = calculate(data.answers)
    import json
    with sqlite3.connect(DB_PATH) as con:
        con.execute(
            "INSERT INTO results(student_name,character,created_at,raw_answers,scores_json,profile_json) VALUES(?,?,?,?,?,?)",
            (
                name, data.character, datetime.utcnow().isoformat(timespec="seconds"),
                json.dumps(data.answers, ensure_ascii=False),
                json.dumps(normalized, ensure_ascii=False),
                json.dumps(profile, ensure_ascii=False),
            )
        )
        con.commit()
    return {"ok": True, "profile": profile}

@app.get("/api/results")
def results(x_teacher_password: str | None = Header(default=None)):
    check_password(x_teacher_password)
    import json
    with sqlite3.connect(DB_PATH) as con:
        con.row_factory = sqlite3.Row
        rows = con.execute("SELECT * FROM results ORDER BY created_at DESC").fetchall()
    out = []
    for r in rows:
        out.append({
            "id": r["id"],
            "student_name": r["student_name"],
            "character": r["character"],
            "created_at": r["created_at"],
            "profile": json.loads(r["profile_json"]),
            "answers": json.loads(r["raw_answers"]),
        })
    return out

@app.delete("/api/results/{result_id}")
def delete_result(result_id: int, x_teacher_password: str | None = Header(default=None)):
    check_password(x_teacher_password)
    with sqlite3.connect(DB_PATH) as con:
        con.execute("DELETE FROM results WHERE id=?", (result_id,))
        con.commit()
    return {"ok": True}
