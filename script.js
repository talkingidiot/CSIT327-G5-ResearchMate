const signUpButton = document.getElementById('signUp');
const signInButton = document.getElementById('signIn');
const container = document.getElementById('container');

signUpButton.addEventListener('click', () => {
  container.classList.add("right-panel-active");
  document.getElementById("role-step").classList.remove("hidden");
  document.getElementById("register-form").classList.add("hidden");
});

signInButton.addEventListener('click', () => {
  container.classList.remove("right-panel-active");
});

function showForm(role) {
  document.getElementById("role-step").classList.add("hidden");
  document.getElementById("register-form").classList.remove("hidden");
  document.getElementById("role-title").innerText =
    "Register as " + role.charAt(0).toUpperCase() + role.slice(1);

  const emailField = document.getElementById("emailField");
  const workplaceField = document.getElementById("workplace-field");

  if (role === "student" || role === "admin") {
    emailField.placeholder = "Email (e.g. name@cit.edu)";
    workplaceField.classList.add("hidden");
  } else if (role === "consultant") {
    emailField.placeholder = "Email (CIT or personal)";
    workplaceField.classList.remove("hidden");
  }
}

function backToRole() {
  document.getElementById("register-form").classList.add("hidden");
  document.getElementById("role-step").classList.remove("hidden");
}

// Password toggle + strength
const passwordField = document.getElementById('passwordField');
const toggleRegisterPassword = document.getElementById('toggleRegisterPassword');
const passwordStrength = document.getElementById('passwordStrength');

toggleRegisterPassword.addEventListener('click', () => {
  passwordField.type = passwordField.type === 'password' ? 'text' : 'password';
});

passwordField.addEventListener('input', () => {
  const val = passwordField.value;
  let strength = 'Weak';
  let color = 'red';

  if (val.length >= 6 && /[A-Za-z]/.test(val) && /\d/.test(val)) {
    strength = 'Medium';
    color = 'orange';
  }
  if (val.length >= 8 && /[A-Za-z]/.test(val) && /\d/.test(val) && /[!@#$%^&*]/.test(val)) {
    strength = 'Strong';
    color = 'green';
  }

  passwordStrength.textContent = `Password strength: ${strength}`;
  passwordStrength.style.color = color;
});

// Sign In password toggle
const signinPassword = document.getElementById('signinPassword');
const toggleSignInPassword = document.getElementById('toggleSignInPassword');

toggleSignInPassword.addEventListener('click', () => {
  signinPassword.type = signinPassword.type === 'password' ? 'text' : 'password';
});

// Redirect Sign In link
function signInRedirect() {
  container.classList.remove("right-panel-active");
}
