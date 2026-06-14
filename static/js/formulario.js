document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("evaluationForm");
    const messageBox = document.getElementById("formValidationMessage");

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
            if (typeof target.focus === "function") {
                target.focus({ preventScroll: true });
            }
        } else {
            messageBox.scrollIntoView({ behavior: "smooth", block: "center" });
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

    const findFirstUnansweredQuestion = () => {
        for (let index = 1; index <= 40; index += 1) {
            const answered = form.querySelector(`input[name="Q${index}"]:checked`);
            if (!answered) {
                return form.querySelector(`input[name="Q${index}"]`)?.closest("[data-question-card]");
            }
        }
        return null;
    };

    form.addEventListener("submit", (event) => {
        clearErrors();

        const sexo = form.querySelector("#sexo");
        const edad = form.querySelector("#edad");
        const edadValue = Number(edad.value);

        if (!sexo.value) {
            event.preventDefault();
            showMessage("Por favor, seleccione el g\u00e9nero del paciente.", sexo);
            return;
        }

        if (!edad.value || !Number.isInteger(edadValue) || edadValue < 4 || edadValue > 12) {
            event.preventDefault();
            showMessage("Ingrese una edad v\u00e1lida para continuar.", edad);
            return;
        }

        const unansweredQuestion = findFirstUnansweredQuestion();
        if (unansweredQuestion) {
            event.preventDefault();
            showMessage("Debe responder todas las preguntas antes de continuar.", unansweredQuestion);
        }
    });
});
