// 切换登录和注册页面
document.getElementById('signupLink').addEventListener('click', function(event) {
    event.preventDefault();
    document.getElementById('loginPage').classList.add('hidden');
    document.getElementById('signupPage').classList.remove('hidden');
});

// 登录表单提交
document.getElementById('loginForm').addEventListener('submit', function(event) {
    event.preventDefault();
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;

    // 这里可以添加登录逻辑
    console.log('Login - Email:', email);
    console.log('Login - Password:', password);

    alert('Login successful!');
});

// 注册表单提交
document.getElementById('signupForm').addEventListener('submit', function(event) {
    event.preventDefault();
    const email = document.getElementById('signupEmail').value;
    const password = document.getElementById('signupPassword').value;

    // 这里可以添加注册逻辑
    console.log('Signup - Email:', email);
    console.log('Signup - Password:', password);

    alert('Signup successful!');
});