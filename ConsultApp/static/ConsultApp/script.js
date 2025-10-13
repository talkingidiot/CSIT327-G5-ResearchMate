const signUpButton = document.getElementById('signUp');
const signInButton = document.getElementById('signIn');
const container = document.getElementById('container');

if (signUpButton) {
  signUpButton.addEventListener('click', () => {
    container.classList.add("right-panel-active");
    const roleStep = document.getElementById("role-step");
    const registerForm = document.getElementById("register-form");
    if (roleStep) roleStep.classList.remove("hidden");
    if (registerForm) registerForm.classList.add("hidden");
  });
}

if (signInButton) {
  signInButton.addEventListener('click', () => {
    container.classList.remove("right-panel-active");
  });
}

function showForm(role) {
  const roleStep = document.getElementById("role-step");
  const registerForm = document.getElementById("register-form");
  const roleTitle = document.getElementById("role-title");
  const selectedRoleInput = document.getElementById("selectedRole");

  // Hide the role selection step and show the register form
  roleStep.classList.add("hidden");
  registerForm.classList.remove("hidden");

  // Save the role in the form
  selectedRoleInput.value = role;
  roleTitle.textContent = "Register as " + role.charAt(0).toUpperCase() + role.slice(1);

  // Save the role so we can restore after reload
  sessionStorage.setItem("selectedRole", role);

  // Show fields based on the role
  document.getElementById("studentFields").classList.toggle("hidden", role !== "student");
  document.getElementById("consultantFields").classList.toggle("hidden", role !== "consultant");
  document.getElementById("adminFields").classList.toggle("hidden", role !== "admin");
}

// Restore role after reload if show_signup is true
document.addEventListener("DOMContentLoaded", function() {
  const savedRole = sessionStorage.getItem("selectedRole");

  if (!document.getElementById("role-step")) {
    sessionStorage.removeItem("selectedRole");
    return;
  }

  if (savedRole && container.classList.contains("right-panel-active"))  {
    const roleStep = document.getElementById("role-step");
    const registerForm = document.getElementById("register-form");
    const roleTitle = document.getElementById("role-title");
    const selectedRoleInput = document.getElementById("selectedRole");

    roleStep.classList.add("hidden");
    registerForm.classList.remove("hidden");
    selectedRoleInput.value = savedRole;
    roleTitle.textContent = "Register as " + savedRole.charAt(0).toUpperCase() + savedRole.slice(1);

    // Show fields based on saved role
    document.getElementById("studentFields").classList.toggle("hidden", savedRole !== "student");
    document.getElementById("consultantFields").classList.toggle("hidden", savedRole !== "consultant");
    document.getElementById("adminFields").classList.toggle("hidden", savedRole !== "admin");
  }
});

function backToRole() {
  const registerForm = document.getElementById("register-form");
  const roleStep = document.getElementById("role-step");
  if (registerForm) registerForm.classList.add("hidden");
  if (roleStep) roleStep.classList.remove("hidden");
}

function signInRedirect() {
  container.classList.remove("right-panel-active");
}

// Toggle register password
const passwordField = document.getElementById('passwordField');
const toggleRegisterPassword = document.getElementById('toggleRegisterPassword');

if (toggleRegisterPassword && passwordField) {
  toggleRegisterPassword.addEventListener('click', () => {
    if (passwordField.type === 'password') {
      passwordField.type = 'text';
      toggleRegisterPassword.textContent = 'X';
    } else {
      passwordField.type = 'password';
      toggleRegisterPassword.textContent = '👁';
    }
  });
}

// Toggle signin password
const signinPassword = document.getElementById('signinPassword');
const toggleSignInPassword = document.getElementById('toggleSignInPassword');

if (toggleSignInPassword && signinPassword) {
  toggleSignInPassword.addEventListener('click', () => {
    if (signinPassword.type === 'password') {
      signinPassword.type = 'text';
      toggleSignInPassword.textContent = 'X';
    } else {
      signinPassword.type = 'password';
      toggleSignInPassword.textContent = '👁';
    }
  });
}