const express = require("express");
const cors = require("cors");
const bodyParser = require("body-parser");
const axios = require("axios");
require("dotenv").config();

const app = express();
app.use(cors());
app.use(bodyParser.json());

app.post("/generate-plan", async (req, res) => {
  const { goal, deadline, availableHours, dailyRoutine } = req.body;

  const prompt = `
You are a goal-tracking AI assistant.
Goal: ${goal}
Deadline: ${deadline}
Available hours per day: ${availableHours}
Daily routine: ${dailyRoutine}
Create a daily actionable plan until the goal is reached, including checkpoints and advice.
`;

  try {
    const response = await axios.post(
      "https://api.openai.com/v1/chat/completions",
      {
        model: "gpt-4o-mini",
        messages: [{ role: "user", content: prompt }],
      },
      {
        headers: {
          Authorization: `Bearer ${process.env.OPENAI_API_KEY}`,
          "Content-Type": "application/json",
        },
      }
    );

    res.json({ plan: response.data.choices[0].message.content });
  } catch (error) {
    console.error(error);
    res.status(500).json({ error: "Error generating plan" });
  }
});

app.listen(3000, () => {
  console.log("Backend running on http://localhost:3000");
});
