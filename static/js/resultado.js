document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll(".fade-in-up").forEach((element, index) => {
        window.setTimeout(() => {
            element.classList.add("is-visible");
        }, 90 + index * 80);
    });

    const nivel = (document.body.dataset.nivel || "").toLowerCase();
    const scorePct = Number.parseFloat(document.body.dataset.scorepct || "0");

    const card = document.querySelector(".card-resultado");
    const fill = document.getElementById("scoreFill");
    const marker = document.getElementById("scoreMarker");
    const badge = document.getElementById("scoreBadge");

    if (!card || Number.isNaN(scorePct)) {
        return;
    }

    let accent = "#2f6c67";
    let accentSoft = "rgba(47, 108, 103, 0.14)";

    if (nivel.includes("leve")) {
        accent = "#c98a1a";
        accentSoft = "rgba(201, 138, 26, 0.16)";
    } else if (nivel.includes("moderado")) {
        accent = "#c96c4a";
        accentSoft = "rgba(201, 108, 74, 0.16)";
    } else if (nivel.includes("severo") || nivel.includes("alto")) {
        accent = "#d35745";
        accentSoft = "rgba(211, 87, 69, 0.16)";
    } else if (nivel.includes("sin") || nivel.includes("bajo")) {
        accent = "#2e7d5b";
        accentSoft = "rgba(46, 125, 91, 0.16)";
    }

    card.style.borderColor = accentSoft;

    if (badge) {
        badge.style.background = accentSoft;
        badge.style.color = accent;
    }

    if (fill) {
        fill.style.width = "0%";
        fill.style.background = `linear-gradient(90deg, ${accentSoft}, ${accent})`;

        window.setTimeout(() => {
            fill.style.transition = "width 0.9s ease";
            fill.style.width = `${Math.max(0, Math.min(scorePct, 100))}%`;
        }, 160);
    }

    if (marker) {
        const finalLeft = marker.style.left || `${scorePct}%`;
        marker.style.left = "0%";

        window.setTimeout(() => {
            marker.style.transition = "left 0.9s ease";
            marker.style.left = finalLeft;
        }, 160);
    }
});
