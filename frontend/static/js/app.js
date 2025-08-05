Vue.prototype.$http = axios;

// Global dark mode toggle function
window.toggleDarkMode = function() {
  document.body.classList.toggle('dark-mode');
  // Save preference to localStorage
  const isDarkMode = document.body.classList.contains('dark-mode');
  localStorage.setItem('darkMode', isDarkMode);
};

// Initialize dark mode from localStorage
document.addEventListener('DOMContentLoaded', function() {
  const savedDarkMode = localStorage.getItem('darkMode');
  if (savedDarkMode === 'true') {
    document.body.classList.add('dark-mode');
  }
});

// Homepage Component
const IndexComponent = { 
  template: `
    <div class="home-container text-center fade-in">
      <div class="hero-section py-5">
        <h1 class="display-4 mb-4">Welcome to Quiz Master V2</h1>
        <p class="lead mb-4">Test your knowledge, track your progress, and improve your skills with our interactive quizzes</p>
        <div class="d-flex justify-content-center mt-4">
          <a href="#/login" class="btn btn-primary btn-lg me-3">Login</a>
          <a href="#/register" class="btn btn-secondary btn-lg">Register</a>
        </div>
      </div>
      
      <div class="features-section py-5">
        <h2 class="mb-4">Key Features</h2>
        <div class="row">
          <div class="col-md-4 mb-4">
            <div class="card h-100 slide-up">
              <div class="card-body text-center">
                <div class="feature-icon mb-3">📚</div>
                <h3>Diverse Subjects</h3>
                <p>Access quizzes across various subjects and topics</p>
              </div>
            </div>
          </div>
          <div class="col-md-4 mb-4">
            <div class="card h-100 slide-up">
              <div class="card-body text-center">
                <div class="feature-icon mb-3">📈</div>
                <h3>Progress Tracking</h3>
                <p>Monitor your performance and improvement over time</p>
              </div>
            </div>
          </div>
          <div class="col-md-4 mb-4">
            <div class="card h-100 slide-up">
              <div class="card-body text-center">
                <div class="feature-icon mb-3">📊</div>
                <h3>Export Results</h3>
                <p>Download your quiz history and performance reports</p>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Dark Mode Toggle Button -->
      <button class="dark-mode-toggle" @click="toggleDarkMode" title="Toggle Dark Mode">
        {{ isDarkMode ? '☀️' : '🌙' }}
      </button>
    </div>
  `,
  data() {
    return {
      isDarkMode: false
    };
  },
  created() {
    console.log("Home component created");
    this.updateNavbar(false);
    this.checkDarkMode();
  },
  mounted() {
    console.log("Home component mounted");
  },
  methods: {
    toggleDarkMode() {
      window.toggleDarkMode();
      this.checkDarkMode();
    },
    checkDarkMode() {
      this.isDarkMode = document.body.classList.contains('dark-mode');
    },
    updateNavbar(isLoggedIn) {
      console.log("Updating navbar");
      const navbarNav = document.getElementById('navbarNav');

      if (!navbarNav) {
        console.error("Navigation bar not found");
        return;
      }

      const navList = navbarNav.querySelector('ul');
      if (!navList) {
        console.error("Navigation list not found");
        return;
      }

      if (!isLoggedIn) {
        navList.innerHTML = `
          <li class="nav-item">
            <a class="nav-link active" href="#/">Home</a>
          </li>
          <li class="nav-item">
            <a class="nav-link" href="#/login">Login</a>
          </li>
          <li class="nav-item">
            <a class="nav-link" href="#/register">Register</a>
          </li>
          <li class="nav-item">
            <button onclick="toggleDarkMode()" class="btn btn-sm btn-outline-secondary ms-2">🌙</button>
          </li>
        `;
      } else {
        navList.innerHTML = `
          <li class="nav-item">
            <a class="nav-link active" href="#/">Dashboard</a>
          </li>
          <li class="nav-item">
            <a class="nav-link" href="#/profile">Profile</a>
          </li>
          <li class="nav-item">
            <a class="nav-link" href="#/logout">Logout</a>
          </li>
          <li class="nav-item">
            <button onclick="toggleDarkMode()" class="btn btn-sm btn-outline-secondary ms-2">🌙</button>
          </li>
        `;
      }
    }
  }
};


// Auth components
const AuthComponent = {
  Login: { 
    template: `
      <div class="auth-container">
        <div class="auth-form">
          <h2>Login to Your Account</h2>
          <div v-if="errorMessage" class="alert alert-danger" role="alert">
            {{ errorMessage }}
          </div>
          <form @submit.prevent="login">
            <div class="mb-3">
              <label class="form-label">Username</label>
              <div class="input-group">
                <span class="input-group-text"><i class="fas fa-user"></i></span>
                <input 
                  type="text" 
                  class="form-control" 
                  v-model="username" 
                  placeholder="Enter your username"
                  required
                >
              </div>
            </div>
            <div class="mb-3">
              <label class="form-label">Password</label>
              <div class="input-group">
                <span class="input-group-text"><i class="fas fa-lock"></i></span>
                <input 
                  type="password" 
                  class="form-control" 
                  v-model="password"
                  placeholder="Enter your password"
                  required
                >
              </div>
            </div>
            <div class="d-grid gap-2">
              <button type="submit" class="btn btn-primary" :disabled="loading">
                <span v-if="loading" class="spinner-border spinner-border-sm me-2" role="status"></span>
                {{ loading ? 'Logging in...' : 'Login' }}
              </button>
            </div>
          </form>
          <p class="mt-3 text-center">Don't have an account? <a href="#/register">Register</a></p>
          <p class="text-center mt-3">
            <a href="#/" class="text-decoration-none">
              <i class="fas fa-arrow-left me-1"></i> Back to Home
            </a>
          </p>
        </div>
      </div>
    `, 
    data() { 
      return { 
        username: '', 
        password: '',
        loading: false,
        errorMessage: ''
      }; 
    },
    created() {
      // Update navbar for login page
      this.updateNavbar(false);
    },
    methods: { 
      login() { 
        this.loading = true;
        this.errorMessage = '';
        
        // Check if this is an admin login attempt
        if (this.username === 'admin') {
          // Use admin login endpoint
      this.$http.post('/api/v2/admin/login', { 
          username: this.username, 
          password: this.password 
        })
        .then(response => { 
            console.log("Admin login response:", response.data);
            
            if (response.data.status === 'success') {
              // Store admin JWT token and admin info
              const token = response.data.access_token;
              const admin = response.data.admin;
              
              localStorage.setItem('admin_token', token);
              localStorage.setItem('admin_user', JSON.stringify(admin));
            this.$router.push('/admin_dashboard');
          } else {
              this.errorMessage = response.data.message || 'Admin login failed';
            }
          })
          .catch(error => { 
            this.errorMessage = error.response?.data?.message || 'Admin login failed. Please check your credentials.';
            console.error('Admin login error:', error);
          })
          .finally(() => {
            this.loading = false;
          });
        } else {
          // Use regular user login endpoint
      this.$http.post('/api/v2/auth/login', { 
            username: this.username, 
            password: this.password 
          })
          .then(response => { 
            console.log("User login response:", response.data);
            
            if (response.data.status === 'success') {
              // Store user JWT token and user info
              const token = response.data.access_token;
              const user = response.data.user;
              
              localStorage.setItem('user_token', token);
              localStorage.setItem('user_data', JSON.stringify(user));
            this.$router.push('/user_dashboard');
            } else {
              this.errorMessage = response.data.message || 'Login failed';
          }
        })
        .catch(error => { 
            this.errorMessage = error.response?.data?.message || 'Login failed. Please check your credentials.';
            console.error('User login error:', error);
        })
        .finally(() => {
          this.loading = false;
        });
        }
      },
      updateNavbar(isLoggedIn) {
        // Update navigation bar for login page
        const navbarNav = document.getElementById('navbarNav');
        if (navbarNav) {
          const navList = navbarNav.querySelector('ul');
          if (navList) {
            navList.innerHTML = `
              <li class="nav-item">
                <a class="nav-link" href="#/">Home</a>
              </li>
              <li class="nav-item">
                <a class="nav-link active" href="#/login">Login</a>
              </li>
              <li class="nav-item">
                <a class="nav-link" href="#/register">Register</a>
              </li>
            `;
          }
        }
      }
    }
  },
  Register: { 
    template: `
      <div class="auth-container">
        <div class="auth-form">
          <h2>Create New Account</h2>
          <div v-if="errorMessage" class="alert alert-danger" role="alert">
            {{ errorMessage }}
          </div>
          <form @submit.prevent="register">
            <div class="mb-3">
              <label class="form-label">Full Name</label>
              <input 
                type="text" 
                class="form-control" 
                v-model="full_name"
                placeholder="Enter your full name"
                required
              >
            </div>
            <div class="mb-3">
              <label class="form-label">Username</label>
              <input 
                type="text" 
                class="form-control" 
                v-model="username"
                placeholder="Choose a username"
                required
              >
            </div>
            <div class="mb-3">
              <label class="form-label">Password</label>
              <input 
                type="password" 
                class="form-control" 
                v-model="password"
                placeholder="Create a password"
                required
              >
              <div class="form-text">Password should be at least 6 characters long</div>
            </div>
            <div class="mb-3">
              <label class="form-label">Confirm Password</label>
              <input 
                type="password" 
                class="form-control" 
                v-model="confirmPassword"
                placeholder="Confirm your password"
                required
              >
            </div>
            <div class="mb-3">
              <label class="form-label">Date of Birth</label>
              <input 
                type="date" 
                class="form-control" 
                v-model="dob"
              >
            </div>
            <div class="mb-3">
              <label class="form-label">Qualification</label>
              <input 
                type="text" 
                class="form-control" 
                v-model="qualification"
                placeholder="Enter your qualification"
              >
            </div>
            <div class="mb-3">
              <label class="form-label">Report Format</label>
              <select class="form-select" v-model="report_format">
                <option value="pdf">PDF</option>
                <option value="html">HTML</option>
              </select>
            </div>
            <div class="d-grid gap-2">
              <button type="submit" class="btn btn-primary" :disabled="loading">
                <span v-if="loading" class="spinner-border spinner-border-sm me-2" role="status"></span>
                {{ loading ? 'Registering...' : 'Register' }}
              </button>
            </div>
          </form>
          <p class="mt-3 text-center">Already have an account? <a href="#/login">Login</a></p>
          <p class="text-center mt-3">
            <a href="#/" class="text-decoration-none">
              <i class="fas fa-arrow-left me-1"></i> Back to Home
            </a>
          </p>
        </div>
      </div>
    `,
    data() { 
      return { 
        full_name: '', 
        username: '', 
        password: '', 
        confirmPassword: '', 
        dob: '', 
        qualification: '', 
        report_format: 'pdf',
        loading: false,
        errorMessage: ''
      }; 
    },
    created() {
      // Update navbar for registration page
      this.updateNavbar(false);
    },
    methods: { 
      register() { 
        // Validate form
        if (this.password !== this.confirmPassword) { 
          this.errorMessage = 'Passwords do not match';
          return; 
        }
        
        if (this.password.length < 6) {
          this.errorMessage = 'Password should be at least 6 characters long';
          return;
        }
        
        this.loading = true;
        this.errorMessage = '';
        
        this.$http.post('/api/v2/api/register', { 
          full_name: this.full_name, 
          username: this.username, 
          password: this.password, 
          dob: this.dob, 
          qualification: this.qualification,  
        })
        .then(response => { 
          console.log("Registration response:", response.data);
          alert('Registration successful! Please login.');
          this.$router.push('/login'); 
        })
        .catch(error => { 
          this.errorMessage = error.response?.data?.error || 'Registration failed. Please try again.';
          console.error('Registration error:', error);
        })
        .finally(() => {
          this.loading = false;
        });
      },
      updateNavbar(isLoggedIn) {
        // Update navigation bar for registration page
        const navbarNav = document.getElementById('navbarNav');
        if (navbarNav) {
          const navList = navbarNav.querySelector('ul');
          if (navList) {
            navList.innerHTML = `
              <li class="nav-item">
                <a class="nav-link" href="#/">Home</a>
              </li>
              <li class="nav-item">
                <a class="nav-link" href="#/login">Login</a>
              </li>
              <li class="nav-item">
                <a class="nav-link active" href="#/register">Register</a>
              </li>
            `;
          }
        }
      }
    }
  }
};

