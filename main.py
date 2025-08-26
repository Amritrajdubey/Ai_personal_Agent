### ===============================
### BACKEND (FastAPI + SQLite)
### File: backend/main.py
### ===============================

import os
import sqlite3
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from openai import OpenAI
import json

# Load environment variables
load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=API_KEY)

# Initialize FastAPI
app = FastAPI()

# Enable CORS so frontend (React) can call backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database setup
DB_NAME = "goals.db"

conn = sqlite3.connect(DB_NAME, check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS goals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    user_name TEXT,
    deadline TEXT,
    description TEXT,
    topics TEXT,
    routine TEXT,
    weekday_hours INTEGER,
    weekend_hours INTEGER,
    roadmap TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS tracker (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    goal_id INTEGER,
    date TEXT,
    tasks TEXT,
    comments TEXT,
    FOREIGN KEY(goal_id) REFERENCES goals(id)
)
""")

conn.commit()

# Models
class GoalInput(BaseModel):
    user_name: str
    name: str
    deadline: str
    description: str
    topics: str
    routine: str
    weekday_hours: int
    weekend_hours: int

class TrackerUpdate(BaseModel):
    goal_id: int
    date: str
    tasks: dict
    comments: str

# Routes
@app.post("/generate-goal")
def generate_goal(data: GoalInput):
    # Prompt for GPT
    prompt = f"""
    You are an AI mentor. Create a detailed day-wise roadmap for the following:
    Goal Name: {data.name}
    User: {data.user_name}
    Deadline: {data.deadline}
    Short Description: {data.description}
    Topics: {data.topics}
    Routine: {data.routine}
    Available Hours: Weekdays {data.weekday_hours}, Weekends {data.weekend_hours}
    Format response in JSON with keys: days -> [ { 'day': 'Day 1', 'tasks': ['task1', 'task2'] } ]
    """

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )

    roadmap = response.choices[0].message.content

    cursor.execute("""
        INSERT INTO goals (name, user_name, deadline, description, topics, routine, weekday_hours, weekend_hours, roadmap)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (data.name, data.user_name, data.deadline, data.description, data.topics, data.routine, data.weekday_hours, data.weekend_hours, roadmap))
    conn.commit()

    return {"status": "success", "roadmap": json.loads(roadmap)}

@app.get("/goals")
def get_goals():
    cursor.execute("SELECT id, name, deadline FROM goals")
    rows = cursor.fetchall()
    return [{"id": r[0], "name": r[1], "deadline": r[2]} for r in rows]

@app.get("/goal/{goal_id}")
def get_goal(goal_id: int):
    cursor.execute("SELECT * FROM goals WHERE id=?", (goal_id,))
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Goal not found")
    return {
        "id": row[0],
        "name": row[1],
        "user_name": row[2],
        "deadline": row[3],
        "description": row[4],
        "topics": row[5],
        "routine": row[6],
        "weekday_hours": row[7],
        "weekend_hours": row[8],
        "roadmap": json.loads(row[9])
    }

@app.post("/update-tracker")
def update_tracker(data: TrackerUpdate):
    cursor.execute("""
        INSERT INTO tracker (goal_id, date, tasks, comments)
        VALUES (?, ?, ?, ?)
    """, (data.goal_id, data.date, json.dumps(data.tasks), data.comments))
    conn.commit()
    return {"status": "tracker updated"}

@app.delete("/delete-goal/{goal_id}")
def delete_goal(goal_id: int):
    cursor.execute("DELETE FROM goals WHERE id=?", (goal_id,))
    cursor.execute("DELETE FROM tracker WHERE goal_id=?", (goal_id,))
    conn.commit()
    return {"status": "goal deleted"}

