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
const passwordField = document.getElementById('password');
const toggleRegisterPassword = document.getElementById('toggleRegisterPassword');

if (toggleRegisterPassword && passwordField) {
  toggleRegisterPassword.addEventListener('click', () => {
    if (passwordField.type === 'password') {
      passwordField.type = 'text';
      toggleRegisterPassword.textContent = '❌';
    } else {
      passwordField.type = 'password';
      toggleRegisterPassword.textContent = '✅';
    }
  });
}

/* Toggle Sign-In Password Visibility */
const signinPassword = document.getElementById('signinPassword');
const toggleSignInPassword = document.getElementById('toggleSignInPassword');

if (toggleSignInPassword && signinPassword) {
  toggleSignInPassword.addEventListener('click', () => {
    if (signinPassword.type === 'password') {
      signinPassword.type = 'text';
      toggleSignInPassword.textContent = '❌';
    } else {
      signinPassword.type = 'password';
      toggleSignInPassword.textContent = '✅';
    }
  });
}

/* Handle login redirect based on stored role */
const loginForm = document.getElementById("login-form");
if (loginForm) {
  loginForm.addEventListener("submit", async (e) => {
    e.preventDefault();

    const data = {
      email: document.getElementById("loginEmail").value,
      password: document.getElementById("loginPassword").value,
    };

    try {
      const response = await fetch("{% url 'login_user' %}", {   // ✅ correct
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCSRFToken(),
            "X-Requested-With": "XMLHttpRequest"   // ✅ add this since your view checks for AJAX
          },
          body: JSON.stringify(data),
      });


      const result = await response.json();
      if (result.role === "student") {
        window.location.href = "{% url 'student_dashboard' %}";
      } else if (result.role === "consultant") {
          window.location.href = "{% url 'consultant_dashboard' %}";
      } else if (result.role === "admin") {
          window.location.href = "{% url 'admin_dashboard' %}";
      }

    } catch (err) {
      console.error(err);
      alert("Something went wrong. Please try again.");
    }
  });
}


/* Helper: Get CSRF Token (for Django POST requests) */
function getCSRFToken() {
  const cookieValue = document.cookie
    .split('; ')
    .find(row => row.startsWith('csrftoken='));
  return cookieValue ? cookieValue.split('=')[1] : '';
}

/* Handle Registration Form Submit */
const registerForm = document.getElementById("register-form");
if (registerForm) {
  registerForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const data = {
      first_name: document.getElementById("first_name").value,
      last_name: document.getElementById("last_name").value,
      username: document.getElementById("username").value,
      email: document.getElementById("email").value,
      password: document.getElementById("password").value,
      role: document.getElementById("role").value,
      workplace: document.getElementById("workplace")?.value || "",
    };

    try {
      const response = await fetch("/register/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCSRFToken(),
        },
        body: JSON.stringify(data),
      });

      const result = await response.json();

      if (response.ok) {
        alert(result.message);
        // 👇 Switch to sign-in panel
        container.classList.remove("right-panel-active");
      } else {
        alert(result.error || "Registration failed");
      }
    } catch (error) {
      console.error("Error:", error);
      alert("Something went wrong. Please try again.");
    }
  });
}

