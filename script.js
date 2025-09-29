import { supabase } from './config.js';

const container = document.getElementById('container');

// Sign In / Sign Up toggle
const signUpButton = document.getElementById('signUp');
const signInButton = document.getElementById('signIn');

if (signUpButton) {
  signUpButton.addEventListener('click', () => {
    container.classList.add("right-panel-active");
    document.getElementById("role-step").classList.remove("hidden");
    document.getElementById("register-form").classList.add("hidden");
  });
}

if (signInButton) {
  signInButton.addEventListener('click', () => {
    container.classList.remove("right-panel-active");
  });
}

// Role selection buttons
document.getElementById('studentBtn')?.addEventListener('click', () => showForm('student'));
document.getElementById('consultantBtn')?.addEventListener('click', () => showForm('consultant'));
document.getElementById('adminBtn')?.addEventListener('click', () => showForm('admin'));

function showForm(role) {
  const roleStep = document.getElementById('role-step');
  const registerForm = document.getElementById('register-form');
  const roleTitle = document.getElementById('role-title');
  const emailField = document.getElementById('emailField');
  const workplaceField = document.getElementById('workplace-field');
  const selectedRole = document.getElementById('selectedRole');

  roleStep.classList.add('hidden');
  registerForm.classList.remove('hidden');
  roleTitle.innerText = `Register as ${role.charAt(0).toUpperCase() + role.slice(1)}`;

  if (role === 'consultant') {
    emailField.placeholder = 'Email (CIT or personal)';
    workplaceField.classList.remove('hidden');
  } else {
    emailField.placeholder = 'Email (e.g. name@cit.edu)';
    workplaceField.classList.add('hidden');
  }

  selectedRole.value = role;
}

// Back button
function backToRole() {
  document.getElementById("register-form").classList.add("hidden");
  document.getElementById("role-step").classList.remove("hidden");
}

// Redirect to login
function signInRedirect() {
  container.classList.remove("right-panel-active");
}

// Toggle password
function setupToggle(idInput, idToggle) {
  const input = document.getElementById(idInput);
  const toggle = document.getElementById(idToggle);
  if (input && toggle) {
    toggle.addEventListener('click', () => {
      if (input.type === 'password') {
        input.type = 'text';
        toggle.textContent = '🙈';
      } else {
        input.type = 'password';
        toggle.textContent = '👁️';
      }
    });
  }
}
setupToggle('passwordField', 'toggleRegisterPassword');
setupToggle('signinPassword', 'toggleSignInPassword');

// Handle registration
document.getElementById('register-form').addEventListener('submit', async (e) => {
  e.preventDefault();

  const fullName = document.getElementById('fullName').value;
  const email = document.getElementById('emailField').value;
  const password = document.getElementById('passwordField').value;
  const role = document.getElementById('selectedRole').value;
  const workplace = document.getElementById('workplace')?.value || '';

  try {
    // Create user - Supabase will send confirmation email according to your template.
    // If your template includes {{ .Token }}, the email will contain OTP instead of a magic link.
    const { data, error } = await supabase.auth.signUp({
      email,
      password,
      options: {
        data: { full_name: fullName, role, workplace }
      }
    });

    if (error) throw error;

    alert('Registration successful! Please check your email for the verification code (OTP).');

    // Show OTP form so user can type the code (you asked for inline OTP entry)
    document.getElementById("register-form").classList.add("hidden");
    document.getElementById("otp-form").classList.remove("hidden");
  } catch (error) {
    alert('Error: ' + error.message);
  }
});

// Verify OTP form submit
document.getElementById('otp-form').addEventListener('submit', async (e) => {
  e.preventDefault();

  const email = document.getElementById('emailField').value;
  const token = document.getElementById('otpCode').value;

  try {
    // Verify the OTP for signup flow
    const { data, error } = await supabase.auth.verifyOtp({
      email,
      token,
      type: 'signup'
    });

    if (error) throw error;

    alert('Email verified successfully! You can now sign in.');
    document.getElementById("otp-form").classList.add("hidden");
    container.classList.remove('right-panel-active'); // go back to login view
  } catch (err) {
    alert('Invalid or expired OTP. Please try again.');
  }
});

// Handle login
document.getElementById('loginForm').addEventListener('submit', async (e) => {
  e.preventDefault();

  const email = document.getElementById('loginEmail').value;
  const password = document.getElementById('signinPassword').value;

  try {
    const { data, error } = await supabase.auth.signInWithPassword({ email, password });
    if (error) throw error;

    const role = data.user.user_metadata.role;
    localStorage.setItem('userRole', role);

    switch(role) {
      case 'student': window.location.href = 'student-dashboard.html'; break;
      case 'consultant': window.location.href = 'consultant-dashboard.html'; break;
      case 'admin': window.location.href = 'admin-dashboard.html'; break;
      default: alert('Invalid role'); 
    }
  } catch (error) {
    alert('Error: ' + error.message);
  }
});
