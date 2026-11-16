document.querySelectorAll("[data-leadhub-form]").forEach((form) => {
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const status = form.querySelector("[data-leadhub-status]");
    const fields = new FormData(form);
    const button = form.querySelector("button[type=submit]");
    button.disabled = true;
    status.textContent = "Joining…";
    try {
      const response = await fetch(form.dataset.endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          project: "campusflow",
          email: fields.get("email"),
          consent: fields.get("consent") === "on",
          website: fields.get("website"),
          source: window.location.hostname,
        }),
      });
      const result = await response.json();
      if (!response.ok || !result.ok) throw new Error(result.error || "Signup could not be completed.");
      form.reset();
      status.textContent = result.message || "Check your inbox to confirm your signup.";
    } catch {
      status.textContent = "Signup is unavailable right now. Please try again later.";
    } finally {
      button.disabled = false;
    }
  });
});
