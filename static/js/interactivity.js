
function setActiveButton(button) {
  // Remove "active" class from all buttons
  document.querySelectorAll("button").forEach(btn => btn.classList.remove("active"));

  // Add "active" class to the clicked button
  button.classList.add("active");
}