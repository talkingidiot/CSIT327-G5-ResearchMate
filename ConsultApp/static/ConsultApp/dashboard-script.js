
let currentUser = {
  name: "John Doe",
  email: "john.doe@cit.edu",
  role: "student",
  avatar: "JD"
};


document.addEventListener('DOMContentLoaded', function() {
  initDashboard();
  setupEventListeners();
});


function initDashboard() {

  const urlParams = new URLSearchParams(window.location.search);
  const role = urlParams.get('role') || getStoredUserRole() || 'student';
  
  updateUserInfo(role);
  updateDashboardContent(role);
  

  showNotification('Welcome to ResearchMate Dashboard!', 'success');
}


function setupEventListeners() {

  document.querySelectorAll('.nav-link').forEach(link => {
    link.addEventListener('click', function(e) {
      e.preventDefault();
      const section = this.getAttribute('data-section');
      switchSection(section);
      
   
      document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
      this.classList.add('active');
    });
  });

  
  document.querySelectorAll('.close-btn').forEach(btn => {
    btn.addEventListener('click', function() {
      const modal = this.closest('.modal');
      closeModal(modal.id);
    });
  });

  
  document.querySelectorAll('.modal').forEach(modal => {
    modal.addEventListener('click', function(e) {
      if (e.target === this) {
        closeModal(this.id);
      }
    });
  });

  
  setupFormHandlers();
}


function setupFormHandlers() {

  const newProjectForm = document.querySelector('#newProjectModal form');
  if (newProjectForm) {
    newProjectForm.addEventListener('submit', function(e) {
      e.preventDefault();
      handleNewProject(this);
    });
  }


  const collaborateForm = document.querySelector('#collaborateModal form');
  if (collaborateForm) {
    collaborateForm.addEventListener('submit', function(e) {
      e.preventDefault();
      handleCollaborateSearch(this);
    });
  }


  const editProfileForm = document.querySelector('#editProfileModal form');
  if (editProfileForm) {
    editProfileForm.addEventListener('submit', function(e) {
      e.preventDefault();
      handleProfileUpdate(this);
    });
  }
}


function getStoredUserRole() {

  return localStorage.getItem('userRole');
}


function updateUserInfo(role) {
  currentUser.role = role;
  
  const roleNames = {
    'student': 'Student',
    'consultant': 'Consultant', 
    'admin': 'Administrator'
  };

  const userNames = {
    'student': 'John Doe',
    'consultant': 'Dr. Sarah Wilson',
    'admin': 'Admin User'
  };

  const userEmails = {
    'student': 'john.doe@cit.edu',
    'consultant': 'sarah.wilson@company.com',
    'admin': 'admin@researchmate.com'
  };

  const userAvatars = {
    'student': 'JD',
    'consultant': 'SW', 
    'admin': 'AU'
  };


  currentUser.name = userNames[role];
  currentUser.email = userEmails[role];
  currentUser.avatar = userAvatars[role];
  

  const userName = document.getElementById('userName');
  const userRole = document.getElementById('userRole');
  const userAvatar = document.getElementById('userAvatar');
  const welcomeName = document.getElementById('welcomeName');
  const profileName = document.getElementById('profileName');
  const profileEmail = document.getElementById('profileEmail');
  const profileRole = document.getElementById('profileRole');
  
  if (userName) userName.textContent = currentUser.name;
  if (userRole) userRole.textContent = `(${roleNames[role]})`;
  if (userAvatar) userAvatar.textContent = currentUser.avatar;
  if (welcomeName) welcomeName.textContent = currentUser.name.split(' ')[0];
  if (profileName) profileName.textContent = currentUser.name;
  if (profileEmail) profileEmail.textContent = currentUser.email;
  if (profileRole) profileRole.textContent = roleNames[role];
}


function updateDashboardContent(role) {
  const adminNav = document.getElementById('adminNav');
  const welcomeMessage = document.getElementById('welcomeMessage');
  
  if (role === 'admin') {
    if (adminNav) adminNav.style.display = 'block';
    if (welcomeMessage) welcomeMessage.textContent = 'Manage the ResearchMate platform';
  } else if (role === 'consultant') {
    if (welcomeMessage) welcomeMessage.textContent = 'Share your expertise and collaborate with researchers';
  } else {
    if (welcomeMessage) welcomeMessage.textContent = 'Continue your research journey with ResearchMate';
  }


  updateStatsForRole(role);
  updateActivitiesForRole(role);
}


function updateStatsForRole(role) {
  const stats = {
    student: { 
      projects: 3, 
      collaborations: 7, 
      publications: 12, 
      citations: 45 
    },
    consultant: { 
      projects: 15, 
      collaborations: 23, 
      publications: 87, 
      citations: 324 
    },
    admin: { 
      projects: 89, 
      collaborations: 156, 
      publications: 523, 
      citations: 2341 
    }
  };

  const roleStats = stats[role] || stats.student;
  
  const activeProjects = document.getElementById('activeProjects');
  const collaborations = document.getElementById('collaborations');
  const publications = document.getElementById('publications');
  const citations = document.getElementById('citations');

  if (activeProjects) activeProjects.textContent = roleStats.projects;
  if (collaborations) collaborations.textContent = roleStats.collaborations;
  if (publications) publications.textContent = roleStats.publications;
  if (citations) citations.textContent = roleStats.citations;
}


