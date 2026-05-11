document.addEventListener("DOMContentLoaded", function () {
  const forms = document.querySelectorAll("form[data-confirm]");

  forms.forEach((form) => {
    form.addEventListener("submit", function (event) {
      const message =
        form.getAttribute("data-confirm-message") ||
        "Are you sure you want to submit this form?";

      const confirmed = window.confirm(message);

      if (!confirmed) {
        event.preventDefault();
      }
    });
  });
});