const UserDashboardComponent = {
  template: `
    <div class="container">
      <h2 class="mb-3">User Dashboard</h2>
      <div v-if="userData">
        <p class="mb-4">Welcome, {{ userData?.user_name || 'User' }}!</p>
        
        <!-- Stats Cards -->
        <div class="dashboard-stats mb-5 d-flex flex-wrap gap-3">
          <div class="stat-card p-3 border rounded flex-fill text-center">
            <h4>Total Subjects</h4>
            <div class="stat-number fs-3">{{ userData.subjects?.length || 0 }}</div>
          </div>
          <div class="stat-card p-3 border rounded flex-fill text-center">
            <h4>Quizzes Attempted</h4>
            <div class="stat-number fs-3">{{ totalQuizAttempts }}</div>
          </div>
          <div class="stat-card p-3 border rounded flex-fill text-center">
            <h4>Average Score</h4>
            <div class="stat-number fs-3">{{ formattedAvgScore }}%</div>
          </div>
        </div>
        
        <!-- Search -->
        <div class="mb-4">
          <div class="input-group">
            <input type="text" class="form-control" placeholder="Search quizzes..." v-model="searchQuery" @keyup.enter="searchQuizzes">
            <button class="btn btn-primary" @click="searchQuizzes">Search</button>
          </div>
        </div>
        
        <!-- Subjects -->
        <h3 class="mb-3">Available Subjects</h3>
        <div class="row">
          <div class="col-md-6 col-lg-4 mb-4" v-for="subject in userData.subjects" :key="subject.id">
            <div class="card h-100">
              <div class="card-body">
                <h5 class="card-title">{{ subject.name }}</h5>
                <div class="d-grid gap-2">
                  <router-link :to="'/chapters/' + subject.id" class="btn btn-primary">View Chapters</router-link>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <!-- Chapters -->
        <h3 class="mb-3">Available Chapters</h3>
        <div class="row">
          <div class="col-md-6 col-lg-4 mb-4" v-for="chapter in userData.chapters" :key="chapter.id">
            <div class="card h-100">
              <div class="card-body">
                <h5 class="card-title">{{ chapter.name }}</h5>
                <div class="d-grid gap-2">
                  <router-link :to="'/chapter_quizzes/' + chapter.id" class="btn btn-primary">View Quizzes</router-link>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <!-- Recent Activities -->
        <h3 class="mt-4 mb-3">Recent Activities</h3>
        <div class="table-responsive">
          <table class="table table-striped">
            <thead>
              <tr>
                <th>Subject</th>
                <th>Chapter</th>
                <th>Date</th>
                <th>Score</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(score, index) in recentScores" :key="index">
                <td>{{ score.subject?.name }}</td>
                <td>{{ score.chapter?.name }}</td>
                <td>{{ formatDate(score.score.time_stamp_of_attempt) }}</td>
                <td>{{ score.score.total_scored }}%</td>
                <td>
                  <router-link :to="'/view_answers/' + score.quiz.id" class="btn btn-sm btn-info">View</router-link>
                </td>
              </tr>
              <tr v-if="recentScores.length === 0">
                <td colspan="5" class="text-center">No recent quiz attempts</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
      
      <div v-else class="text-center my-5">
        <div class="spinner-border" role="status">
          <span class="visually-hidden">Loading...</span>
        </div>
      </div>
    </div>
  `,
  data() {
    return {
      userData: null,
      searchQuery: ''
    };
  },
  computed: {
    totalQuizAttempts() {
      return this.userData?.scores?.length || 0;
    },
    avgScore() {
      if (!this.userData?.scores?.length) return 0;
      const total = this.userData.scores.reduce((sum, score) => sum + score.score.total_scored, 0);
      return total / this.userData.scores.length;
    },
    formattedAvgScore() {
      return this.avgScore.toFixed(1);
    },
    recentScores() {
      if (!this.userData?.scores) return [];
      return [...this.userData.scores]
        .sort((a, b) => new Date(b.score.time_stamp_of_attempt) - new Date(a.score.time_stamp_of_attempt))
        .slice(0, 5);
    }
  },
  created() {
    this.fetchUserData();
    this.updateNavbar(true);
  },
  methods: {
    fetchUserData() {
      this.$http.get('/api/user_dashboard')
        .then(response => {
          this.userData = response.data;
        })
        .catch(error => {
          console.error('Error fetching dashboard data:', error);
          if (error.response?.status === 403) {
            alert('Please log in to access your dashboard');
            this.$router.push('/login');
          }
        });
    },
    updateNavbar(isLoggedIn) {
      const navbarNav = document.getElementById('navbarNav')?.querySelector('ul');
      if (isLoggedIn && navbarNav) {
        navbarNav.innerHTML = `
          <li class="nav-item">
            <a class="nav-link" href="#/">Home</a>
          </li>
          <li class="nav-item">
            <a class="nav-link" href="#/user_dashboard">Dashboard</a>
          </li>
          <li class="nav-item">
            <a class="nav-link" href="#/quiz_history">Quiz History</a>
          </li>
          <li class="nav-item">
            <a class="nav-link" href="/logout">Logout</a>
          </li>
          <li class="nav-item">
            <button onclick="toggleDarkMode()" class="btn btn-sm btn-dark ms-2">Dark Mode</button>
          </li>
        `;
      }
    },
    searchQuizzes() {
      if (!this.searchQuery.trim()) return;
      this.$router.push({
        path: '/search_results',
        query: { q: this.searchQuery.trim() }
      });
    },
    formatDate(dateStr) {
      return new Date(dateStr).toLocaleString();
    }
  }
};

// Admin Dashboard component with all mapping
const DashboardComponent = {
  AdminDashboard: {
    template: `
      <div class="container">
        <h2 class="mb-4">Admin Dashboard</h2>
        <p class="lead mb-5">Welcome, Administrator!</p>
        
        <!-- Statistics Cards -->
        <div class="row mb-4">
          <div class="col-md-3">
            <div class="card text-center">
              <div class="card-body">
                <h5 class="card-title">{{ statistics.user_count || 0 }}</h5>
                <p class="card-text">Total Users</p>
              </div>
            </div>
          </div>
          <div class="col-md-3">
            <div class="card text-center">
              <div class="card-body">
                <h5 class="card-title">{{ statistics.subject_count || 0 }}</h5>
                <p class="card-text">Total Subjects</p>
              </div>
            </div>
          </div>
          <div class="col-md-3">
            <div class="card text-center">
              <div class="card-body">
                <h5 class="card-title">{{ statistics.quiz_count || 0 }}</h5>
                <p class="card-text">Total Quizzes</p>
              </div>
            </div>
          </div>
          <div class="col-md-3">
            <div class="card text-center">
              <div class="card-body">
                <h5 class="card-title">{{ statistics.recent_scores?.length || 0 }}</h5>
                <p class="card-text">Recent Attempts</p>
              </div>
            </div>
          </div>
        </div>
        
        <div class="row">
          <!-- Manage Subjects -->
          <div class="col-md-6 mb-4">
            <div class="card h-100">
              <div class="card-body">
                <h5 class="card-title">Subjects Management</h5>
                <p class="card-text">Create, view, and edit quiz subjects</p>
                <div class="btn-group" role="group">
                  <a href="#/add_subject" class="btn btn-primary">Add Subject</a>
                  <a href="#/view_subjects" class="btn btn-info">View Subjects</a>
                </div>
              </div>
            </div>
          </div>

          <!-- Manage Chapters -->
          <div class="col-md-6 mb-4">
            <div class="card h-100">
              <div class="card-body">
                <h5 class="card-title">Chapters Management</h5>
                <p class="card-text">Create and organize chapters under subjects</p>
                <div class="btn-group" role="group">
                  <a href="#/view_chapters" class="btn btn-info">View Chapters</a>
                </div>
              </div>
            </div>
          </div>

          <!-- Manage Quizzes -->
          <div class="col-md-6 mb-4">
            <div class="card h-100">
              <div class="card-body">
                <h5 class="card-title">Quizzes Management</h5>
                <p class="card-text">Create and manage quizzes</p>
                <div class="btn-group" role="group">
                  <a href="#/view_quizzes" class="btn btn-info">View Quizzes</a>
                </div>
              </div>
            </div>
          </div>

          <!-- Manage Users -->
          <div class="col-md-6 mb-4">
            <div class="card h-100">
              <div class="card-body">
                <h5 class="card-title">Users Management</h5>
                <p class="card-text">Monitor and manage user accounts</p>
                <a href="#/view_users" class="btn btn-primary">View Users</a>
              </div>
            </div>
          </div>

          <!-- Reports -->
          <div class="col-md-6 mb-4">
            <div class="card h-100">
              <div class="card-body">
                <h5 class="card-title">Reports & Analytics</h5>
                <p class="card-text">Access usage and performance reports</p>
                <a href="#/reports" class="btn btn-primary">View Reports</a>
              </div>
            </div>
          </div>

          <!-- CSV Import/Export -->
          <div class="col-md-6 mb-4">
            <div class="card h-100">
              <div class="card-body">
                <h5 class="card-title">Data Management</h5>
                <p class="card-text">Import/Export data via CSV</p>
                <div class="btn-group" role="group">
                  <a href="#/csv_import" class="btn btn-success">Import CSV</a>
                  <a href="#/csv_export" class="btn btn-warning">Export CSV</a>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Recent Activity -->
        <div class="row mt-4" v-if="statistics.recent_scores && statistics.recent_scores.length">
          <div class="col-12">
            <div class="card">
              <div class="card-header">
                <h5>Recent Quiz Attempts</h5>
              </div>
              <div class="card-body">
                <div class="table-responsive">
                  <table class="table table-striped">
                    <thead>
                      <tr>
                        <th>User</th>
                        <th>Quiz</th>
                        <th>Score</th>
                        <th>Date</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="score in statistics.recent_scores.slice(0, 5)" :key="score.id">
                        <td>{{ score.user?.full_name || 'Unknown' }}</td>
                        <td>{{ score.quiz?.chapter?.name || 'Unknown Quiz' }}</td>
                        <td>{{ score.total_scored }}%</td>
                        <td>{{ formatDate(score.time_stamp_of_attempt) }}</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    `,
    data() {
      return {
        statistics: {
          user_count: 0,
          subject_count: 0,
          quiz_count: 0,
          recent_scores: []
        }
      };
    },
    created() {
      this.updateNavbar(true, true);
      this.fetchDashboardStatistics();
    },
    methods: {
      fetchDashboardStatistics() {
        const adminToken = localStorage.getItem('admin_token');
        if (!adminToken) {
          this.$router.push('/login');
          return;
        }
        
        this.$http.get('/api/v2/admin/dashboard', {
          headers: { 'Authorization': `Bearer ${adminToken}` }
        }).then(response => {
          if (response.data.status === 'success') {
            this.statistics = response.data.statistics;
          }
        }).catch(error => {
          console.error('Error fetching dashboard statistics:', error);
        });
      },
      formatDate(dateString) {
        if (!dateString) return 'N/A';
        const date = new Date(dateString);
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
      },
      updateNavbar(isLoggedIn, isAdmin) {
        const navbarNav = document.getElementById('navbarNav')?.querySelector('ul');
        if (isLoggedIn && isAdmin && navbarNav) {
          navbarNav.innerHTML = `
            <li class="nav-item">
              <a class="nav-link" href="#/">Home</a>
            </li>
            <li class="nav-item">
              <a class="nav-link" href="#/admin_dashboard">Admin Dashboard</a>
            </li>
            <li class="nav-item">
              <a class="nav-link" href="#/add_subject">Add Subject</a>
            </li>
            <li class="nav-item">
              <a class="nav-link" href="#/view_users">View Users</a>
            </li>
            <li class="nav-item">
              <a class="nav-link" href="/logout">Logout</a>
            </li>
            <li class="nav-item">
              <button onclick="toggleDarkMode()" class="btn btn-sm btn-dark ms-2">Dark Mode</button>
            </li>
          `;
        }
      }
    }
  }
};

