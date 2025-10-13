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

// Save role on register
function showForm(role) {
  const roleStep = document.getElementById("role-step");
  const registerForm = document.getElementById("register-form");
  const roleTitle = document.getElementById("role-title");
  const emailField = document.getElementById("emailField");
  const workplaceField = document.getElementById("workplace-field");
  const selectedRole = document.getElementById("selectedRole");

  if (roleStep) roleStep.classList.add("hidden");
  if (registerForm) registerForm.classList.remove("hidden");
  if (roleTitle) roleTitle.innerText = "Register as " + role.charAt(0).toUpperCase() + role.slice(1);

  if (emailField && workplaceField) {
    if (role === "student" || role === "admin") {
      emailField.placeholder = "Email (e.g. name@cit.edu)";
      workplaceField.classList.add("hidden");
    } else if (role === "consultant") {
      emailField.placeholder = "Email (CIT or personal)";
      workplaceField.classList.remove("hidden");
    }
  }

  if (selectedRole) {
    selectedRole.value = role; // save chosen role
    localStorage.setItem("userRole", role); // persist role for login
  }
}

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

