document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("registrationForm");
    const messageBox = document.getElementById("registrationValidationMessage");

    if (!form || !messageBox) {
        return;
    }

    const showMessage = (message, target) => {
        messageBox.textContent = message;
        messageBox.hidden = false;
        messageBox.classList.add("is-visible");

        if (target) {
            target.classList.add("field-error");
            target.scrollIntoView({ behavior: "smooth", block: "center" });
            target.focus({ preventScroll: true });
        }
    };

    const clearErrors = () => {
        messageBox.textContent = "";
        messageBox.hidden = true;
        messageBox.classList.remove("is-visible");
        form.querySelectorAll(".field-error").forEach((element) => {
            element.classList.remove("field-error");
        });
    };

    form.addEventListener("submit", (event) => {
        clearErrors();

        const nombrePadre = form.querySelector("#nombre_padre");
        const nombreMadre = form.querySelector("#nombre_madre");

        if (!nombrePadre.value.trim()) {
            event.preventDefault();
            showMessage("Campo obligatorio. En caso de omitir, colocar '-'.", nombrePadre);
            return;
        }

        if (!nombreMadre.value.trim()) {
            event.preventDefault();
            showMessage("Campo obligatorio. En caso de omitir, colocar '-'.", nombreMadre);
        }
    });
});