const AttemptQuizComponent = { 
  template: `
    <div class="container">
      <h2 class="mb-4">Attempt Quiz</h2>

      <!-- Timer -->
      <div v-if="quizDuration > 0" class="alert alert-warning text-center fs-5">
        ⏱ Time Remaining: <strong>{{ formattedTime }}</strong>
      </div>

      <!-- Loading Spinner -->
      <div v-if="loading" class="text-center">
        <div class="spinner-border" role="status">
          <span class="visually-hidden">Loading...</span>
        </div>
      </div>

      <!-- Quiz Questions -->
      <div v-else-if="questions.length" class="question-container">
        <div v-for="(question, index) in questions" :key="question.id" class="card mb-4">
          <div class="card-body">
            <h5 class="card-title mb-3">
              {{ index + 1 }}. {{ question.question_statement }}
            </h5>

            <div class="form-check mb-2" v-for="option in [1, 2, 3, 4]" :key="option">
              <input
                class="form-check-input"
                type="radio"
                :name="'question_' + question.id"
                :id="'option' + option + '_' + question.id"
                :value="option"
                v-model="answers[question.id]"
              />
              <label class="form-check-label" :for="'option' + option + '_' + question.id">
                {{ question['option' + option] }}
              </label>
            </div>
          </div>
        </div>

        <!-- Submit Button -->
        <div class="d-grid gap-2">
          <button @click="submitAnswers" class="btn btn-success">Submit Quiz</button>
        </div>
      </div>

      <!-- No Questions Found -->
      <div v-else class="alert alert-info">
        No questions found for this quiz.
      </div>
    </div>
  `,
  data() {
    return {
      questions: [],
      answers: {},
      loading: true,
      quizDuration: 0, // in seconds
      timer: null
    };
  },
  computed: {
    formattedTime() {
      const minutes = Math.floor(this.quizDuration / 60);
      const seconds = this.quizDuration % 60;
      return `${minutes}:${seconds.toString().padStart(2, '0')}`;
    }
  },
  created() {
    this.fetchQuiz();
  },
  methods: {
    fetchQuiz() {
      const quizId = this.$route.params.quizId;
      this.$http.get(`/attempt_quiz/${quizId}`)
        .then(response => {
          this.questions = response.data.questions || [];
          this.quizDuration = (response.data.time_duration || 10) * 60; // Convert mins to sec
          this.startTimer();
          this.loading = false;
        })
        .catch(error => {
          this.loading = false;
          alert('Error loading quiz: ' + (error.response?.data?.error || error.message));
        });
    },
    startTimer() {
      this.timer = setInterval(() => {
        if (this.quizDuration > 0) {
          this.quizDuration--;
        } else {
          clearInterval(this.timer);
          alert('Time is up! Auto-submitting quiz.');
          this.submitAnswers();
        }
      }, 1000);
    },
    submitAnswers() {
      clearInterval(this.timer);
      const quizId = this.$route.params.quizId;
      this.$http.post(`/submit_quiz/${quizId}`, { answers: this.answers })
        .then(response => {
          alert(`Quiz submitted! Your score: ${response.data.score.toFixed(2)}%`);
          this.$router.push(`/view_answers/${quizId}`);
        })
        .catch(error => {
          alert('Error submitting quiz: ' + (error.response?.data?.error || error.message));
        });
    }
  },
  beforeUnmount() {
    clearInterval(this.timer); // Cleanup timer on component exit
  }
};


const ChapterQuizzesComponent = {
  template: `
    <div class="container">
      <h2 class="mb-4">Chapter Quizzes</h2>

      <!-- Loading Spinner -->
      <div v-if="loading" class="text-center">
        <div class="spinner-border" role="status">
          <span class="visually-hidden">Loading...</span>
        </div>
      </div>

      <!-- Main Content -->
      <div v-else>
        <!-- Breadcrumb -->
        <nav aria-label="breadcrumb" class="mb-4">
          <ol class="breadcrumb">
            <li class="breadcrumb-item">
              <router-link to="/user_dashboard">Dashboard</router-link>
            </li>
            <li class="breadcrumb-item">
              <router-link :to="\`/chapters/\${subjectId}\`">{{ subjectName }}</router-link>
            </li>
            <li class="breadcrumb-item active" aria-current="page">{{ chapterName }}</li>
          </ol>
        </nav>

        <!-- Quizzes Grid -->
        <div class="row">
          <div
            class="col-md-6 col-lg-4 mb-4"
            v-for="quiz in quizzes"
            :key="quiz.id"
          >
            <div class="card h-100 shadow-sm">
              <div class="card-body">
                <h5 class="card-title">Quiz {{ quiz.id }}</h5>
                <p class="card-text">
                  <strong>Date:</strong> {{ formatDate(quiz.date_of_quiz) }}<br />
                  <strong>Duration:</strong> {{ quiz.time_duration }} minutes
                </p>
                <p class="card-text" v-if="quiz.remarks">
                  <em>{{ quiz.remarks }}</em>
                </p>
                <div class="d-grid gap-2">
                  <router-link
                    :to="\`/attempt_quiz/\${quiz.id}\`"
                    class="btn btn-primary"
                  >
                    Attempt Quiz
                  </router-link>
                </div>
              </div>
            </div>
          </div>

          <!-- No Quizzes -->
          <div v-if="quizzes.length === 0" class="col-12">
            <div class="alert alert-info text-center">
              No quizzes available for this chapter.
            </div>
          </div>
        </div>

        <!-- Back Button -->
        <div class="d-grid gap-2 mt-4">
          <router-link
            :to="\`/chapters/\${subjectId}\`"
            class="btn btn-secondary"
          >
            Back to Chapters
          </router-link>
        </div>
      </div>
    </div>
  `,
  data() {
    return {
      quizzes: [],
      chapterName: '',
      subjectName: '',
      subjectId: null,
      loading: true
    };
  },
  created() {
    this.fetchQuizzes();
  },
  methods: {
    fetchQuizzes() {
      const chapterId = this.$route.params.chapterId;
      this.$http
        .get(`/api/chapter_quizzes/${chapterId}`)
        .then(response => {
          const data = response.data;
          this.quizzes = data.quizzes || [];
          this.chapterName = data.chapter_name || 'Chapter';
          this.subjectName = data.subject_name || 'Subject';
          this.subjectId = data.subject_id;
          this.loading = false;
        })
        .catch(error => {
          console.error('Error fetching quizzes:', error);
          alert('Error loading quizzes: ' + (error.response?.data?.error || error.message));
          this.loading = false;
        });
    },
    formatDate(dateString) {
      if (!dateString) return 'N/A';
      const date = new Date(dateString);
      return date.toLocaleDateString(undefined, {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      });
    }
  }
};

const ChaptersComponent = {
  template: `
    <div class="container">
      <h2 class="mb-4">Chapters</h2>

      <!-- Loading Spinner -->
      <div v-if="loading" class="text-center">
        <div class="spinner-border" role="status">
          <span class="visually-hidden">Loading...</span>
        </div>
      </div>

      <!-- Main Content -->
      <div v-else>
        <!-- Breadcrumb -->
        <nav aria-label="breadcrumb" class="mb-4">
          <ol class="breadcrumb">
            <li class="breadcrumb-item">
              <router-link to="/user_dashboard">Dashboard</router-link>
            </li>
            <li class="breadcrumb-item active" aria-current="page">
              {{ subjectName }}
            </li>
          </ol>
        </nav>

        <!-- Chapters List -->
        <div class="row">
          <div
            class="col-md-6 col-lg-4 mb-4"
            v-for="chapter in chapters"
            :key="chapter.id"
          >
            <div class="card h-100 shadow-sm">
              <div class="card-body">
                <h5 class="card-title">{{ chapter.name }}</h5>
                <div class="d-grid gap-2">
                  <router-link
                    :to="\`/chapter_quizzes/\${chapter.id}\`"
                    class="btn btn-primary"
                  >
                    View Quizzes
                  </router-link>
                </div>
              </div>
            </div>
          </div>

          <!-- No Chapters -->
          <div v-if="chapters.length === 0" class="col-12">
            <div class="alert alert-info text-center">
              No chapters available for this subject.
            </div>
          </div>
        </div>

        <!-- Back Button -->
        <div class="d-grid gap-2 mt-4">
          <router-link to="/user_dashboard" class="btn btn-secondary">
            Back to Dashboard
          </router-link>
        </div>
      </div>
    </div>
  `,
  data() {
    return {
      chapters: [],
      subjectName: '',
      loading: true
    };
  },
  created() {
    this.fetchChapters();
  },
  methods: {
    fetchChapters() {
      const subjectId = this.$route.params.subjectId;
      this.$http
        .get(`/api/chapters/${subjectId}`)
        .then(response => {
          const data = response.data;
          this.chapters = data.chapters || [];
          this.subjectName = data.subject_name || 'Subject';
          this.loading = false;
        })
        .catch(error => {
          console.error('Error fetching chapters:', error);
          alert('Error loading chapters: ' + (error.response?.data?.error || error.message));
          this.loading = false;
        });
    }
  }
};

