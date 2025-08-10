import express from "express";
import cors from "cors";
import dotenv from "dotenv";
import OpenAI from "openai";

dotenv.config();
const app = express();
const port = 3000;

// Middleware
app.use(cors());
app.use(express.json());

// Initialize OpenAI client
const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY
});

// Route to handle goal planning
app.post("/generate-plan", async (req, res) => {
  try {
    const { goal, topic, deadline, availableHours } = req.body;

    const prompt = `
    You are a smart AI coach. Based on the following details:
    Goal: ${goal}
    Topic: ${topic}
    Deadline: ${deadline}
    Available hours per day: ${availableHours}
    
    Provide a detailed step-by-step daily plan to achieve the goal within the deadline. 
    Also include motivational tips and key checkpoints.
    `;

    const completion = await openai.chat.completions.create({
      model: "gpt-4o-mini",
      messages: [
        { role: "system", content: "You are a helpful and motivational AI coach." },
        { role: "user", content: prompt }
      ]
    });

    res.json({
      plan: completion.choices[0].message.content
    });
  } catch (error) {
    console.error(error);
    res.status(500).json({ error: "Something went wrong" });
  }
});

app.listen(port, () => {
  console.log(`Backend server running on http://localhost:${port}`);
});
