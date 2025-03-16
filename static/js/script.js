// Login and signup page toggle
document.getElementById('signupLink').addEventListener('click', function(event) {
    event.preventDefault();
    document.getElementById('loginPage').classList.add('hidden');
    document.getElementById('signupPage').classList.remove('hidden');
  });

  // Login form submission
  document.getElementById('loginForm').addEventListener('submit', function(event) {
    event.preventDefault();
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;

    // Add login logic here
    console.log('Login - Email:', email);
    console.log('Login - Password:', password);

    alert('Login successful!');
  });

  // Signup form submission
  document.getElementById('signupForm').addEventListener('submit', function(event) {
    event.preventDefault();
    const email = document.getElementById('signupEmail').value;
    const password = document.getElementById('signupPassword').value;

    // Add signup logic here
    console.log('Signup - Email:', email);
    console.log('Signup - Password:', password);

    alert('Signup successful!');
  });