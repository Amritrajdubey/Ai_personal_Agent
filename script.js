document.getElementById("goalForm").addEventListener("submit", async function (e) {
    e.preventDefault();

    const goal = document.getElementById("goal").value;
    const topic = document.getElementById("topic").value;
    const deadline = document.getElementById("deadline").value;
    const hours = document.getElementById("hours").value;

    const planContainer = document.getElementById("planContainer");
    const planOutput = document.getElementById("planOutput");
    planOutput.textContent = "Generating your personalized plan... Please wait.";
    planContainer.classList.remove("hidden");

    try {
        const res = await fetch("http://localhost:3000/generate-plan", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ goal, topic, deadline, hours })
        });

        if (!res.ok) throw new Error("Failed to fetch plan");

        const data = await res.json();
        planOutput.textContent = data.plan || "No plan generated.";
    } catch (error) {
        console.error(error);
        planOutput.textContent = "Error generating plan. Please try again.";
    }
});
