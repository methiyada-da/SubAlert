(() => {
    const password = document.querySelector('.login-card input[name="password"]');
    const toggle = document.querySelector('.login-password-toggle');
    if (!password || !toggle) return;

    toggle.hidden = false;
    toggle.addEventListener('click', () => {
        const visible = password.type === 'password';
        password.type = visible ? 'text' : 'password';
        toggle.setAttribute('aria-pressed', String(visible));
        toggle.setAttribute('aria-label', visible ? 'ซ่อนรหัสผ่าน' : 'แสดงรหัสผ่าน');
        password.focus();
    });
})();
