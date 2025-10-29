document.addEventListener("DOMContentLoaded", function () {
  const form = document.getElementById("wordForm");
  const resultDiv = document.getElementById("result");
  const loader = document.getElementById("loader");

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const clue = document.getElementById("clue").value.trim();
    if (!clue) {
      resultDiv.innerHTML = "⚠️ Please enter a clue.";
      return;
    }

    loader.style.display = "block";
    resultDiv.innerHTML = "";

    try {
      const res = await fetch("/find_word", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ clue }),
      });

      const data = await res.json();
      loader.style.display = "none";

      if (data.error) {
        resultDiv.innerHTML = `❌ ${data.error}`;
      } else {
        resultDiv.innerHTML = `
          <strong>Primary word:</strong> ${data.primary}<br>
          <small>Definition:</small> ${data.definition}<br><br>
          <em>Alternatives:</em> ${data.alternatives.join(", ")}
        `;
      }
    } catch (err) {
      loader.style.display = "none";
      resultDiv.innerHTML = "❌ Something went wrong.";
    }
  });
});
