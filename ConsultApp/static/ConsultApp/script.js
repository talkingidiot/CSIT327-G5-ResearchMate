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

/* STEP 1: Show the correct registration form based on role */
function showForm(role) {
  const roleStep = document.getElementById("role-step");
  const registerForm = document.getElementById("register-form");
  const roleTitle = document.getElementById("role-title");
  const emailField = document.getElementById("email");
  const workplaceField = document.getElementById("workplace-field");
  const roleInput = document.getElementById("role");

  // Toggle visibility
  if (roleStep) roleStep.classList.add("hidden");
  if (registerForm) registerForm.classList.remove("hidden");

  // Update title text
  if (roleTitle) {
    roleTitle.innerText = "Register as " + role.charAt(0).toUpperCase() + role.slice(1);
  }

  // Adjust email placeholder and workplace field
  if (emailField && workplaceField) {
    if (role === "student" || role === "admin") {
      emailField.placeholder = "Email (e.g. name@cit.edu)";
      workplaceField.classList.add("hidden");
    } else if (role === "consultant") {
      emailField.placeholder = "Email (CIT or personal)";
      workplaceField.classList.remove("hidden");
    }
  }

  // Save selected role
  if (roleInput) {
    roleInput.value = role;
    localStorage.setItem("userRole", role);
  }
}

/* STEP 2: Back to role selection */
function backToRole() {
  const registerForm = document.getElementById("register-form");
  const roleStep = document.getElementById("role-step");
  if (registerForm) registerForm.classList.add("hidden");
  if (roleStep) roleStep.classList.remove("hidden");
}

/* STEP 3: Redirect to Sign In */
function signInRedirect() {
  container.classList.remove("right-panel-active");
}

/* Toggle Register Password Visibility */
const registerPassword = document.getElementById('registerPassword');
const toggleRegisterPassword = document.getElementById('toggleRegisterPassword');

if (toggleRegisterPassword && registerPassword) {
  toggleRegisterPassword.addEventListener('click', () => {
    if (registerPassword.type === 'password') {
      registerPassword.type = 'text';
      toggleRegisterPassword.textContent = '❌';
    } else {
      registerPassword.type = 'password';
      toggleRegisterPassword.textContent = '✅';
    }
  });
}


const loginPassword = document.getElementById('loginPassword');
const toggleLoginPassword = document.getElementById('toggleLoginPassword');

if (toggleLoginPassword && loginPassword) {
  toggleLoginPassword.addEventListener('click', () => {
    if (loginPassword.type === 'password') {
      loginPassword.type = 'text';
      toggleLoginPassword.textContent = '❌';
    } else {
      loginPassword.type = 'password';
      toggleLoginPassword.textContent = '✅';
    }
  });
}
