(() => {
    const form = document.querySelector('.profile-form');
    if (!form) return;

    const username = form.elements.namedItem('username');
    const email = form.elements.namedItem('email');
    const status = form.querySelector('.profile-save-status');
    if (!username || !email || !status) return;

    const update = () => {
        const changed = username.value !== form.dataset.savedUsername || email.value !== form.dataset.savedEmail;
        status.hidden = !changed;
    };

    username.addEventListener('input', update);
    email.addEventListener('input', update);
    update();

    const sectionLinks = Array.from(document.querySelectorAll('.profile-section-nav a'));
    const syncSection = () => {
        const current = window.location.hash || '#profile-details';
        sectionLinks.forEach((link) => link.classList.toggle('is-current', link.getAttribute('href') === current));
    };
    window.addEventListener('hashchange', syncSection);
    syncSection();
})();