const CreateQuizComponent = {
  template: `
    <div class="container">
      <h2 class="mb-4">Create Quiz</h2>

      <!-- Breadcrumb -->
      <nav aria-label="breadcrumb" class="mb-4">
        <ol class="breadcrumb">
          <li class="breadcrumb-item">
            <router-link to="/admin_dashboard">Admin Dashboard</router-link>
          </li>
          <li class="breadcrumb-item active" aria-current="page">Create Quiz</li>
        </ol>
      </nav>

      <!-- Loading Spinner -->
      <div v-if="loading" class="text-center">
        <div class="spinner-border" role="status">
          <span class="visually-hidden">Loading...</span>
        </div>
      </div>

      <!-- Main Form -->
      <div v-else>
        <!-- Quiz Info -->
        <div class="card mb-4 shadow-sm">
          <div class="card-body">
            <h5 class="card-title">Quiz Details</h5>
            <div class="mb-3">
              <label for="chapterName" class="form-label">Chapter</label>
              <input type="text" class="form-control" id="chapterName" v-model="chapterName" readonly>
            </div>
            <div class="mb-3">
              <label for="quizDate" class="form-label">Quiz Date</label>
              <input type="date" class="form-control" id="quizDate" v-model="quizDate" required>
            </div>
            <div class="mb-3">
              <label for="quizRemarks" class="form-label">Remarks</label>
              <textarea class="form-control" id="quizRemarks" v-model="quizRemarks" rows="3" placeholder="Optional remarks for the quiz"></textarea>
            </div>
          </div>
        </div>

        <!-- Questions Section -->
        <h5 class="mb-3">Questions</h5>
        <div
          class="card mb-3 shadow-sm"
          v-for="(question, index) in questions"
          :key="index"
        >
          <div class="card-body">
            <div class="d-flex justify-content-between align-items-center mb-3">
              <h6 class="card-title mb-0">Question {{ index + 1 }}</h6>
              <button class="btn btn-sm btn-danger" @click="removeQuestion(index)">
                <i class="fas fa-trash-alt"></i> Remove
              </button>
            </div>

            <div class="mb-3">
              <label :for="'questionStatement' + index" class="form-label">Question Statement</label>
              <textarea
                :id="'questionStatement' + index"
                class="form-control"
                v-model="question.statement"
                rows="2"
                required
              ></textarea>
            </div>

            <div class="row" v-for="optionIndex in 4" :key="optionIndex">
              <div class="col-md-10 mb-2">
                <label :for="'option' + optionIndex + 'q' + index" class="form-label">Option {{ optionIndex }}</label>
                <input
                  type="text"
                  :id="'option' + optionIndex + 'q' + index"
                  class="form-control"
                  v-model="question['option' + optionIndex]"
                  required
                />
              </div>
              <div class="col-md-2 d-flex align-items-end mb-2">
                <div class="form-check">
                  <input
                    class="form-check-input"
                    type="radio"
                    :name="'correctOption' + index"
                    :id="'correctOption' + optionIndex + 'q' + index"
                    :value="optionIndex"
                    v-model="question.correctOption"
                  />
                  <label class="form-check-label" :for="'correctOption' + optionIndex + 'q' + index">
                    Correct
                  </label>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Action Buttons -->
        <div class="d-grid gap-2">
          <button class="btn btn-primary mb-3" @click="addQuestion">
            <i class="fas fa-plus"></i> Add Question
          </button>
          <button
            class="btn btn-success mb-3"
            @click="saveQuiz"
            :disabled="!canSubmit"
          >
            <i class="fas fa-save"></i> Save Quiz
          </button>
          <router-link to="/admin_dashboard" class="btn btn-secondary">
            Cancel
          </router-link>
        </div>
      </div>
    </div>
  `,
  data() {
    return {
      chapterId: this.$route.params.chapterId,
      chapterName: '',
      quizDate: new Date().toISOString().substr(0, 10),
      quizRemarks: '',
      questions: [],
      loading: true
    };
  },
  computed: {
    canSubmit() {
      return this.questions.length > 0 &&
        this.questions.every(q =>
          q.statement &&
          q.option1 && q.option2 && q.option3 && q.option4 &&
          q.correctOption
        );
    }
  },
  created() {
    this.fetchChapterDetails();
  },
  methods: {
    fetchChapterDetails() {
      this.$http.get(`/api/chapter/${this.chapterId}`)
        .then(response => {
          this.chapterName = response.data.name;
          this.loading = false;
        })
        .catch(error => {
          console.error('Error fetching chapter details:', error);
          alert('Error loading chapter details: ' + (error.response?.data?.error || error.message));
          this.loading = false;
        });
    },
    addQuestion() {
      this.questions.push({
        statement: '',
        option1: '',
        option2: '',
        option3: '',
        option4: '',
        correctOption: null
      });
    },
    removeQuestion(index) {
      this.questions.splice(index, 1);
    },
    saveQuiz() {
      if (!this.canSubmit) {
        alert('Please complete all questions and mark the correct answer.');
        return;
      }

      const quizData = {
        chapter_id: this.chapterId,
        date_of_quiz: this.quizDate,
        time_duration: this.timeDuration,
        remarks: this.quizRemarks
      };

      this.$http.post('/admin/quizzes', quizData)
        .then(() => {
          alert('Quiz created successfully!');
          this.$router.push('/admin_dashboard');
        })
        .catch(error => {
          console.error('Error creating quiz:', error);
          alert('Error creating quiz: ' + (error.response?.data?.error || error.message));
        });
    }
  }
};

