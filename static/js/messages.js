document.addEventListener("DOMContentLoaded", () => {
    const dismissDelay = 5000;

    document.querySelectorAll(".message[data-auto-dismiss]").forEach((message) => {
        let dismissTimer;
        let removed = false;

        const removeMessage = () => {
            if (removed) return;
            removed = true;
            message.classList.add("is-hiding");

            window.setTimeout(() => {
                const container = message.parentElement;
                message.remove();
                if (container && !container.children.length) {
                    container.remove();
                }
            }, 260);
        };

        const startTimer = () => {
            window.clearTimeout(dismissTimer);
            dismissTimer = window.setTimeout(removeMessage, dismissDelay);
        };

        const pauseTimer = () => window.clearTimeout(dismissTimer);

        message.querySelector(".message-close")?.addEventListener("click", removeMessage);
        message.addEventListener("mouseenter", pauseTimer);
        message.addEventListener("mouseleave", startTimer);
        message.addEventListener("focusin", pauseTimer);
        message.addEventListener("focusout", startTimer);
        startTimer();
    });
});
