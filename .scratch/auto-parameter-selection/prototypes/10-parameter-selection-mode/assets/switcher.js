// PROTOTYPE (throwaway): ← / → cycle the variants, except while typing in a field.
document.addEventListener("keydown", (e) => {
  const t = e.target;
  if (t && (t.matches("input, textarea, select, [contenteditable]") || t.closest(".Select, .dash-dropdown"))) return;
  if (e.key === "ArrowLeft") document.getElementById("v-prev")?.click();
  if (e.key === "ArrowRight") document.getElementById("v-next")?.click();
});
