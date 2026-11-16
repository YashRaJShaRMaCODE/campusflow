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

document.querySelectorAll("[data-leadhub-recommendations]").forEach((box) => {
  const consent = box.querySelector("[data-recommendations-consent]");
  const status = box.querySelector("[data-recommendations-status]");
  const list = box.querySelector("[data-recommendations-list]");
  consent.addEventListener("change", async () => {
    list.replaceChildren();
    status.textContent = "";
    if (!consent.checked) return;
    status.textContent = "Loading suggestions…";
    try {
      const response = await fetch(`${box.dataset.endpoint}?project=campusflow&consent=true`);
      const result = await response.json();
      if (!response.ok) throw new Error("Suggestions unavailable");
      for (const item of result.items || []) {
        const url = new URL(item.url);
        if (url.protocol !== "https:") continue;
        const entry = document.createElement("li");
        const link = document.createElement("a");
        link.href = url.href;
        link.target = "_blank";
        link.rel = "noopener noreferrer";
        link.textContent = item.name;
        entry.append(link, document.createTextNode(` — ${item.reason}`));
        list.append(entry);
      }
      status.textContent = list.childElementCount ? "Our other products" : "No related products are available right now.";
    } catch {
      status.textContent = "Suggestions are unavailable right now.";
    }
  });
});
