// static/js/resultado.js

document.addEventListener("DOMContentLoaded", () => {
    // Datos que vienen desde el <body> en resultado.html
    const nivel = document.body.dataset.nivel || "";
    const scorePct = parseFloat(document.body.dataset.scorepct || "0");

    const card = document.querySelector(".card-resultado");
    const bar = document.getElementById("scoreBar");
    const fill = document.getElementById("scoreFill");
    const marker = document.getElementById("scoreMarker");

    // ---------------------------
    // 1) Animación de la tarjeta
    // ---------------------------
    if (card) {
        card.style.opacity = 0;
        card.style.transform = "translateY(10px)";
        setTimeout(() => {
            card.style.transition = "all 0.5s ease";
            card.style.opacity = 1;
            card.style.transform = "translateY(0)";
        }, 100);
    }

    // ---------------------------
    // 2) Color según NIVEL
    // ---------------------------
    let color = "#3b82f6"; // azul por defecto

    const nivelLower = nivel.toLowerCase();

    if (nivelLower.includes("sin")) {
        color = "#22c55e";          // verde
    } else if (nivelLower.includes("leve")) {
        color = "#eab308";          // amarillo
    } else if (nivelLower.includes("moderado")) {
        color = "#f97316";          // naranja
    } else if (nivelLower.includes("severo")) {
        color = "#ef4444";          // rojo
    }

    // ---------------------------
    // 3) Relleno de la barra
    // ---------------------------
    if (fill && !isNaN(scorePct)) {
        // color de la barra
        fill.style.backgroundColor = color;

        // animación del ancho (de 0% al porcentaje real)
        fill.style.width = "0%";
        setTimeout(() => {
            fill.style.transition = "width 0.8s ease";
            fill.style.width = `${scorePct}%`;  // ej. 45%
        }, 200);
    }

    // ---------------------------
    // 4) Marcador (por si quieres animarlo también)
    // ---------------------------
    if (marker && !isNaN(scorePct)) {
        // En el HTML ya se coloca en la posición correcta con Jinja,
        // pero si quieres que "viaje" desde 0 hasta su posición:
        const finalLeft = marker.style.left || `${scorePct}%`;

        // lo llevamos visualmente desde 0 hasta el valor real
        marker.style.left = "0%";
        setTimeout(() => {
            marker.style.transition = "left 0.8s ease";
            marker.style.left = finalLeft;
        }, 200);
    }
});
