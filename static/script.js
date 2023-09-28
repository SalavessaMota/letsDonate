document.addEventListener("DOMContentLoaded", function() {
  const buttons = document.querySelectorAll(".nav-button");
  const headerHeight = document.querySelector('header').offsetHeight;

  buttons.forEach(button => {
    button.addEventListener("click", function() {
      const targetId = this.getAttribute("data-target");
      const targetSection = document.getElementById(targetId);
      window.scrollTo({
        top: targetSection.offsetTop - headerHeight,
        behavior: "smooth"
      });
    });
  });
});