function updateActivitiesForRole(role) {
  const activities = {
    student: [
      { title: 'New collaboration request from Dr. Smith', time: '2 hours ago' },
      { title: 'Research paper "AI in Healthcare" published', time: '1 day ago' },
      { title: 'Project "Climate Analysis" milestone reached', time: '3 days ago' }
    ],
    consultant: [
      { title: 'New student collaboration request approved', time: '1 hour ago' },
      { title: 'Consultation session with research team completed', time: '4 hours ago' },
      { title: 'Industry report "Tech Trends 2024" shared', time: '1 day ago' }
    ],
    admin: [
      { title: 'System backup completed successfully', time: '30 minutes ago' },
      { title: 'New user registrations: 15 students, 3 consultants', time: '2 hours ago' },
      { title: 'Monthly analytics report generated', time: '1 day ago' }
    ]
  };

  const activityList = document.getElementById('activityList');
  if (activityList && activities[role]) {
    activityList.innerHTML = activities[role].map(activity => `
      <div class="activity-item">
        <div class="activity-title">${activity.title}</div>
        <div class="activity-meta">${activity.time}</div>
      </div>
    `).join('');
  }
}


function switchSection(sectionName) {

  document.querySelectorAll('.content-section').forEach(section => {
    section.classList.remove('active');
  });
  

  const targetSection = document.getElementById(sectionName);
  if (targetSection) {
    targetSection.classList.add('active');
  }
}


function openModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.style.display = 'block';
    document.body.style.overflow = 'hidden'; 
  }
}

function closeModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.style.display = 'none';
    document.body.style.overflow = 'auto'; 
  }
}


function handleNewProject(form) {
  const formData = new FormData(form);
  const projectData = {
    title: formData.get('title') || form.querySelector('input[placeholder="Enter project title"]').value,
    description: formData.get('description') || form.querySelector('textarea').value,
    category: formData.get('category') || form.querySelector('select').value
  };


  showNotification('Creating new project...', 'info');
  
  setTimeout(() => {
    showNotification(`Project "${projectData.title}" created successfully!`, 'success');
    closeModal('newProjectModal');
    form.reset();
    

    const activeProjects = document.getElementById('activeProjects');
    if (activeProjects) {
      const current = parseInt(activeProjects.textContent);
      activeProjects.textContent = current + 1;
    }
  }, 1500);
}

function handleCollaborateSearch(form) {
  showNotification('Searching for collaborators...', 'info');
  
  setTimeout(() => {
    showNotification('Found 12 potential collaborators in your field!', 'success');
    closeModal('collaborateModal');
    form.reset();
  }, 1000);
}

function handleProfileUpdate(form) {
  const formData = new FormData(form);
  
  showNotification('Updating profile...', 'info');
  
  setTimeout(() => {
    showNotification('Profile updated successfully!', 'success');
    closeModal('editProfileModal');
    

    const newName = form.querySelector('input[value="John Doe"]').value;
    if (newName) {
      currentUser.name = newName;
      updateUserInfo(currentUser.role);
    }
  }, 1000);
}


function showNotification(message, type = 'info') {

  document.querySelectorAll('.notification').forEach(n => n.remove());
  
  const notification = document.createElement('div');
  notification.className = `notification ${type}`;
  notification.textContent = message;
  
  document.body.appendChild(notification);
  

  setTimeout(() => notification.classList.add('show'), 100);
  

  setTimeout(() => {
    notification.classList.remove('show');
    setTimeout(() => notification.remove(), 300);
  }, 3000);
}


function logout() {
  showNotification('Logging out...', 'info');
  
  setTimeout(() => {

    localStorage.removeItem('userRole');
    localStorage.removeItem('userData');
    

    window.location.href = 'login.html';
  }, 1000);
}


function startRealTimeUpdates() {

  setInterval(() => {
    const activityItems = document.querySelectorAll('.activity-meta');
    activityItems.forEach(item => {
      if (item.textContent.includes('minutes ago')) {
        const minutes = parseInt(item.textContent.match(/\d+/)[0]) + 1;
        if (minutes < 60) {
          item.textContent = `${minutes} minutes ago`;
        } else {
          item.textContent = '1 hour ago';
        }
      }
    });
  }, 60000); 
}


startRealTimeUpdates();


document.addEventListener('keydown', function(e) {

  if (e.ctrlKey && e.shiftKey && e.key === 'N') {
    e.preventDefault();
    openModal('newProjectModal');
  }
  

  if (e.key === 'Escape') {
    document.querySelectorAll('.modal').forEach(modal => {
      if (modal.style.display === 'block') {
        closeModal(modal.id);
      }
    });
  }
});


function searchContent(query) {
  showNotification(`Searching for: ${query}`, 'info');

}


function exportData(format = 'csv') {
  showNotification(`Exporting data as ${format.toUpperCase()}...`, 'info');
  
  setTimeout(() => {
    showNotification('Data exported successfully!', 'success');
  }, 1500);
}

  
function importData(file) {
  showNotification('Importing data...', 'info');
  
  setTimeout(() => {
    showNotification('Data imported successfully!', 'success');
  }, 2000);
}


function formatDate(date) {
  return new Intl.DateTimeFormat('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  }).format(date);
}

function formatNumber(num) {
  return new Intl.NumberFormat().format(num);
}

function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}