const QuizHistoryComponent = {
  template: `
    <div class="container">
      <h2 class="mb-4">Quiz History</h2>

      <div v-if="loading" class="text-center">
        <div class="spinner-border" role="status">
          <span class="visually-hidden">Loading...</span>
        </div>
      </div>

      <div v-else>
        <div class="row mb-4">
          <div class="col-md-8">
            <input
              type="text"
              v-model="searchTerm"
              class="form-control"
              placeholder="Search by subject or chapter..."
            />
          </div>
          <div class="col-md-4">
            <button
              class="btn btn-primary w-100"
              @click="exportQuizData"
              :disabled="exportInProgress"
            >
              <i class="fas fa-file-export me-2"></i>
              {{ exportInProgress ? 'Exporting...' : 'Export CSV' }}
            </button>
          </div>
        </div>

        <div v-if="exportStatus" class="alert" :class="exportStatusClass" role="alert">
          {{ exportStatus }}
        </div>

        <div class="table-responsive">
          <table class="table table-striped align-middle">
            <thead>
              <tr>
                <th>Subject</th>
                <th>Chapter</th>
                <th>Quiz Date</th>
                <th>Attempt Date</th>
                <th>Score</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(attempt, index) in filteredAttempts" :key="index">
                <td>{{ attempt.subject_name }}</td>
                <td>{{ attempt.chapter_name }}</td>
                <td>{{ formatDate(attempt.quiz_date) }}</td>
                <td>{{ formatDate(attempt.time_of_attempt) }}</td>
                <td>
                  <div class="progress" style="height: 25px;">
                    <div
                      class="progress-bar"
                      role="progressbar"
                      :style="{ width: attempt.score + '%' }"
                      :class="getScoreClass(attempt.score)"
                      :aria-valuenow="attempt.score"
                      aria-valuemin="0"
                      aria-valuemax="100"
                    >
                      {{ attempt.score }}%
                    </div>
                  </div>
                </td>
                <td>
                  <router-link
                    :to="'/view_answers/' + attempt.quiz_id"
                    class="btn btn-sm btn-info"
                    title="View Answers"
                  >
                    View
                  </router-link>
                </td>
              </tr>

              <tr v-if="filteredAttempts.length === 0">
                <td colspan="6" class="text-center">No quiz history found</td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="d-grid gap-2 mt-4">
          <router-link to="/user_dashboard" class="btn btn-secondary">
            Back to Dashboard
          </router-link>
        </div>
      </div>
    </div>
  `,
  data() {
    return {
      attempts: [],
      loading: true,
      searchTerm: '',
      exportInProgress: false,
      exportStatus: '',
      exportStatusClass: 'alert-info'
    };
  },
  computed: {
    filteredAttempts() {
      if (!this.searchTerm) return this.attempts;

      const term = this.searchTerm.toLowerCase();
      return this.attempts.filter(
        attempt =>
          attempt.subject_name.toLowerCase().includes(term) ||
          attempt.chapter_name.toLowerCase().includes(term)
      );
    }
  },
  created() {
    this.fetchHistory();
  },
  methods: {
    fetchHistory() {
      this.$http.get('/api/quiz_history')
        .then(response => {
          this.attempts = response.data.history || [];
          this.loading = false;
        })
        .catch(error => {
          console.error('Error fetching quiz history:', error);
          alert('Error loading quiz history: ' +
            (error.response && error.response.data && error.response.data.error
              ? error.response.data.error
              : error.message));
          this.loading = false;
        });
    },
    formatDate(dateString) {
      if (!dateString) return 'N/A';
      const date = new Date(dateString);
      return `${date.toLocaleDateString()} ${date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
    },
    getScoreClass(score) {
      if (score >= 80) return 'bg-success';
      if (score >= 60) return 'bg-info';
      if (score >= 40) return 'bg-warning';
      return 'bg-danger';
    },
    exportQuizData() {
      if (this.exportInProgress) return;

      this.exportInProgress = true;
      this.exportStatus = 'Initiating export...';
      this.exportStatusClass = 'alert-info';

      this.$http.post('/api/export-user-quiz-csv')
        .then(response => {
          if (response.data.success) {
            this.exportStatus = response.data.message;
            this.checkTaskStatus(response.data.task_id);
          } else {
            this.exportStatus = `Export failed: ${response.data.message}`;
            this.exportStatusClass = 'alert-danger';
            this.exportInProgress = false;
          }
        })
        .catch(error => {
          console.error('Error exporting quiz data:', error);
          this.exportStatus = 'Export failed: Network error';
          this.exportStatusClass = 'alert-danger';
          this.exportInProgress = false;
        });
    },
    checkTaskStatus(taskId) {
      const statusInterval = setInterval(() => {
        this.$http.get(`/api/task-status/${taskId}`)
          .then(response => {
            if (response.data.success) {
              const status = response.data.status;
              if (status === 'SUCCESS') {
                clearInterval(statusInterval);
                this.exportStatus = 'Export completed successfully! Check your email for the file.';
                this.exportStatusClass = 'alert-success';
                this.exportInProgress = false;
              } else if (status === 'FAILURE') {
                clearInterval(statusInterval);
                this.exportStatus = `Export failed: ${response.data.info || 'Unknown error'}`;
                this.exportStatusClass = 'alert-danger';
                this.exportInProgress = false;
              } else {
                this.exportStatus = `Export in progress: ${status}`;
                this.exportStatusClass = 'alert-info';
              }
            } else {
              clearInterval(statusInterval);
              this.exportStatus = `Error checking export status: ${response.data.message}`;
              this.exportStatusClass = 'alert-warning';
              this.exportInProgress = false;
            }
          })
          .catch(error => {
            clearInterval(statusInterval);
            console.error('Error checking task status:', error);
            this.exportStatus = 'Error checking export status';
            this.exportStatusClass = 'alert-danger';
            this.exportInProgress = false;
          });
      }, 2000);

      setTimeout(() => {
        clearInterval(statusInterval);
        if (this.exportInProgress) {
          this.exportStatus = 'Export is taking longer than expected. Check your email later.';
          this.exportStatusClass = 'alert-warning';
          this.exportInProgress = false;
        }
      }, 120000);
    }
  }
};


const QuizQuestionsComponent = {
  template: `
    <div>
      <h2>Quiz Questions</h2>
      <p>Quiz ID: {{ $route.params.quizId }}</p>
    </div>
  `
};

const ViewAnswersComponent = {
  template: `
    <div class="container">
      <h2 class="mb-4">Quiz Results</h2>
      <div v-if="loading" class="text-center">
        <div class="spinner-border" role="status">
          <span class="visually-hidden">Loading...</span>
        </div>
      </div>
      <div v-else>
        <div class="card mb-4">
          <div class="card-body">
            <h5 class="card-title">Summary</h5>
            <div class="row">
              <div class="col-md-6">
                <p class="mb-1"><strong>Your Score:</strong> {{ score }}%</p>
                <div class="progress mb-4">
                  <div 
                    class="progress-bar" 
                    role="progressbar" 
                    :style="{ width: score + '%' }" 
                    :class="scoreClass" 
                    :aria-valuenow="score" 
                    aria-valuemin="0" 
                    aria-valuemax="100"
                  ></div>
                </div>
              </div>
              <div class="col-md-6">
                <p v-if="remarks" class="mb-0"><strong>Remarks:</strong> {{ remarks }}</p>
              </div>
            </div>
          </div>
        </div>

        <div class="mb-4">
          <h5>Questions and Answers</h5>
          <div 
            v-for="(question, index) in questions" 
            :key="question.id" 
            class="card mb-3"
          >
            <div class="card-body">
              <h6 class="card-title">Question {{ index + 1 }}</h6>
              <p>{{ question.question_statement }}</p>
              <div class="list-group">
                <div 
                  v-for="i in 4" 
                  :key="i" 
                  class="list-group-item" 
                  :class="{ 'list-group-item-success': question.correct_option === i }"
                >
                  <div class="d-flex w-100 justify-content-between">
                    <span>{{ question['option' + i] }}</span>
                    <span v-if="question.correct_option === i">
                      <i class="fas fa-check-circle text-success"></i> Correct Answer
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <div class="d-grid gap-2">
          <router-link to="/quiz_history" class="btn btn-primary">
            View Quiz History
          </router-link>
          <router-link to="/user_dashboard" class="btn btn-secondary">
            Back to Dashboard
          </router-link>
        </div>
      </div>
    </div>
  `,
  data() {
    return {
      questions: [],
      score: 0,
      remarks: '',
      loading: true,
    };
  },
  computed: {
    scoreClass() {
      if (this.score >= 80) return 'bg-success';
      if (this.score >= 60) return 'bg-info';
      if (this.score >= 40) return 'bg-warning';
      return 'bg-danger';
    }
  },
  created() {
    this.fetchAnswers();
  },
  methods: {
    fetchAnswers() {
      this.$http.get(`/api/view_answers/${this.$route.params.quizId}`)
        .then(response => {
          this.questions = response.data.questions || [];
          this.score = response.data.score || 0;
          this.remarks = response.data.remarks || '';
          this.loading = false;
        })
        .catch(error => {
          console.error('Error fetching quiz answers:', error);
          alert('Error loading quiz answers: ' + (error.response?.data?.error || error.message));
          this.loading = false;
        });
    }
  }
};

// AdminLoginComponent removed - using unified login system

const SearchResultsComponent = { template: '<div><h2>Search Results</h2><p>Query: {{ $route.query.q }}</p></div>' };
// These components are now properly defined in their respective .vue files
// The routing will automatically load them from the components directory
const ViewQuizComponent = { template: '<div><h2>View Quiz</h2><p>Quiz ID: {{ $route.params.quizId }}</p></div>' };
const ViewQuizUsersComponent = { template: '<div><h2>View Quiz Users</h2><p>Quiz ID: {{ $route.params.quizId }}</p></div>' };
const ViewSubjectComponent = { template: '<div><h2>View Subject</h2><p>Subject ID: {{ $route.params.subjectId }}</p></div>' };
const ViewUsersComponent = {
  template: `
    <div class="container">
      <h2 class="mb-4">Manage Users</h2>
      
      <!-- Loading Spinner -->
      <div v-if="loading" class="text-center">
        <div class="spinner-border" role="status">
          <span class="visually-hidden">Loading...</span>
        </div>
      </div>

      <!-- Users List -->
      <div v-else>
        <div class="row mb-3">
          <div class="col-md-6">
            <h4>All Users ({{ users.length }})</h4>
          </div>
        </div>

        <div v-if="users.length === 0" class="alert alert-info">
          No users found.
        </div>

        <div v-else class="table-responsive">
          <table class="table table-striped">
            <thead>
              <tr>
                <th>Username</th>
                <th>Full Name</th>
                <th>Qualification</th>
                <th>Date of Birth</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="user in users" :key="user.id">
                <td>{{ user.username }}</td>
                <td>{{ user.full_name }}</td>
                <td>{{ user.qualification || 'N/A' }}</td>
                <td>{{ formatDate(user.dob) }}</td>
                <td>
                  <div class="btn-group" role="group">
                    <a :href="'#/view_user/' + user.id" class="btn btn-sm btn-info">View</a>
                    <button @click="deleteUser(user.id)" class="btn btn-sm btn-outline-danger">Delete</button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div class="mt-3">
        <a href="#/admin_dashboard" class="btn btn-secondary">Back to Dashboard</a>
      </div>
    </div>
  `,
  data() {
    return {
      users: [],
      loading: true
    };
  },
  created() {
    this.fetchUsers();
  },
  methods: {
    fetchUsers() {
      const adminToken = localStorage.getItem('admin_token');
      if (!adminToken) {
        console.log('No admin token found, redirecting to login');
        this.$router.push('/login');
        return;
      }
      
      this.$http.get('/admin/users', {
        headers: { 'Authorization': `Bearer ${adminToken}` }
      }).then(response => {
        console.log('Fetch users response:', response);
        if (response.data.status === 'success') {
          this.users = response.data.users;
        } else {
          console.error('Failed to fetch users:', response.data.message);
        }
        this.loading = false;
      }).catch(error => {
        console.error('Error fetching users:', error);
        this.loading = false;
      });
    },
    deleteUser(userId) {
      if (!confirm('Are you sure you want to delete this user?')) {
        return;
      }
      
      const adminToken = localStorage.getItem('admin_token');
      if (!adminToken) {
        this.$router.push('/login');
        return;
      }
      
      this.$http.delete(`/api/v2/admin/users/${userId}`, {
        headers: { 'Authorization': `Bearer ${adminToken}` }
      }).then(response => {
        if (response.data.status === 'success') {
          alert('User deleted successfully!');
          this.fetchUsers(); // Refresh the list
        } else {
          alert('Error: ' + response.data.message);
        }
      }).catch(error => {
        console.error('Error deleting user:', error);
        alert('Error deleting user. Please try again.');
      });
    },
    formatDate(dateString) {
      if (!dateString) return 'N/A';
      const date = new Date(dateString);
      return date.toLocaleDateString();
    }
  }
};

const ViewUserComponent = {
  template: `
    <div class="container">
      <h1>Quiz Master</h1>
      <nav class="navbar navbar-light bg-light">
        <a class="navbar-brand">Welcome, Admin</a>
        <a href="#/logout" class="btn btn-outline-danger">Logout</a>
        <button @click="toggleDarkMode" class="btn btn-secondary">Dark Mode</button>
      </nav>
      <h2>User Details</h2>
      <div class="card">
        <div class="card-body">
          <p><strong>Username:</strong> {{ user.username }}</p>
          <p><strong>Full Name:</strong> {{ user.full_name }}</p>
          <p><strong>Qualification:</strong> {{ user.qualification || 'N/A' }}</p>
          <p><strong>Date of Birth:</strong> {{ user.dob || 'N/A' }}</p>
        </div>
      </div>
      <a href="#/admin_dashboard" class="btn btn-secondary mt-3">Back to Admin Dashboard</a>
    </div>
  `,
  data() {
    return {
      userId: this.$route.params.userId,
      user: {}
    };
  },
  mounted() {
    const adminToken = localStorage.getItem('admin_token');
    if (!adminToken) {
      alert('Please login as admin first');
      this.$router.push('/login');
      return;
    }
    
    this.$http.get(`/api/v2/admin/users/${this.userId}`, {
      headers: { 'Authorization': `Bearer ${adminToken}` }
    }).then(response => {
      if (response.data.status === 'success') {
        this.user = response.data.user;
      }
    }).catch(error => {
      console.error('Error fetching user:', error);
      alert('Error fetching user details');
    });
  },
  methods: {
    toggleDarkMode() {
      document.body.classList.toggle('bg-dark');
    }
  }
};

// CRUD Components - Extracted from .vue files
const AddSubjectComponent = {
  template: `
    <div class="container">
      <h2>Add New Subject</h2>
      <form @submit.prevent="addSubject" class="needs-validation" novalidate>
        <div class="mb-3">
          <label for="name" class="form-label">Subject Name</label>
          <input v-model="name" type="text" class="form-control" id="name" required>
          <div class="invalid-feedback">Please enter a name.</div>
        </div>
        <div class="mb-3">
          <label for="description" class="form-label">Description</label>
          <input v-model="description" type="text" class="form-control" id="description">
          <div class="invalid-feedback">Please enter a description.</div>
        </div>
        <button type="submit" class="btn btn-primary">Add Subject</button>
        <p></p>
      </form>
      <a href="#/admin_dashboard" class="btn btn-secondary">Back to Dashboard</a>
    </div>
  `,
  data() {
    return {
      name: '',
      description: ''
    };
  },
  methods: {
    addSubject() {
      const form = document.querySelector('.needs-validation');
      if (!form.checkValidity()) {
        form.classList.add('was-validated');
        return;
      }
      
      // Get admin token from localStorage
      const adminToken = localStorage.getItem('admin_token');
      if (!adminToken) {
        alert('Please login as admin first');
        this.$router.push('/login');
        return;
      }
      
      this.$http.post('/api/v2/admin/subjects', 
        { name: this.name, description: this.description },
        { headers: { 'Authorization': `Bearer ${adminToken}` } }
      ).then(response => {
        if (response.data.status === 'success') {
          alert('Subject added successfully!');
          this.$router.push('/admin_dashboard');
        } else {
          alert('Error: ' + response.data.message);
        }
      }).catch(error => {
        console.error('Error adding subject:', error);
        alert('Error adding subject. Please try again.');
      });
    },
    toggleDarkMode() {
      document.body.classList.toggle('bg-dark');
    }
  }
};


//Add chapter component
const AddChapterComponent = {
  template: `
    <div class="container">
      <h2>Add New Chapter</h2>
      <!-- Subject Info -->
      <div v-if="subjectName" class="alert alert-info">
        <strong>Subject:</strong> {{ subjectName }}
      </div>
      
      <form @submit.prevent="addChapter" class="needs-validation" novalidate>
        <div class="mb-3">
          <label for="name" class="form-label">Chapter Name</label>
          <input v-model="name" type="text" class="form-control" id="name" required>
          <div class="invalid-feedback">Please enter a chapter name.</div>
        </div>
        <div class="mb-3">
          <label for="description" class="form-label">Description</label>
          <textarea v-model="description" class="form-control" id="description" rows="3" placeholder="Enter chapter description (optional)"></textarea>
        </div>
        <button type="submit" class="btn btn-primary">Add Chapter</button>
      </form>
      
      <div class="mt-3">
        <a href="#/admin_dashboard" class="btn btn-secondary">Back to Dashboard</a>
        <a href="#/view_subjects" class="btn btn-info">View All Subjects</a>
      </div>
    </div>
  `,
  data() {
    return {
      name: '',
      description: '',
      subjectId: this.$route.params.subjectId,
      subjectName: ''
    };
  },
  created() {
    this.fetchSubjectName();
  },
  methods: {
    fetchSubjectName() {
      const adminToken = localStorage.getItem('admin_token');
      if (!adminToken) {
        this.$router.push('/login');
        return;
      }
      
      this.$http.get(`/api/v2/admin/subjects/${this.subjectId}`, {
        headers: { 'Authorization': `Bearer ${adminToken}` }
      }).then(response => {
        if (response.data.status === 'success') {
          this.subjectName = response.data.subject.name;
        }
      }).catch(error => {
        console.error('Error fetching subject name:', error);
      });
    },
    addChapter() {
      const form = document.querySelector('.needs-validation');
      if (!form.checkValidity()) {
        form.classList.add('was-validated');
        return;
      }
      
      const adminToken = localStorage.getItem('admin_token');
      if (!adminToken) {
        alert('Please login as admin first');
        this.$router.push('/login');
        return;
      }
      
      this.$http.post('/api/v2/admin/chapters', 
        { 
          name: this.name, 
          description: this.description,
          subject_id: this.subjectId
        },
        { headers: { 'Authorization': `Bearer ${adminToken}` } }
      ).then(response => {
        if (response.data.status === 'success') {
          alert('Chapter added successfully!');
          this.$router.push('/admin_dashboard');
        } else {
          alert('Error: ' + response.data.message);
        }
      }).catch(error => {
        console.error('Error adding chapter:', error);
        alert('Error adding chapter. Please try again.');
      });
    },
    toggleDarkMode() {
      document.body.classList.toggle('bg-dark');
    }
  }
};

const AddQuestionComponent = {
  template: `
    <div class="container">
      <h1>Quiz Master</h1>
      <nav class="navbar navbar-light bg-light">
        <a class="navbar-brand">Add New Question</a>
        <button @click="toggleDarkMode" class="btn btn-secondary">Dark Mode</button>
      </nav>
      <h2>Add New Question</h2>
      <form @submit.prevent="addQuestion" class="needs-validation" novalidate>
        <div class="mb-3">
          <label for="question" class="form-label">Question</label>
          <textarea v-model="question" class="form-control" id="question" required></textarea>
          <div class="invalid-feedback">Please enter a question.</div>
        </div>
        <div class="mb-3">
          <label for="option1" class="form-label">Option 1</label>
          <input v-model="option1" type="text" class="form-control" id="option1" required>
        </div>
        <div class="mb-3">
          <label for="option2" class="form-label">Option 2</label>
          <input v-model="option2" type="text" class="form-control" id="option2" required>
        </div>
        <div class="mb-3">
          <label for="option3" class="form-label">Option 3</label>
          <input v-model="option3" type="text" class="form-control" id="option3" required>
        </div>
        <div class="mb-3">
          <label for="option4" class="form-label">Option 4</label>
          <input v-model="option4" type="text" class="form-control" id="option4" required>
        </div>
        <div class="mb-3">
          <label for="correct_option" class="form-label">Correct Option (1-4)</label>
          <select v-model="correct_option" class="form-control" id="correct_option" required>
            <option value="">Select correct option</option>
            <option value="1">Option 1</option>
            <option value="2">Option 2</option>
            <option value="3">Option 3</option>
            <option value="4">Option 4</option>
          </select>
        </div>
        <button type="submit" class="btn btn-primary">Add Question</button>
      </form>
      <a href="#/admin_dashboard" class="btn btn-secondary">Back to Dashboard</a>
    </div>
  `,
  data() {
    return {
      question: '',
      option1: '',
      option2: '',
      option3: '',
      option4: '',
      correct_option: '',
      quizId: this.$route.params.quizId
    };
  },
  methods: {
    addQuestion() {
      const form = document.querySelector('.needs-validation');
      if (!form.checkValidity()) {
        form.classList.add('was-validated');
        return;
      }
      
      const adminToken = localStorage.getItem('admin_token');
      if (!adminToken) {
        alert('Please login as admin first');
        this.$router.push('/login');
        return;
      }
      
      this.$http.post('/api/v2/admin/questions', 
        { 
          quiz_id: this.quizId,
          question_statement: this.question,
          option1: this.option1,
          option2: this.option2,
          option3: this.option3,
          option4: this.option4,
          correct_option: parseInt(this.correct_option)
        },
        { headers: { 'Authorization': `Bearer ${adminToken}` } }
      ).then(response => {
        if (response.data.status === 'success') {
          alert('Question added successfully!');
          this.$router.push('/admin_dashboard');
        } else {
          alert('Error: ' + response.data.message);
        }
      }).catch(error => {
        console.error('Error adding question:', error);
        alert('Error adding question. Please try again.');
      });
    },
    toggleDarkMode() {
      document.body.classList.toggle('bg-dark');
    }
  }
};

const EditSubjectComponent = {
  template: `
    <div class="container">
      <h1>Quiz Master</h1>
      <nav class="navbar navbar-light bg-light">
        <a class="navbar-brand">Edit Subject</a>
        <a href="#/logout" class="btn btn-outline-danger">Logout</a>
        <button @click="toggleDarkMode" class="btn btn-secondary">Dark Mode</button>
      </nav>
      <h2>Edit Subject</h2>
      <form @submit.prevent="editSubject" class="needs-validation" novalidate>
        <div class="mb-3">
          <label for="name" class="form-label">Subject Name</label>
          <input v-model="name" type="text" class="form-control" id="name" required>
          <div class="invalid-feedback">Please enter a name.</div>
        </div>
        <div class="mb-3">
          <label for="description" class="form-label">Description</label>
          <input v-model="description" type="text" class="form-control" id="description">
          <div class="invalid-feedback">Please enter a description.</div>
        </div>
        <button type="submit" class="btn btn-primary">Save Changes</button>
      </form>
      <a href="#/admin_dashboard" class="btn btn-secondary">Back to Dashboard</a>
    </div>
  `,
  data() {
    return {
      subjectId: this.$route.params.subjectId,
      name: '',
      description: ''
    };
  },
  mounted() {
    // Get admin token from localStorage
    const adminToken = localStorage.getItem('admin_token');
    if (!adminToken) {
      alert('Please login as admin first');
      this.$router.push('/login');
      return;
    }
    
    this.$http.get(`/api/v2/admin/subjects/${this.subjectId}`, 
      { headers: { 'Authorization': `Bearer ${adminToken}` } }
    ).then(response => {
      if (response.data.status === 'success') {
        this.name = response.data.subject.name;
        this.description = response.data.subject.description;
      }
    }).catch(error => {
      console.error('Error loading subject:', error);
      alert('Error loading subject data.');
    });
  },
  methods: {
    editSubject() {
      const form = document.querySelector('.needs-validation');
      if (!form.checkValidity()) {
        form.classList.add('was-validated');
        return;
      }
      
      // Get admin token from localStorage
      const adminToken = localStorage.getItem('admin_token');
      if (!adminToken) {
        alert('Please login as admin first');
        this.$router.push('/login');
        return;
      }
      
      this.$http.put(`/api/v2/admin/subjects/${this.subjectId}`, 
        { name: this.name, description: this.description },
        { headers: { 'Authorization': `Bearer ${adminToken}` } }
      ).then(response => {
        if (response.data.status === 'success') {
          alert('Subject updated successfully!');
          this.$router.push('/admin_dashboard');
        } else {
          alert('Error: ' + response.data.message);
        }
      }).catch(error => {
        console.error('Error updating subject:', error);
        alert('Error updating subject. Please try again.');
      });
    },
    toggleDarkMode() {
      document.body.classList.toggle('bg-dark');
    }
  }
};

const EditChapterComponent = {
  template: `
    <div class="container">
      <h1>Quiz Master</h1>
      <nav class="navbar navbar-light bg-light">
        <a class="navbar-brand">Edit Chapter</a>
        <a href="#/logout" class="btn btn-outline-danger">Logout</a>
        <button @click="toggleDarkMode" class="btn btn-secondary">Dark Mode</button>
      </nav>
      <h2>Edit Chapter</h2>
      <form @submit.prevent="editChapter" class="needs-validation" novalidate>
        <div class="mb-3">
          <label for="name" class="form-label">Chapter Name</label>
          <input v-model="name" type="text" class="form-control" id="name" required>
          <div class="invalid-feedback">Please enter a name.</div>
        </div>
        <div class="mb-3">
          <label for="description" class="form-label">Description</label>
          <input v-model="description" type="text" class="form-control" id="description">
          <div class="invalid-feedback">Please enter a description.</div>
        </div>
        <button type="submit" class="btn btn-primary">Save Changes</button>
      </form>
      <a href="#/admin_dashboard" class="btn btn-secondary">Back to Dashboard</a>
    </div>
  `,
  data() {
    return {
      chapterId: this.$route.params.chapterId,
      name: '',
      description: ''
    };
  },
  mounted() {
    const adminToken = localStorage.getItem('admin_token');
    if (!adminToken) {
      alert('Please login as admin first');
      this.$router.push('/login');
      return;
    }
    
    this.$http.get(`/api/v2/admin/chapters/${this.chapterId}`, 
      { headers: { 'Authorization': `Bearer ${adminToken}` } }
    ).then(response => {
      if (response.data.status === 'success') {
        this.name = response.data.chapter.name;
        this.description = response.data.chapter.description;
      }
    }).catch(error => {
      console.error('Error loading chapter:', error);
      alert('Error loading chapter data.');
    });
  },
  methods: {
    editChapter() {
      const form = document.querySelector('.needs-validation');
      if (!form.checkValidity()) {
        form.classList.add('was-validated');
        return;
      }
      
      const adminToken = localStorage.getItem('admin_token');
      if (!adminToken) {
        alert('Please login as admin first');
        this.$router.push('/login');
        return;
      }
      
      this.$http.put(`/api/v2/admin/chapters/${this.chapterId}`, 
        { name: this.name, description: this.description },
        { headers: { 'Authorization': `Bearer ${adminToken}` } }
      ).then(response => {
        if (response.data.status === 'success') {
          alert('Chapter updated successfully!');
          this.$router.push('/admin_dashboard');
        } else {
          alert('Error: ' + response.data.message);
        }
      }).catch(error => {
        console.error('Error updating chapter:', error);
        alert('Error updating chapter. Please try again.');
      });
    },
    toggleDarkMode() {
      document.body.classList.toggle('bg-dark');
    }
  }
};

const EditQuizComponent = {
  template: `
    <div class="container">
      <h1>Quiz Master</h1>
      <nav class="navbar navbar-light bg-light">
        <a class="navbar-brand">Edit Quiz</a>
        <a href="#/logout" class="btn btn-outline-danger">Logout</a>
        <button @click="toggleDarkMode" class="btn btn-secondary">Dark Mode</button>
      </nav>
      <h2>Edit Quiz</h2>
      <form @submit.prevent="editQuiz" class="needs-validation" novalidate>
        <div class="mb-3">
          <label for="title" class="form-label">Quiz Title</label>
          <input v-model="title" type="text" class="form-control" id="title" required>
          <div class="invalid-feedback">Please enter a title.</div>
        </div>
        <div class="mb-3">
          <label for="description" class="form-label">Description</label>
          <input v-model="description" type="text" class="form-control" id="description">
          <div class="invalid-feedback">Please enter a description.</div>
        </div>
        <div class="mb-3">
          <label for="time_limit" class="form-label">Time Limit (minutes)</label>
          <input v-model="time_limit" type="number" class="form-control" id="time_limit" required>
          <div class="invalid-feedback">Please enter a time limit.</div>
        </div>
        <button type="submit" class="btn btn-primary">Save Changes</button>
      </form>
      <a href="#/admin_dashboard" class="btn btn-secondary">Back to Dashboard</a>
    </div>
  `,
  data() {
    return {
      quizId: this.$route.params.quizId,
      title: '',
      description: '',
      time_limit: ''
    };
  },
  mounted() {
    const adminToken = localStorage.getItem('admin_token');
    if (!adminToken) {
      alert('Please login as admin first');
      this.$router.push('/login');
      return;
    }
    
    this.$http.get(`/api/v2/admin/quizzes/${this.quizId}`, 
      { headers: { 'Authorization': `Bearer ${adminToken}` } }
    ).then(response => {
      if (response.data.status === 'success') {
        this.title = response.data.quiz.title;
        this.description = response.data.quiz.description;
        this.time_limit = response.data.quiz.time_limit;
      }
    }).catch(error => {
      console.error('Error loading quiz:', error);
      alert('Error loading quiz data.');
    });
  },
  methods: {
    editQuiz() {
      const form = document.querySelector('.needs-validation');
      if (!form.checkValidity()) {
        form.classList.add('was-validated');
        return;
      }
      
      const adminToken = localStorage.getItem('admin_token');
      if (!adminToken) {
        alert('Please login as admin first');
        this.$router.push('/login');
        return;
      }
      
      this.$http.put(`/api/v2/admin/quizzes/${this.quizId}`, 
        { 
          title: this.title, 
          description: this.description,
          time_limit: parseInt(this.time_limit)
        },
        { headers: { 'Authorization': `Bearer ${adminToken}` } }
      ).then(response => {
        if (response.data.status === 'success') {
          alert('Quiz updated successfully!');
          this.$router.push('/admin_dashboard');
        } else {
          alert('Error: ' + response.data.message);
        }
      }).catch(error => {
        console.error('Error updating quiz:', error);
        alert('Error updating quiz. Please try again.');
      });
    },
    toggleDarkMode() {
      document.body.classList.toggle('bg-dark');
    }
  }
};

const ViewSubjectsComponent = {
  template: `
    <div class="container">
      <h2 class="mb-4">Manage Subjects</h2>
      
      <!-- Loading Spinner -->
      <div v-if="loading" class="text-center">
        <div class="spinner-border" role="status">
          <span class="visually-hidden">Loading...</span>
        </div>
      </div>

      <!-- Subjects List -->
      <div v-else>
        <div class="row mb-3">
          <div class="col-md-6">
            <h4>All Subjects ({{ subjects.length }})</h4>
          </div>
          <div class="col-md-6 text-end">
            <a href="#/add_subject" class="btn btn-primary">Add New Subject</a>
          </div>
        </div>

        <div v-if="subjects.length === 0" class="alert alert-info">
          No subjects found. <a href="#/add_subject">Create your first subject</a>
        </div>

        <div v-else class="row">
          <div v-for="subject in subjects" :key="subject.id" class="col-md-6 mb-3">
            <div class="card">
              <div class="card-body">
                <h5 class="card-title">{{ subject.name }}</h5>
                <p class="card-text">{{ subject.description || 'No description' }}</p>
                <div class="d-flex justify-content-between align-items-center">
                  <small class="text-muted">
                    Created: {{ formatDate(subject.created_at) }}
                  </small>
                  <div class="btn-group" role="group">
                    <a :href="'#/edit_subject/' + subject.id" class="btn btn-sm btn-outline-primary">Edit</a>
                    <a :href="'#/add_chapter/' + subject.id" class="btn btn-sm btn-success">Add Chapter</a>
                    <button @click="deleteSubject(subject.id)" class="btn btn-sm btn-outline-danger">Delete</button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="mt-3">
        <a href="#/admin_dashboard" class="btn btn-secondary">Back to Dashboard</a>
      </div>
    </div>
  `,
  data() {
    return {
      subjects: [],
      loading: true
    };
  },
  created() {
    this.fetchSubjects();
  },
  methods: {
    fetchSubjects() {
      const adminToken = localStorage.getItem('admin_token');
      if (!adminToken) {
        this.$router.push('/login');
        return;
      }
      
      this.$http.get('/api/v2/admin/subjects', {
        headers: { 'Authorization': `Bearer ${adminToken}` }
      }).then(response => {
        if (response.data.status === 'success') {
          this.subjects = response.data.subjects;
        }
        this.loading = false;
      }).catch(error => {
        console.error('Error fetching subjects:', error);
        this.loading = false;
      });
    },
    deleteSubject(subjectId) {
      if (!confirm('Are you sure you want to delete this subject? This will also delete all associated chapters and quizzes.')) {
        return;
      }
      
      const adminToken = localStorage.getItem('admin_token');
      if (!adminToken) {
        this.$router.push('/login');
        return;
      }
      
      this.$http.delete(`/api/v2/admin/subjects/${subjectId}`, {
        headers: { 'Authorization': `Bearer ${adminToken}` }
      }).then(response => {
        if (response.data.status === 'success') {
          alert('Subject deleted successfully!');
          this.fetchSubjects(); // Refresh the list
        } else {
          alert('Error: ' + response.data.message);
        }
      }).catch(error => {
        console.error('Error deleting subject:', error);
        alert('Error deleting subject. Please try again.');
      });
    },
    formatDate(dateString) {
      if (!dateString) return 'N/A';
      const date = new Date(dateString);
      return date.toLocaleDateString();
    }
  }
};

const ViewChaptersComponent = {
  template: `
    <div class="container">
      <h2 class="mb-4">Manage Chapters</h2>
      
      <!-- Loading Spinner -->
      <div v-if="loading" class="text-center">
        <div class="spinner-border" role="status">
          <span class="visually-hidden">Loading...</span>
        </div>
      </div>

      <!-- Chapters List -->
      <div v-else>
        <div class="row mb-3">
          <div class="col-md-6">
            <h4>All Chapters ({{ chapters.length }})</h4>
          </div>
          <div class="col-md-6 text-end">
            <a href="#/add_chapter" class="btn btn-primary">Add New Chapter</a>
          </div>
        </div>

        <div v-if="chapters.length === 0" class="alert alert-info">
          No chapters found. <a href="#/add_chapter">Create your first chapter</a>
        </div>

        <div v-else class="row">
          <div v-for="chapter in chapters" :key="chapter.id" class="col-md-6 mb-3">
            <div class="card">
              <div class="card-body">
                <h5 class="card-title">{{ chapter.name }}</h5>
                <p class="card-text">{{ chapter.description || 'No description' }}</p>
                <p class="card-text">
                  <small class="text-muted">
                    Subject: {{ getSubjectName(chapter.subject_id) }}
                  </small>
                </p>
                <div class="d-flex justify-content-between align-items-center">
                  <small class="text-muted">
                    Created: {{ formatDate(chapter.created_at) }}
                  </small>
                  <div class="btn-group" role="group">
                    <a :href="'#/edit_chapter/' + chapter.id" class="btn btn-sm btn-outline-primary">Edit</a>
                    <a :href="'#/create_quiz/' + chapter.id" class="btn btn-sm btn-success">Add Quiz</a>
                    <button @click="deleteChapter(chapter.id)" class="btn btn-sm btn-outline-danger">Delete</button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="mt-3">
        <a href="#/admin_dashboard" class="btn btn-secondary">Back to Dashboard</a>
      </div>
    </div>
  `,
  data() {
    return {
      chapters: [],
      subjects: [],
      loading: true
    };
  },
  created() {
    this.fetchChapters();
    this.fetchSubjects();
  },
  methods: {
    fetchChapters() {
      const adminToken = localStorage.getItem('admin_token');
      if (!adminToken) {
        this.$router.push('/login');
        return;
      }
      
      this.$http.get('/api/v2/admin/chapters', {
        headers: { 'Authorization': `Bearer ${adminToken}` }
      }).then(response => {
        if (response.data.status === 'success') {
          this.chapters = response.data.chapters;
        }
        this.loading = false;
      }).catch(error => {
        console.error('Error fetching chapters:', error);
        this.loading = false;
      });
    },
    fetchSubjects() {
      const adminToken = localStorage.getItem('admin_token');
      if (!adminToken) {
        this.$router.push('/login');
        return;
      }
      
      this.$http.get('/api/v2/admin/subjects', {
        headers: { 'Authorization': `Bearer ${adminToken}` }
      }).then(response => {
        if (response.data.status === 'success') {
          this.subjects = response.data.subjects;
        }
      }).catch(error => {
        console.error('Error fetching subjects:', error);
      });
    },
    getSubjectName(subjectId) {
      const subject = this.subjects.find(s => s.id === subjectId);
      return subject ? subject.name : 'Unknown Subject';
    },
    deleteChapter(chapterId) {
      if (!confirm('Are you sure you want to delete this chapter? This will also delete all associated quizzes.')) {
        return;
      }
      
      const adminToken = localStorage.getItem('admin_token');
      if (!adminToken) {
        this.$router.push('/login');
        return;
      }
      
      this.$http.delete(`/api/v2/admin/chapters/${chapterId}`, {
        headers: { 'Authorization': `Bearer ${adminToken}` }
      }).then(response => {
        if (response.data.status === 'success') {
          alert('Chapter deleted successfully!');
          this.fetchChapters(); // Refresh the list
        } else {
          alert('Error: ' + response.data.message);
        }
      }).catch(error => {
        console.error('Error deleting chapter:', error);
        alert('Error deleting chapter. Please try again.');
      });
    },
    formatDate(dateString) {
      if (!dateString) return 'N/A';
      const date = new Date(dateString);
      return date.toLocaleDateString();
    }
  }
};

const ViewQuizzesComponent = {
  template: `
    <div class="container">
      <h2 class="mb-4">Manage Quizzes</h2>
      
      <!-- Loading Spinner -->
      <div v-if="loading" class="text-center">
        <div class="spinner-border" role="status">
          <span class="visually-hidden">Loading...</span>
        </div>
      </div>

      <!-- Quizzes List -->
      <div v-else>
        <div class="row mb-3">
          <div class="col-md-6">
            <h4>All Quizzes ({{ quizzes.length }})</h4>
          </div>
          <div class="col-md-6 text-end">
            <a href="#/create_quiz" class="btn btn-primary">Add New Quiz</a>
          </div>
        </div>

        <div v-if="quizzes.length === 0" class="alert alert-info">
          No quizzes found. <a href="#/create_quiz">Create your first quiz</a>
        </div>

        <div v-else class="row">
          <div v-for="quiz in quizzes" :key="quiz.id" class="col-md-6 mb-3">
            <div class="card">
              <div class="card-body">
                <h5 class="card-title">Quiz #{{ quiz.id }}</h5>
                <p class="card-text">
                  <strong>Date:</strong> {{ formatDate(quiz.date_of_quiz) }}<br>
                  <strong>Duration:</strong> {{ quiz.time_duration }}<br>
                  <strong>Chapter:</strong> {{ getChapterName(quiz.chapter_id) }}
                </p>
                <p class="card-text">{{ quiz.remarks || 'No remarks' }}</p>
                <div class="d-flex justify-content-between align-items-center">
                  <small class="text-muted">
                    Created: {{ formatDate(quiz.created_at) }}
                  </small>
                  <div class="btn-group" role="group">
                    <a :href="'#/edit_quiz/' + quiz.id" class="btn btn-sm btn-outline-primary">Edit</a>
                    <a :href="'#/add_question/' + quiz.id" class="btn btn-sm btn-success">Add Question</a>
                    <button @click="deleteQuiz(quiz.id)" class="btn btn-sm btn-outline-danger">Delete</button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="mt-3">
        <a href="#/admin_dashboard" class="btn btn-secondary">Back to Dashboard</a>
      </div>
    </div>
  `,
  data() {
    return {
      quizzes: [],
      chapters: [],
      loading: true
    };
  },
  created() {
    this.fetchQuizzes();
    this.fetchChapters();
  },
  methods: {
    fetchQuizzes() {
      const adminToken = localStorage.getItem('admin_token');
      if (!adminToken) {
        this.$router.push('/login');
        return;
      }
      
      this.$http.get('/api/v2/admin/quizzes', {
        headers: { 'Authorization': `Bearer ${adminToken}` }
      }).then(response => {
        if (response.data.status === 'success') {
          this.quizzes = response.data.quizzes;
        }
        this.loading = false;
      }).catch(error => {
        console.error('Error fetching quizzes:', error);
        this.loading = false;
      });
    },
    fetchChapters() {
      const adminToken = localStorage.getItem('admin_token');
      if (!adminToken) {
        this.$router.push('/login');
        return;
      }
      
      this.$http.get('/api/v2/admin/chapters', {
        headers: { 'Authorization': `Bearer ${adminToken}` }
      }).then(response => {
        if (response.data.status === 'success') {
          this.chapters = response.data.chapters;
        }
      }).catch(error => {
        console.error('Error fetching chapters:', error);
      });
    },
    getChapterName(chapterId) {
      const chapter = this.chapters.find(c => c.id === chapterId);
      return chapter ? chapter.name : 'Unknown Chapter';
    },
    deleteQuiz(quizId) {
      if (!confirm('Are you sure you want to delete this quiz? This will also delete all associated questions and scores.')) {
        return;
      }
      
      const adminToken = localStorage.getItem('admin_token');
      if (!adminToken) {
        this.$router.push('/login');
        return;
      }
      
      this.$http.delete(`/api/v2/admin/quizzes/${quizId}`, {
        headers: { 'Authorization': `Bearer ${adminToken}` }
      }).then(response => {
        if (response.data.status === 'success') {
          alert('Quiz deleted successfully!');
          this.fetchQuizzes(); // Refresh the list
        } else {
          alert('Error: ' + response.data.message);
        }
      }).catch(error => {
        console.error('Error deleting quiz:', error);
        alert('Error deleting quiz. Please try again.');
      });
    },
    formatDate(dateString) {
      if (!dateString) return 'N/A';
      const date = new Date(dateString);
      return date.toLocaleDateString();
    }
  }
};

const EditQuestionComponent = {
  template: `
    <div class="container">
      <h1>Quiz Master</h1>
      <nav class="navbar navbar-light bg-light">
        <a class="navbar-brand">Edit Question</a>
        <a href="#/logout" class="btn btn-outline-danger">Logout</a>
        <button @click="toggleDarkMode" class="btn btn-secondary">Dark Mode</button>
      </nav>
      <h2>Edit Question</h2>
      <form @submit.prevent="editQuestion" class="needs-validation" novalidate>
        <div class="mb-3">
          <label for="question" class="form-label">Question</label>
          <textarea v-model="question" class="form-control" id="question" required></textarea>
          <div class="invalid-feedback">Please enter a question.</div>
        </div>
        <div class="mb-3">
          <label for="option1" class="form-label">Option 1</label>
          <input v-model="option1" type="text" class="form-control" id="option1" required>
        </div>
        <div class="mb-3">
          <label for="option2" class="form-label">Option 2</label>
          <input v-model="option2" type="text" class="form-control" id="option2" required>
        </div>
        <div class="mb-3">
          <label for="option3" class="form-label">Option 3</label>
          <input v-model="option3" type="text" class="form-control" id="option3" required>
        </div>
        <div class="mb-3">
          <label for="option4" class="form-label">Option 4</label>
          <input v-model="option4" type="text" class="form-control" id="option4" required>
        </div>
        <div class="mb-3">
          <label for="correct_option" class="form-label">Correct Option (1-4)</label>
          <select v-model="correct_option" class="form-control" id="correct_option" required>
            <option value="">Select correct option</option>
            <option value="1">Option 1</option>
            <option value="2">Option 2</option>
            <option value="3">Option 3</option>
            <option value="4">Option 4</option>
          </select>
        </div>
        <button type="submit" class="btn btn-primary">Save Changes</button>
      </form>
      <a href="#/admin_dashboard" class="btn btn-secondary">Back to Dashboard</a>
    </div>
  `,
  data() {
    return {
      questionId: this.$route.params.questionId,
      question: '',
      option1: '',
      option2: '',
      option3: '',
      option4: '',
      correct_option: ''
    };
  },
  mounted() {
    const adminToken = localStorage.getItem('admin_token');
    if (!adminToken) {
      alert('Please login as admin first');
      this.$router.push('/login');
      return;
    }
    
    this.$http.get(`/api/v2/admin/questions/${this.questionId}`, 
      { headers: { 'Authorization': `Bearer ${adminToken}` } }
    ).then(response => {
      if (response.data.status === 'success') {
        const questionData = response.data.question;
        this.question = questionData.question_statement;
        this.option1 = questionData.option1;
        this.option2 = questionData.option2;
        this.option3 = questionData.option3;
        this.option4 = questionData.option4;
        this.correct_option = questionData.correct_option.toString();
      }
    }).catch(error => {
      console.error('Error loading question:', error);
      alert('Error loading question data.');
    });
  },
  methods: {
    editQuestion() {
      const form = document.querySelector('.needs-validation');
      if (!form.checkValidity()) {
        form.classList.add('was-validated');
        return;
      }
      
      const adminToken = localStorage.getItem('admin_token');
      if (!adminToken) {
        alert('Please login as admin first');
        this.$router.push('/login');
        return;
      }
      
      this.$http.put(`/api/v2/admin/questions/${this.questionId}`, 
        { 
          question_statement: this.question,
          option1: this.option1,
          option2: this.option2,
          option3: this.option3,
          option4: this.option4,
          correct_option: parseInt(this.correct_option)
        },
        { headers: { 'Authorization': `Bearer ${adminToken}` } }
      ).then(response => {
        if (response.data.status === 'success') {
          alert('Question updated successfully!');
          this.$router.push('/admin_dashboard');
        } else {
          alert('Error: ' + response.data.message);
        }
      }).catch(error => {
        console.error('Error updating question:', error);
        alert('Error updating question. Please try again.');
      });
    },
    toggleDarkMode() {
      document.body.classList.toggle('bg-dark');
    }
  }
};

// Define routes with component references
const routes = [
  { path: '/', component: IndexComponent },
  { path: '/login', component: AuthComponent.Login },
  { path: '/register', component: AuthComponent.Register },
  { path: '/user_dashboard', component: UserDashboardComponent },
  { path: '/admin_dashboard', component: DashboardComponent.AdminDashboard },
  { path: '/attempt_quiz/:quizId', component: AttemptQuizComponent },
  { path: '/chapter_quizzes/:chapterId', component: ChapterQuizzesComponent },
  { path: '/chapters/:subjectId', component: ChaptersComponent },
  { path: '/create_quiz/:chapterId', component: CreateQuizComponent },
  { path: '/quiz_history', component: QuizHistoryComponent },
  { path: '/quiz_questions/:quizId', component: QuizQuestionsComponent },
  { path: '/view_answers/:quizId', component: ViewAnswersComponent },
  { path: '/search_results', component: SearchResultsComponent },
  { path: '/add_question/:quizId', component: AddQuestionComponent },
  { path: '/add_chapter/:subjectId', component: AddChapterComponent },
  { path: '/add_subject', component: AddSubjectComponent },
  { path: '/edit_chapter/:chapterId', component: EditChapterComponent },
  { path: '/edit_quiz/:quizId', component: EditQuizComponent },
  { path: '/edit_question/:questionId', component: EditQuestionComponent },
  { path: '/edit_subject/:subjectId', component: EditSubjectComponent },
  { path: '/view_quiz/:quizId', component: ViewQuizComponent },
  { path: '/view_quiz_users/:quizId', component: ViewQuizUsersComponent },
  { path: '/view_subject/:subjectId', component: ViewSubjectComponent },
  { path: '/view_user/:userId', component: ViewUserComponent },
  { path: '/view_subjects', component: ViewSubjectsComponent },
  { path: '/view_chapters', component: ViewChaptersComponent },
  { path: '/view_quizzes', component: ViewQuizzesComponent }
];

// Create and mount the router with hash mode to avoid server navigation issues
const router = new VueRouter({ 
  routes,
  mode: 'hash' 
});

// Add debug logging for router navigation
router.beforeEach((to, from, next) => {
  console.log(`Navigating from ${from.path} to ${to.path}`);
  next();
});

// Create the Vue instance with router
const app = new Vue({
  el: '#app',
  router,
  data: {
    isLoggedIn: false,
    isAdmin: false
  },
  created() {
    console.log("Vue app initialized");
    
    // Check login status
    this.checkAuth();
  },
  methods: {
    checkAuth() {
      console.log("Checking authentication status...");
      
      // Check for admin token first
      const adminToken = localStorage.getItem('admin_token');
      if (adminToken) {
        this.$http.get('/api/v2/auth/verify-token', {
          headers: { 'Authorization': `Bearer ${adminToken}` }
        }).then(response => {
          console.log("Admin auth check response:", response.data);
          if (response.data.status === 'success') {
            this.isLoggedIn = true;
            this.isAdmin = true;
            this.updateUI();
          } else {
            throw new Error('Invalid admin token');
          }
        }).catch(error => {
          console.log("Admin auth check error:", error);
          localStorage.removeItem('admin_token');
          localStorage.removeItem('admin_user');
          this.isLoggedIn = false;
          this.isAdmin = false;
          this.updateUI();
          this.checkUserAuth();
        });
      } else {
        this.checkUserAuth();
      }
    },
    
    checkUserAuth() {
      // Check for user token
      const userToken = localStorage.getItem('user_token');
      if (userToken) {
        this.$http.get('/api/v2/auth/verify-token', {
          headers: { 'Authorization': `Bearer ${userToken}` }
        }).then(response => {
          console.log("User auth check response:", response.data);
          if (response.data.status === 'success') {
            this.isLoggedIn = true;
            this.isAdmin = false;
            this.updateUI();
          } else {
            throw new Error('Invalid user token');
          }
        }).catch(error => {
          console.log("User auth check error:", error);
          localStorage.removeItem('user_token');
          localStorage.removeItem('user_data');
          this.isLoggedIn = false;
          this.isAdmin = false;
          this.updateUI();
        });
      } else {
        this.isLoggedIn = false;
        this.isAdmin = false;
        this.updateUI();
      }
    },
    updateUI() {
      // Update navbar based on authentication status
      const navbarNav = document.getElementById('navbarNav');
      if (navbarNav) {
        const navList = navbarNav.querySelector('ul');
        if (navList) {
          if (this.isLoggedIn) {
            if (this.isAdmin) {
              navList.innerHTML = `
                <li class="nav-item">
                  <a class="nav-link" href="#/">Home</a>
                </li>
                <li class="nav-item">
                  <a class="nav-link" href="#/admin_dashboard">Admin Dashboard</a>
                </li>
                <li class="nav-item">
                  <a class="nav-link" href="#/logout" @click.prevent="logout">Logout</a>
                </li>
              `;
            } else {
              navList.innerHTML = `
                <li class="nav-item">
                  <a class="nav-link" href="#/">Home</a>
                </li>
                <li class="nav-item">
                  <a class="nav-link" href="#/user_dashboard">Dashboard</a>
                </li>
                <li class="nav-item">
                  <a class="nav-link" href="#/quiz_history">Quiz History</a>
                </li>
                <li class="nav-item">
                  <a class="nav-link" href="#/logout" @click.prevent="logout">Logout</a>
                </li>
              `;
            }
          } else {
            navList.innerHTML = `
              <li class="nav-item">
                <a class="nav-link" href="#/">Home</a>
              </li>
              <li class="nav-item">
                <a class="nav-link" href="#/login">Login</a>
              </li>
              <li class="nav-item">
                <a class="nav-link" href="#/register">Register</a>
              </li>
            `;
          }
        }
      }
    },
    logout() {
      localStorage.removeItem('admin_token');
      localStorage.removeItem('admin_user');
      localStorage.removeItem('user_token');
      localStorage.removeItem('user_data');
      this.isLoggedIn = false;
      this.isAdmin = false;
      this.updateUI();
      this.$router.push('/');
    }
  }
});
