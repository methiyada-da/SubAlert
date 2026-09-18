document.addEventListener("DOMContentLoaded", () => {
    const sidebar = document.querySelector("#app-sidebar");
    const toggle = document.querySelector("#sidebar-toggle");
    const backdrop = document.querySelector("#sidebar-backdrop");
    const notificationToggle = document.querySelector("#notification-toggle");
    const notificationPopover = document.querySelector("#notification-popover");
    if (!sidebar || !toggle || !backdrop) return;

    function setSidebar(open) {
        sidebar.classList.toggle("open", open);
        backdrop.hidden = !open;
        toggle.setAttribute("aria-expanded", String(open));
        document.body.classList.toggle("sidebar-open", open);
    }

    function setNotifications(open) {
        if (!notificationToggle || !notificationPopover) return;
        notificationPopover.hidden = !open;
        notificationToggle.setAttribute("aria-expanded", String(open));
    }

    toggle.addEventListener("click", () => setSidebar(!sidebar.classList.contains("open")));
    backdrop.addEventListener("click", () => setSidebar(false));
    sidebar.querySelectorAll("a").forEach((link) => link.addEventListener("click", () => setSidebar(false)));
    notificationToggle?.addEventListener("click", (event) => {
        event.stopPropagation();
        setNotifications(notificationPopover.hidden);
    });
    notificationPopover?.addEventListener("click", (event) => event.stopPropagation());
    document.addEventListener("click", () => setNotifications(false));
    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape") {
            setSidebar(false);
            setNotifications(false);
        }
    });
});
