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


### ===============================
### FRONTEND (React + Tailwind)
### File: frontend/src/App.jsx
### ===============================

import { useState, useEffect } from "react";
import axios from "axios";

export default function App() {
  const [tab, setTab] = useState("get-started");
  const [goals, setGoals] = useState([]);

  useEffect(() => {
    if (tab === "ongoing") {
      axios.get("http://127.0.0.1:8000/goals").then(res => setGoals(res.data));
    }
  }, [tab]);

  return (
    <div className="p-6">
      <div className="flex gap-4 mb-4">
        <button onClick={() => setTab("get-started")} className="px-4 py-2 bg-blue-500 text-white rounded">Get Started</button>
        <button onClick={() => setTab("ongoing")} className="px-4 py-2 bg-green-500 text-white rounded">Ongoing Goals</button>
      </div>

      {tab === "get-started" && <GetStarted />}
      {tab === "ongoing" && <Ongoing goals={goals} />}
    </div>
  );
}

function GetStarted() {
  const [form, setForm] = useState({ user_name:"", name:"", deadline:"", description:"", topics:"", routine:"", weekday_hours:0, weekend_hours:0 });
  const [roadmap, setRoadmap] = useState(null);

  const handleChange = (e) => setForm({...form, [e.target.name]: e.target.value});

  const handleSubmit = () => {
    axios.post("http://127.0.0.1:8000/generate-goal", form).then(res => setRoadmap(res.data.roadmap));
  };

  return (
    <div className="space-y-4">
      <input name="user_name" placeholder="Your Name" onChange={handleChange} className="border p-2 w-full"/>
      <input name="name" placeholder="Goal Name" onChange={handleChange} className="border p-2 w-full"/>
      <input type="date" name="deadline" onChange={handleChange} className="border p-2 w-full"/>
      <input name="description" placeholder="Short Goal" onChange={handleChange} className="border p-2 w-full"/>
      <input name="topics" placeholder="Topics (comma separated)" onChange={handleChange} className="border p-2 w-full"/>
      <input name="weekday_hours" placeholder="Hours on Weekdays" type="number" onChange={handleChange} className="border p-2 w-full"/>
      <input name="weekend_hours" placeholder="Hours on Weekends" type="number" onChange={handleChange} className="border p-2 w-full"/>
      <textarea name="routine" placeholder="Your Daily Routine" onChange={handleChange} className="border p-2 w-full"></textarea>

      <button onClick={handleSubmit} className="px-4 py-2 bg-blue-600 text-white rounded">Generate Roadmap</button>

      {roadmap && (
        <div className="mt-6 border p-4">
          <h2 className="font-bold mb-2">Generated Roadmap</h2>
          {roadmap.days.map((d, i) => (
            <div key={i} className="mb-4">
              <h3 className="font-semibold">{d.day}</h3>
              <ul className="list-disc ml-6">
                {d.tasks.map((t, j) => <li key={j}>{t}</li>)}
              </ul>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function Ongoing({ goals }) {
  const [selected, setSelected] = useState(null);
  const [detail, setDetail] = useState(null);

  const loadGoal = (id) => {
    axios.get(`http://127.0.0.1:8000/goal/${id}`).then(res => setDetail(res.data));
    setSelected(id);
  };

  const deleteGoal = (id) => {
    if(window.confirm("Delete this goal?")){
      axios.delete(`http://127.0.0.1:8000/delete-goal/${id}`).then(() => window.location.reload());
    }
  }

  return (
    <div className="flex gap-6">
      <div className="w-1/3 border-r p-2">
        <h2 className="font-bold mb-2">Your Goals</h2>
        {goals.map(g => (
          <div key={g.id} className="flex justify-between items-center mb-2">
            <button onClick={() => loadGoal(g.id)} className="text-blue-600 underline">{g.name}</button>
            <button onClick={() => deleteGoal(g.id)} className="text-red-500">Delete</button>
          </div>
        ))}
      </div>

      <div className="flex-1 p-2">
        {detail && (
          <div>
            <h2 className="text-xl font-bold mb-2">{detail.name}</h2>
            <h3 className="font-semibold mb-2">Frozen Roadmap</h3>
            {detail.roadmap.days.map((d, i) => (
              <div key={i} className="mb-4">
                <h4 className="font-semibold">{d.day}</h4>
                <ul className="list-disc ml-6">
                  {d.tasks.map((t, j) => <li key={j}>{t}</li>)}
                </ul>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
