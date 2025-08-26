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
