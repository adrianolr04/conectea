import json
import os
from datetime import datetime
from functools import wraps

import psycopg2
from fpdf import FPDF
from flask import (
    Flask,
    flash,
    make_response,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from psycopg2.extras import RealDictCursor
from werkzeug.security import check_password_hash, generate_password_hash

from miterap_model import MiterapModel


app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev_secret_key")

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "CONECTEA")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "adriano13")
DB_PORT = int(os.getenv("DB_PORT", 5432))

DEFAULT_ADMIN_NAME = os.getenv("ADMIN_NAME", "Administrador")
DEFAULT_ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@conectea.local")
DEFAULT_ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

SCHEMA_READY = False

modelo = MiterapModel(artifacts_dir="artifacts")

QUESTION_ITEMS = [
    {"number": 1, "text": "¿Es capaz de hablar usando frases u oraciones cortas?", "example": "Ejemplo: dice 'quiero agua' o 'vamos al parque' usando frases breves, no solo palabras sueltas."},
    {"number": 2, "text": "¿Tiene conversaciones con él o con ella, en la que participen ambos y se vayan turnando o vayan construyendo sobre lo ya dicho?", "example": "Ejemplo: usted pregunta algo, responde y luego continúa el intercambio sin cortar la conversación."},
    {"number": 3, "text": "¿Usa algunas veces frases raras o dice la misma cosa una y otra vez y casi exactamente de la misma manera ya sean frases que ha oído a otras personas o frases que se inventa?", "example": "Ejemplo: repite una frase de un video o programa muchas veces aunque no encaje con la situación."},
    {"number": 4, "text": "¿Hace en ocasiones preguntas o afirmaciones socialmente inconvenientes, tales como preguntas indiscretas o comentarios personales en momentos inoportunos?", "example": "Ejemplo: hace comentarios muy personales en público sin notar que pueden incomodar."},
    {"number": 5, "text": "¿Confunde a veces los pronombres diciendo, por ejemplo 'tú' o 'ella' en lugar de 'yo'?", "example": "Ejemplo: dice 'tú quieres agua' cuando en realidad habla de sí mismo."},
    {"number": 6, "text": "¿Usa alguna vez palabras que ha inventado, expresa algunas cosas de una manera rara o indirecta o usa formas metafóricas para referirse a las cosas, como por ejemplo, decir 'lluvia caliente' en lugar de 'vapor'?", "example": "Ejemplo: nombra objetos con palabras inventadas o descripciones poco habituales que solo algunos entienden."},
    {"number": 7, "text": "¿Dice en ocasiones la misma cosa una y otra vez y exactamente de la misma manera o insiste para que usted diga las mismas cosas una y otra vez?", "example": "Ejemplo: pide repetir la misma frase exacta varias veces seguidas."},
    {"number": 8, "text": "¿Insiste alguna vez en hacer ciertas cosas de una manera o en un orden muy particular o hay determinados 'rituales' que pretende que usted respete?", "example": "Ejemplo: se altera si cambian el orden de su rutina o si un objeto no está donde espera."},
    {"number": 9, "text": "¿Piensa usted que por lo general su expresión facial se puede considerar adecuada a la situación del momento?", "example": "Ejemplo: muestra alegría, tristeza o sorpresa de forma acorde con lo que está pasando."},
    {"number": 10, "text": "¿Usa alguna vez la mano de usted como una herramienta o como si fuera parte de su propio cuerpo, por ejemplo, apuntando con su dedo o poniendo la mano de usted en el tirador de la puerta para lograr que la abriese?", "example": "Ejemplo: toma su mano y la coloca sobre algo para que usted haga la acción por él."},
    {"number": 11, "text": "¿Muestra alguna vez interés por ciertas cosas que le preocupan mucho y que a otras personas les parecen extrañas, por ejemplo, semáforos, tuberías de desagüe u horarios de transporte?", "example": "Ejemplo: pasa mucho tiempo pendiente de un tema muy específico poco común para su edad."},
    {"number": 12, "text": "¿Se interesa algunas veces más en las piezas de un juguete o de un objeto, por ejemplo dar vueltas a las ruedas de un coche, que en usar el objeto de acuerdo a su finalidad?", "example": "Ejemplo: gira las ruedas del carro repetidamente en vez de jugar con el carro completo."},
    {"number": 13, "text": "¿Muestra un interés especial por algún tema, por ejemplo trenes o dinosaurios, que aun siendo normal a su edad y en su ambiente, parece fuera de lo normal por su intensidad?", "example": "Ejemplo: habla del mismo tema con gran detalle y mucha frecuencia durante el día."},
    {"number": 14, "text": "¿Muestra a veces interés excepcional por la vista, el tacto, el sonido, el sabor o el olor de las cosas o las personas?", "example": "Ejemplo: busca, evita o reacciona mucho ante texturas, sonidos, luces u olores."},
    {"number": 15, "text": "¿Realiza en ocasiones gestos o movimientos extraños con las manos o los dedos, como agitar o mover sus dedos delante de sus ojos?", "example": "Ejemplo: mueve las manos frente a la cara o mira sus dedos mientras los agita."},
    {"number": 16, "text": "¿Realiza en ocasiones movimientos complicados de su cuerpo, como dar vueltas, retorcerse o dar saltos repetidos en el sitio?", "example": "Ejemplo: gira sobre sí mismo o salta muchas veces seguidas sin una actividad concreta."},
    {"number": 17, "text": "¿Se hace daño a propósito alguna vez, por ejemplo, mordiéndose un brazo o golpeándose la cabeza?", "example": "Ejemplo: cuando se frustra, se muerde, se golpea o se lastima de manera intencional."},
    {"number": 18, "text": "¿Tiene algún objeto que necesita llevar consigo, aparte de un muñeco o una manta?", "example": "Ejemplo: insiste en llevar siempre una tapa, cuerda, piedra u otro objeto específico."},
    {"number": 19, "text": "¿Tiene un amigo íntimo o alguna amistad en particular?", "example": "Ejemplo: busca con frecuencia a un niño específico para jugar o compartir."},
    {"number": 20, "text": "¿Habla con usted alguna vez solo para ser simpático y amable y no para conseguir algo?", "example": "Ejemplo: se acerca a conversar o contar algo sin pedir ayuda ni objetos."},
    {"number": 21, "text": "¿Imita alguna vez espontáneamente a otras personas o lo que hacen, como pasar la aspiradora, cocinar o arreglar cosas?", "example": "Ejemplo: copia actividades de los adultos por iniciativa propia durante el juego."},
    {"number": 22, "text": "¿Señala alguna vez espontáneamente las cosas que ve solo para mostrárselas a usted y no porque quiera obtenerlas?", "example": "Ejemplo: apunta a un avión o un perro solo para compartir lo que vio."},
    {"number": 23, "text": "¿Hace alguna vez gestos para indicarle lo que quiere, aparte de señalar el objeto o tirarle a usted de la mano?", "example": "Ejemplo: hace señas con la mano para pedir ayuda, acercarse o cargarlo."},
    {"number": 24, "text": "¿Asiente con la cabeza para decir sí?", "example": "Ejemplo: mueve la cabeza afirmativamente cuando acepta algo."},
    {"number": 25, "text": "¿Niega con la cabeza para decir no?", "example": "Ejemplo: mueve la cabeza de lado a lado para rechazar comida, juego o ayuda."},
    {"number": 26, "text": "Al hablarle o hacer algo con usted, ¿suele mirarle directamente a la cara?", "example": "Ejemplo: mientras interactúan, suele buscar su rostro o sus ojos por algunos instantes."},
    {"number": 27, "text": "¿Devuelve la sonrisa cuando alguien le sonríe?", "example": "Ejemplo: si usted le sonríe, normalmente responde sonriendo también."},
    {"number": 28, "text": "¿Le muestra a usted cosas que le interesan a fin de captar su atención?", "example": "Ejemplo: le enseña un dibujo o un juguete para que usted lo mire con él."},
    {"number": 29, "text": "¿Se ofrece alguna vez a compartir cosas con usted, aparte de alimentos?", "example": "Ejemplo: le ofrece un juguete u objeto que le gusta sin que usted se lo pida."},
    {"number": 30, "text": "En su opinión, ¿quiere alguna vez que usted participe en sus juegos?", "example": "Ejemplo: lo invita a jugar, le da un rol o le acerca juguetes para hacerlo juntos."},
    {"number": 31, "text": "¿Intenta alguna vez consolarle si ve que usted está triste o se ha hecho daño?", "example": "Ejemplo: se acerca, pregunta qué pasó o intenta ayudar cuando lo ve mal."},
    {"number": 32, "text": "Cuando quiere algo o buscaba ayuda, ¿le mira y hace gestos con sonidos o palabras para captar su atención?", "example": "Ejemplo: combina mirada, gesto y voz para pedir ayuda con algo."},
    {"number": 33, "text": "¿Muestra una variedad normal de expresiones faciales?", "example": "Ejemplo: cambia de expresión según esté alegre, molesto, sorprendido o triste."},
    {"number": 34, "text": "¿Alguna vez se une a juegos de grupo y trata de imitar las acciones y juegos sociales que se están haciendo?", "example": "Ejemplo: observa a otros niños jugando y se suma intentando seguir lo que hacen."},
    {"number": 35, "text": "¿Juega a disfrazarse, a simular que es otra persona o a juegos de ficción en general?", "example": "Ejemplo: hace como si cocinara, fuera doctor o interpretara personajes."},
    {"number": 36, "text": "¿Muestra interés por niños de su edad a los que no conoce?", "example": "Ejemplo: mira, se acerca o intenta interactuar con niños nuevos en el parque o colegio."},
    {"number": 37, "text": "¿Responde positivamente cuando se le acerca otro niño?", "example": "Ejemplo: responde al saludo, acepta jugar o continúa la interacción con agrado."},
    {"number": 38, "text": "Si usted entra a un cuarto y empieza a hablarle sin decir su nombre, ¿por lo general levanta la vista y le presta atención?", "example": "Ejemplo: al escuchar su voz, deja un momento lo que hace y mira para atender."},
    {"number": 39, "text": "¿Participa alguna vez con otros niños en juegos de ficción, de tal manera que quede claro que unos y otros comprenden en qué consiste el juego?", "example": "Ejemplo: juega a la casita, a la tienda o a personajes con una idea compartida."},
    {"number": 40, "text": "¿Participaba activamente en juegos que requieren colaborar con otros niños en grupo, como jugar al escondite o a la pelota?", "example": "Ejemplo: toma turnos, sigue reglas simples y coopera con otros niños durante el juego."},
]


def get_connection():
    return psycopg2.connect(
        host=DB_HOST,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        port=DB_PORT,
    )


def ensure_schema():
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS usuarios (
                id SERIAL PRIMARY KEY,
                nombre_completo VARCHAR(150) NOT NULL,
                correo VARCHAR(150) UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                rol VARCHAR(20) NOT NULL CHECK (rol IN ('admin', 'especialista')),
                activo BOOLEAN NOT NULL DEFAULT TRUE,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS especialistas (
                id SERIAL PRIMARY KEY,
                usuario_id INT UNIQUE NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
                especialidad VARCHAR(120),
                numero_colegiatura VARCHAR(80),
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS pacientes (
                id SERIAL PRIMARY KEY,
                codigo VARCHAR(30) UNIQUE,
                nombre_padre VARCHAR(150),
                nombre_madre VARCHAR(150),
                nombre_paciente VARCHAR(150) NOT NULL,
                distrito VARCHAR(120),
                telefono VARCHAR(30),
                correo VARCHAR(150),
                sexo VARCHAR(10),
                edad INT,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS evaluaciones (
                id SERIAL PRIMARY KEY,
                paciente_id INT NOT NULL REFERENCES pacientes(id) ON DELETE CASCADE,
                score NUMERIC(5, 2) NOT NULL,
                score_pct NUMERIC(5, 2) NOT NULL,
                nivel_autismo VARCHAR(80) NOT NULL,
                probabilidades_json TEXT,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS respuestas_evaluacion (
                id SERIAL PRIMARY KEY,
                evaluacion_id INT UNIQUE NOT NULL REFERENCES evaluaciones(id) ON DELETE CASCADE,
                q1 SMALLINT NOT NULL, q2 SMALLINT NOT NULL, q3 SMALLINT NOT NULL, q4 SMALLINT NOT NULL, q5 SMALLINT NOT NULL,
                q6 SMALLINT NOT NULL, q7 SMALLINT NOT NULL, q8 SMALLINT NOT NULL, q9 SMALLINT NOT NULL, q10 SMALLINT NOT NULL,
                q11 SMALLINT NOT NULL, q12 SMALLINT NOT NULL, q13 SMALLINT NOT NULL, q14 SMALLINT NOT NULL, q15 SMALLINT NOT NULL,
                q16 SMALLINT NOT NULL, q17 SMALLINT NOT NULL, q18 SMALLINT NOT NULL, q19 SMALLINT NOT NULL, q20 SMALLINT NOT NULL,
                q21 SMALLINT NOT NULL, q22 SMALLINT NOT NULL, q23 SMALLINT NOT NULL, q24 SMALLINT NOT NULL, q25 SMALLINT NOT NULL,
                q26 SMALLINT NOT NULL, q27 SMALLINT NOT NULL, q28 SMALLINT NOT NULL, q29 SMALLINT NOT NULL, q30 SMALLINT NOT NULL,
                q31 SMALLINT NOT NULL, q32 SMALLINT NOT NULL, q33 SMALLINT NOT NULL, q34 SMALLINT NOT NULL, q35 SMALLINT NOT NULL,
                q36 SMALLINT NOT NULL, q37 SMALLINT NOT NULL, q38 SMALLINT NOT NULL, q39 SMALLINT NOT NULL, q40 SMALLINT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS notas_especialista (
                id SERIAL PRIMARY KEY,
                evaluacion_id INT NOT NULL REFERENCES evaluaciones(id) ON DELETE CASCADE,
                especialista_id INT NOT NULL REFERENCES especialistas(id) ON DELETE CASCADE,
                nota TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_evaluaciones_paciente_id ON evaluaciones(paciente_id);
            CREATE INDEX IF NOT EXISTS idx_pacientes_codigo ON pacientes(codigo);
            CREATE INDEX IF NOT EXISTS idx_usuarios_correo ON usuarios(correo);
            """
        )

        cur.execute("SELECT id FROM usuarios WHERE rol = 'admin' LIMIT 1;")
        admin = cur.fetchone()
        if not admin:
            cur.execute(
                """
                INSERT INTO usuarios (nombre_completo, correo, password_hash, rol)
                VALUES (%s, %s, %s, 'admin');
                """,
                (
                    DEFAULT_ADMIN_NAME,
                    DEFAULT_ADMIN_EMAIL,
                    generate_password_hash(DEFAULT_ADMIN_PASSWORD),
                ),
            )

        conn.commit()
    finally:
        cur.close()
        conn.close()


@app.before_request
def initialize_schema_once():
    global SCHEMA_READY
    if SCHEMA_READY:
        return
    ensure_schema()
    SCHEMA_READY = True


def fetch_one(query, params=None):
    conn = get_connection()
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(query, params or ())
        row = cur.fetchone()
        return dict(row) if row else None
    finally:
        cur.close()
        conn.close()


def fetch_all(query, params=None):
    conn = get_connection()
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(query, params or ())
        rows = cur.fetchall()
        return [dict(row) for row in rows]
    finally:
        cur.close()
        conn.close()


def login_required(*allowed_roles):
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(*args, **kwargs):
            user_role = session.get("user_role")
            if not user_role:
                flash("Debes iniciar sesión para acceder a esta sección.", "error")
                return redirect(url_for("login"))
            if allowed_roles and user_role not in allowed_roles:
                flash("No tienes permisos para acceder a esa vista.", "error")
                return redirect(url_for("dashboard_redirect"))
            return view_func(*args, **kwargs)

        return wrapped_view

    return decorator


def get_specialist_by_user_id(user_id):
    if not user_id:
        return None
    return fetch_one(
        """
        SELECT e.id, e.especialidad, e.numero_colegiatura
        FROM especialistas e
        WHERE e.usuario_id = %s;
        """,
        (user_id,),
    )


def get_current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    return fetch_one(
        """
        SELECT id, nombre_completo, correo, rol, activo
        FROM usuarios
        WHERE id = %s;
        """,
        (user_id,),
    )


def build_evaluation_detail(evaluacion_id):
    evaluacion = fetch_one(
        """
        SELECT
            e.id,
            e.score,
            e.score_pct,
            e.nivel_autismo,
            e.probabilidades_json,
            e.created_at,
            p.id AS paciente_id,
            p.codigo,
            p.nombre_paciente,
            p.nombre_padre,
            p.nombre_madre,
            p.distrito,
            p.telefono,
            p.correo,
            p.sexo,
            p.edad
        FROM evaluaciones e
        INNER JOIN pacientes p ON p.id = e.paciente_id
        WHERE e.id = %s;
        """,
        (evaluacion_id,),
    )
    if not evaluacion:
        return None

    respuestas = fetch_one(
        """
        SELECT *
        FROM respuestas_evaluacion
        WHERE evaluacion_id = %s;
        """,
        (evaluacion_id,),
    )

    notas = fetch_all(
        """
        SELECT
            n.id,
            n.nota,
            n.created_at,
            u.nombre_completo AS especialista_nombre
        FROM notas_especialista n
        INNER JOIN especialistas e ON e.id = n.especialista_id
        INNER JOIN usuarios u ON u.id = e.usuario_id
        WHERE n.evaluacion_id = %s
        ORDER BY n.created_at DESC;
        """,
        (evaluacion_id,),
    )

    probabilidades = {}
    raw_probabilidades = evaluacion.get("probabilidades_json")
    if raw_probabilidades:
        try:
            probabilidades = json.loads(raw_probabilidades)
        except json.JSONDecodeError:
            probabilidades = {}

    respuestas_lista = []
    if respuestas:
        for index in range(1, 41):
            respuestas_lista.append(
                {
                    "numero": index,
                    "valor": respuestas.get(f"q{index}"),
                }
            )

    evaluacion["probabilidades"] = probabilidades
    evaluacion["respuestas"] = respuestas_lista
    evaluacion["notas"] = notas
    return evaluacion


def dashboard_for_role():
    role = session.get("user_role")
    if role == "admin":
        return url_for("admin_dashboard")
    return url_for("specialist_dashboard")


def build_level_distribution(rows):
    palette = {
        "Sin autismo": "#2e7d5b",
        "Autismo leve": "#c98a1a",
        "Autismo moderado": "#c96c4a",
        "Autismo severo": "#d35745",
    }
    ordered_labels = ["Sin autismo", "Autismo leve", "Autismo moderado", "Autismo severo"]
    counts = {label: 0 for label in ordered_labels}

    for row in rows or []:
        label = row.get("nivel_autismo") or "Sin clasificar"
        counts[label] = int(row.get("total") or 0)

    total = sum(counts.values())
    chart_items = []
    start = 0.0
    chart_segments = []

    for label in ordered_labels:
        count = counts.get(label, 0)
        pct = (count / total * 100) if total else 0
        end = start + pct
        color = palette.get(label, "#94a3b8")
        chart_items.append(
            {
                "label": label,
                "count": count,
                "pct": round(pct, 1),
                "color": color,
            }
        )
        if pct > 0:
            chart_segments.append(f"{color} {start:.2f}% {end:.2f}%")
        start = end

    chart_style = (
        f"conic-gradient({', '.join(chart_segments)})"
        if chart_segments
        else "conic-gradient(#e7dfd2 0 100%)"
    )

    return {
        "total": total,
        "items": chart_items,
        "chart_style": chart_style,
    }


def pdf_safe(text):
    value = "" if text is None else str(text)
    return value.encode("latin-1", "replace").decode("latin-1")


def add_pdf_header(pdf, logo_path, codigo):
    pdf.set_fill_color(247, 245, 241)
    pdf.rect(0, 0, 210, 38, style="F")
    pdf.set_draw_color(225, 216, 206)
    pdf.line(10, 38, 200, 38)

    if logo_path and os.path.exists(logo_path):
        pdf.image(logo_path, x=12, y=8, w=26)

    pdf.set_xy(44, 9)
    pdf.set_text_color(41, 51, 65)
    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 8, pdf_safe("Reporte de Evaluación"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(44)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(95, 105, 118)
    pdf.cell(0, 5, pdf_safe("CONECTEA"), new_x="LMARGIN", new_y="NEXT")

    pdf.set_xy(150, 11)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(240, 124, 86)
    pdf.cell(44, 5, pdf_safe("CÓDIGO"), align="R", new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(150)
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(41, 51, 65)
    pdf.cell(44, 5, pdf_safe(codigo), align="R", new_x="LMARGIN", new_y="NEXT")

    pdf.set_y(46)
    pdf.set_text_color(31, 41, 55)


def add_pdf_section_title(pdf, title):
    pdf.ln(5)
    pdf.set_draw_color(230, 223, 214)
    pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
    pdf.ln(3)
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(80, 63, 49)
    pdf.cell(0, 7, pdf_safe(title), new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(31, 41, 55)


def add_pdf_info_grid(pdf, items, columns=2):
    gap = 8
    width = (pdf.w - pdf.l_margin - pdf.r_margin - gap * (columns - 1)) / columns
    row_height = 14

    for start in range(0, len(items), columns):
        row_items = items[start:start + columns]
        y = pdf.get_y()
        max_height = row_height

        for column, (label, value) in enumerate(row_items):
            x = pdf.l_margin + column * (width + gap)
            text_value = pdf_safe(value) or "-"
            extra_lines = max(1, int(len(text_value) / 34) + 1)
            box_height = max(row_height, 8 + extra_lines * 4)
            max_height = max(max_height, box_height)

            pdf.set_fill_color(251, 249, 246)
            pdf.set_draw_color(228, 222, 214)
            pdf.rect(x, y, width, box_height, style="DF")

            pdf.set_xy(x + 3, y + 2.5)
            pdf.set_font("Helvetica", "B", 8)
            pdf.set_text_color(121, 112, 101)
            pdf.cell(width - 6, 4, pdf_safe(label.upper()))

            pdf.set_xy(x + 3, y + 7)
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(31, 41, 55)
            pdf.multi_cell(width - 6, 4.3, text_value)

        pdf.set_y(y + max_height + 4)


def add_pdf_probabilities(pdf, probabilities):
    if not probabilities:
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 7, "No hay probabilidades disponibles.", new_x="LMARGIN", new_y="NEXT")
        return

    color_steps = [
        (46, 125, 91),
        (201, 138, 26),
        (201, 108, 74),
        (211, 87, 69),
    ]
    usable_width = pdf.w - pdf.l_margin - pdf.r_margin

    for index, (nivel, prob) in enumerate(probabilities.items()):
        pct = max(0, min(float(prob) * 100, 100))
        if pdf.get_y() > 258:
            pdf.add_page()

        r, g, b = color_steps[index % len(color_steps)]
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(41, 51, 65)
        pdf.cell(0, 6, pdf_safe(nivel), new_x="LMARGIN", new_y="NEXT")

        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(95, 105, 118)
        pdf.cell(0, 4, pdf_safe(f"{pct:.1f}% estimado"), new_x="LMARGIN", new_y="NEXT")

        bar_y = pdf.get_y() + 2
        pdf.set_fill_color(244, 239, 231)
        pdf.set_draw_color(228, 222, 214)
        pdf.rect(pdf.l_margin, bar_y, usable_width, 7, style="DF")

        fill_width = usable_width * (pct / 100)
        if fill_width > 0:
            pdf.set_fill_color(r, g, b)
            pdf.rect(pdf.l_margin, bar_y, fill_width, 7, style="F")

        pdf.set_y(bar_y + 11)


def add_pdf_responses_table(pdf, respuestas):
    if not respuestas:
        return

    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(242, 237, 231)
    pdf.set_text_color(80, 63, 49)
    col_w = [24, 20, 24, 20, 24, 20, 24, 20]
    headers = ["Pregunta", "Resp.", "Pregunta", "Resp.", "Pregunta", "Resp.", "Pregunta", "Resp."]
    for width, header in zip(col_w, headers):
        pdf.cell(width, 8, header, border=1, align="C", fill=True)
    pdf.ln()

    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(31, 41, 55)
    fill = False
    for start in range(0, len(respuestas), 4):
        row = respuestas[start:start + 4]
        pdf.set_fill_color(251, 249, 246 if fill else 255)
        for offset, value in enumerate(row):
            respuesta = "Sí" if value == 1 else "No"
            pdf.cell(24, 7, pdf_safe(f"Q{start + offset + 1}"), border=1, align="C", fill=fill)
            pdf.cell(20, 7, pdf_safe(respuesta), border=1, align="C", fill=fill)
        for _ in range(4 - len(row)):
            pdf.cell(24, 7, "", border=1, fill=fill)
            pdf.cell(20, 7, "", border=1, fill=fill)
        pdf.ln()
        fill = not fill


def build_pdf_document(data_eval, datos_personales, datos_nino, generated_at=None):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_title("Reporte de Evaluación - CONECTEA")
    pdf.set_author("CONECTEA")

    logo_path = os.path.join(app.root_path, "static", "images", "logo.png")
    codigo = ""
    if datos_personales:
        codigo = datos_personales.get("codigo", "")

    add_pdf_header(pdf, logo_path, codigo or "SIN-CODIGO")

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(95, 105, 118)
    pdf.multi_cell(
        0,
        5,
        pdf_safe(
            "Documento generado a partir de la evaluación completada en CONECTEA. "
            "Presenta un resumen legible para consulta y seguimiento."
        ),
    )

    if datos_personales:
        add_pdf_section_title(pdf, "Datos del apoderado")
        add_pdf_info_grid(
            pdf,
            [
                ("Nombre del padre", datos_personales.get("nombre_padre", "-") or "-"),
                ("Nombre de la madre", datos_personales.get("nombre_madre", "-") or "-"),
                ("Paciente", datos_personales.get("nombre_paciente", "-") or "-"),
                ("Distrito", datos_personales.get("distrito", "-") or "-"),
                ("Teléfono", datos_personales.get("telefono", "-") or "-"),
                ("Correo", datos_personales.get("correo", "-") or "-"),
            ],
        )

    if datos_nino:
        add_pdf_section_title(pdf, "Datos del niño(a)")
        add_pdf_info_grid(
            pdf,
            [
                ("Sexo", datos_nino.get("sexo", "-") or "-"),
                ("Edad", f"{datos_nino.get('edad', '-')} años"),
            ],
        )

    add_pdf_section_title(pdf, "Resumen del resultado")
    pdf_date = generated_at or datetime.now()
    pdf.set_fill_color(250, 247, 243)
    pdf.set_draw_color(228, 222, 214)
    y = pdf.get_y()
    pdf.rect(pdf.l_margin, y, pdf.w - pdf.l_margin - pdf.r_margin, 23, style="DF")
    pdf.set_xy(pdf.l_margin + 4, y + 4)
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(41, 51, 65)
    pdf.cell(34, 8, pdf_safe(str(data_eval["score"])))
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(95, 105, 118)
    pdf.cell(26, 8, pdf_safe("/ 40"))
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(80, 63, 49)
    pdf.cell(0, 8, pdf_safe(data_eval["clase_predicha_texto"]), new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(pdf.l_margin + 4)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(31, 41, 55)
    pdf.cell(0, 5, pdf_safe(f"Porcentaje: {round(data_eval['score_pct'], 1)}%  |  Fecha: {pdf_date.strftime('%Y-%m-%d %H:%M')}"), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(12)

    add_pdf_section_title(pdf, "Probabilidades por nivel")
    add_pdf_probabilities(pdf, data_eval.get("probabilidades", {}))

    respuestas = datos_nino.get("respuestas", []) if datos_nino else []
    if respuestas:
        add_pdf_section_title(pdf, "Respuestas del cuestionario")
        add_pdf_responses_table(pdf, respuestas)

    pdf.ln(6)
    pdf.set_font("Helvetica", "I", 9)
    pdf.set_text_color(110, 110, 110)
    pdf.multi_cell(
        0,
        5,
        pdf_safe(
            "Este reporte es una herramienta de apoyo y no reemplaza una evaluación clínica profesional."
        ),
    )

    raw_pdf = pdf.output(dest="S")
    return raw_pdf.encode("latin-1") if isinstance(raw_pdf, str) else bytes(raw_pdf)


def build_pdf_payload_from_evaluation(evaluation):
    return {
        "resultado": {
            "score": float(evaluation["score"]),
            "score_pct": float(evaluation["score_pct"]),
            "clase_predicha_texto": evaluation["nivel_autismo"],
            "probabilidades": evaluation.get("probabilidades", {}),
        },
        "datos_personales": {
            "codigo": evaluation.get("codigo", ""),
            "nombre_padre": evaluation.get("nombre_padre", ""),
            "nombre_madre": evaluation.get("nombre_madre", ""),
            "nombre_paciente": evaluation.get("nombre_paciente", ""),
            "distrito": evaluation.get("distrito", ""),
            "telefono": evaluation.get("telefono", ""),
            "correo": evaluation.get("correo", ""),
        },
        "datos_nino": {
            "sexo": evaluation.get("sexo", ""),
            "edad": evaluation.get("edad", ""),
            "respuestas": [item["valor"] for item in evaluation.get("respuestas", [])],
        },
        "generated_at": evaluation.get("created_at"),
    }


@app.route("/")
def home():
    return render_template("lobby.html")


@app.route("/registro", methods=["GET", "POST"])
def registro():
    if request.method == "POST":
        datos = {
            "nombre_padre": request.form.get("nombre_padre", "").strip(),
            "nombre_madre": request.form.get("nombre_madre", "").strip(),
            "nombre_paciente": request.form.get("nombre_paciente", "").strip(),
            "distrito": request.form.get("distrito", "").strip(),
            "telefono": request.form.get("telefono", "").strip(),
            "correo": request.form.get("correo", "").strip(),
        }

        if not datos["nombre_paciente"] or not datos["distrito"] or not datos["telefono"] or not datos["correo"]:
            return render_template(
                "registro.html",
                error="Completa todos los campos obligatorios antes de continuar.",
            )

        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO pacientes (
                    nombre_padre,
                    nombre_madre,
                    nombre_paciente,
                    distrito,
                    telefono,
                    correo
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id;
                """,
                (
                    datos["nombre_padre"],
                    datos["nombre_madre"],
                    datos["nombre_paciente"],
                    datos["distrito"],
                    datos["telefono"],
                    datos["correo"],
                ),
            )
            paciente_id = cur.fetchone()[0]
            codigo = f"CT-{datetime.now().year}-{paciente_id:05d}"
            cur.execute(
                """
                UPDATE pacientes
                SET codigo = %s
                WHERE id = %s;
                """,
                (codigo, paciente_id),
            )
            conn.commit()
        finally:
            cur.close()
            conn.close()

        datos["paciente_id"] = paciente_id
        datos["codigo"] = codigo
        session["datos_personales"] = datos
        return redirect(url_for("formulario"))

    return render_template("registro.html")


@app.route("/formulario", methods=["GET"])
def formulario():
    if "datos_personales" not in session:
        return redirect(url_for("registro"))
    return render_template("index.html", question_items=QUESTION_ITEMS)


@app.route("/procesar", methods=["POST"])
def procesar():
    try:
        sexo = request.form.get("sexo")
        edad_str = request.form.get("edad")

        if not sexo or edad_str is None:
            raise ValueError("Debes ingresar sexo y edad.")

        edad = int(edad_str)
        respuestas_q = []
        for index in range(1, 41):
            valor_str = request.form.get(f"Q{index}")
            if valor_str is None or valor_str == "":
                raise ValueError(f"Falta respuesta en la pregunta Q{index}.")
            respuestas_q.append(int(valor_str))

        datos_pers = session.get("datos_personales")
        if not datos_pers or "paciente_id" not in datos_pers:
            raise ValueError("La sesión del paciente no está disponible. Vuelve a iniciar el registro.")

        resultado_modelo = modelo.predecir_desde_cuestionario(sexo, edad, respuestas_q)
        score = float(resultado_modelo["score"])
        score_pct = score / 40 * 100
        probabilidades = {k: float(v) for k, v in resultado_modelo["probabilidades"].items()}

        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                UPDATE pacientes
                SET sexo = %s,
                    edad = %s
                WHERE id = %s;
                """,
                (sexo, edad, datos_pers["paciente_id"]),
            )

            cur.execute(
                """
                INSERT INTO evaluaciones (
                    paciente_id,
                    score,
                    score_pct,
                    nivel_autismo,
                    probabilidades_json
                )
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id;
                """,
                (
                    datos_pers["paciente_id"],
                    score,
                    score_pct,
                    resultado_modelo["clase_predicha_texto"],
                    json.dumps(probabilidades),
                ),
            )
            evaluacion_id = cur.fetchone()[0]

            cur.execute(
                """
                INSERT INTO respuestas_evaluacion (
                    evaluacion_id,
                    q1, q2, q3, q4, q5, q6, q7, q8, q9, q10,
                    q11, q12, q13, q14, q15, q16, q17, q18, q19, q20,
                    q21, q22, q23, q24, q25, q26, q27, q28, q29, q30,
                    q31, q32, q33, q34, q35, q36, q37, q38, q39, q40
                )
                VALUES (
                    %s,
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                );
                """,
                (evaluacion_id, *respuestas_q),
            )
            conn.commit()
        finally:
            cur.close()
            conn.close()

        session["resultado"] = {
            "evaluacion_id": evaluacion_id,
            "score": score,
            "score_pct": score_pct,
            "clase_predicha_texto": resultado_modelo["clase_predicha_texto"],
            "probabilidades": probabilidades,
        }
        session["datos_nino"] = {
            "sexo": sexo,
            "edad": edad,
            "respuestas": respuestas_q,
        }

        return redirect(url_for("resultado"))

    except Exception as exc:
        return render_template("index.html", error=str(exc), question_items=QUESTION_ITEMS)


@app.route("/resultado", methods=["GET"])
def resultado():
    data = session.get("resultado")
    if not data:
        return redirect(url_for("formulario"))

    return render_template(
        "resultado.html",
        resultado=data,
        datos_personales=session.get("datos_personales"),
        datos_nino=session.get("datos_nino"),
    )


@app.route("/descargar_pdf", methods=["GET"])
def descargar_pdf():
    data_eval = session.get("resultado")
    datos_personales = session.get("datos_personales")
    datos_nino = session.get("datos_nino")

    if not data_eval:
        return redirect(url_for("formulario"))

    pdf_bytes = build_pdf_document(data_eval, datos_personales, datos_nino, datetime.now())

    response = make_response(pdf_bytes)
    response.headers.set("Content-Type", "application/pdf")
    disposition = "inline" if request.args.get("inline") == "1" else "attachment"
    paciente_id = (datos_personales or {}).get("paciente_id", "sin_id")
    response.headers.set("Content-Disposition", disposition, filename=f"reporte_paciente_{paciente_id}.pdf")
    return response


@app.route("/evaluacion/<int:evaluacion_id>/pdf")
@login_required("admin", "especialista")
def download_evaluation_pdf(evaluacion_id):
    evaluation = build_evaluation_detail(evaluacion_id)
    if not evaluation:
        flash("La evaluación solicitada no existe.", "error")
        return redirect(url_for("dashboard_redirect"))

    payload = build_pdf_payload_from_evaluation(evaluation)
    pdf_bytes = build_pdf_document(
        payload["resultado"],
        payload["datos_personales"],
        payload["datos_nino"],
        payload["generated_at"],
    )

    paciente_id = evaluation.get("paciente_id", "sin_id")
    filename = f"reporte_paciente_{paciente_id}.pdf"
    response = make_response(pdf_bytes)
    response.headers.set("Content-Type", "application/pdf")
    disposition = "inline" if request.args.get("inline") == "1" else "attachment"
    response.headers.set("Content-Disposition", disposition, filename=filename)
    return response


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_role"):
        return redirect(url_for("dashboard_redirect"))

    if request.method == "POST":
        correo = request.form.get("correo", "").strip().lower()
        password = request.form.get("password", "")

        user = fetch_one(
            """
            SELECT id, nombre_completo, correo, password_hash, rol, activo
            FROM usuarios
            WHERE LOWER(correo) = %s;
            """,
            (correo,),
        )

        if not user or not user["activo"] or not check_password_hash(user["password_hash"], password):
            return render_template(
                "login.html",
                error="Credenciales inválidas. Verifica tu correo y contraseña.",
            )

        session["user_id"] = user["id"]
        session["user_role"] = user["rol"]
        session["user_name"] = user["nombre_completo"]
        flash("Sesión iniciada correctamente.", "success")
        return redirect(url_for("dashboard_redirect"))

    return render_template("login.html")


@app.route("/ingreso-especialistas", methods=["GET"])
def specialist_entry():
    for key in ("user_id", "user_role", "user_name"):
        session.pop(key, None)
    return redirect(url_for("login"))


@app.route("/logout")
def logout():
    for key in ("user_id", "user_role", "user_name"):
        session.pop(key, None)
    flash("La sesión fue cerrada correctamente.", "success")
    return redirect(url_for("login"))


@app.route("/panel")
@login_required("admin", "especialista")
def dashboard_redirect():
    return redirect(dashboard_for_role())


@app.route("/admin/dashboard")
@login_required("admin")
def admin_dashboard():
    specialists = fetch_all(
        """
        SELECT
            u.id AS usuario_id,
            u.nombre_completo,
            u.correo,
            u.activo,
            e.especialidad,
            e.numero_colegiatura,
            e.id AS especialista_id
        FROM usuarios u
        INNER JOIN especialistas e ON e.usuario_id = u.id
        WHERE u.rol = 'especialista'
        ORDER BY u.created_at DESC;
        """
    )

    recent_evaluations = fetch_all(
        """
        SELECT
            ev.id,
            ev.score,
            ev.nivel_autismo,
            ev.created_at,
            p.codigo,
            p.nombre_paciente,
            p.distrito
        FROM evaluaciones ev
        INNER JOIN pacientes p ON p.id = ev.paciente_id
        ORDER BY ev.created_at DESC
        LIMIT 12;
        """
    )

    stats = fetch_one(
        """
        SELECT
            (SELECT COUNT(*) FROM usuarios WHERE rol = 'especialista') AS total_especialistas,
            (SELECT COUNT(*) FROM pacientes) AS total_pacientes,
            (SELECT COUNT(*) FROM evaluaciones) AS total_evaluaciones;
        """
    )

    return render_template(
        "admin_dashboard.html",
        specialists=specialists,
        recent_evaluations=recent_evaluations,
        stats=stats or {},
        admin_email=DEFAULT_ADMIN_EMAIL,
    )


@app.route("/admin/especialistas/nuevo", methods=["POST"])
@login_required("admin")
def create_specialist():
    nombre = request.form.get("nombre_completo", "").strip()
    correo = request.form.get("correo", "").strip().lower()
    password = request.form.get("password", "").strip()
    especialidad = request.form.get("especialidad", "").strip()
    numero_colegiatura = request.form.get("numero_colegiatura", "").strip()

    if not nombre or not correo or not password:
        flash("Nombre, correo y contraseña son obligatorios para crear un especialista.", "error")
        return redirect(url_for("admin_dashboard"))

    existing_user = fetch_one("SELECT id FROM usuarios WHERE LOWER(correo) = %s;", (correo,))
    if existing_user:
        flash("Ya existe una cuenta registrada con ese correo.", "error")
        return redirect(url_for("admin_dashboard"))

    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO usuarios (nombre_completo, correo, password_hash, rol)
            VALUES (%s, %s, %s, 'especialista')
            RETURNING id;
            """,
            (nombre, correo, generate_password_hash(password)),
        )
        usuario_id = cur.fetchone()[0]

        cur.execute(
            """
            INSERT INTO especialistas (usuario_id, especialidad, numero_colegiatura)
            VALUES (%s, %s, %s);
            """,
            (usuario_id, especialidad or None, numero_colegiatura or None),
        )
        conn.commit()
        flash("Especialista creado correctamente.", "success")
    finally:
        cur.close()
        conn.close()

    return redirect(url_for("admin_dashboard"))


@app.route("/especialista/dashboard")
@login_required("especialista")
def specialist_dashboard():
    query_text = request.args.get("q", "").strip()

    if query_text:
        evaluations = fetch_all(
            """
            SELECT
                ev.id,
                ev.score,
                ev.nivel_autismo,
                ev.created_at,
                p.codigo,
                p.nombre_paciente,
                p.edad,
                p.distrito
            FROM evaluaciones ev
            INNER JOIN pacientes p ON p.id = ev.paciente_id
            WHERE
                p.codigo ILIKE %s OR
                p.nombre_paciente ILIKE %s OR
                COALESCE(p.distrito, '') ILIKE %s
            ORDER BY ev.created_at DESC;
            """,
            tuple([f"%{query_text}%"] * 3),
        )
    else:
        evaluations = fetch_all(
            """
            SELECT
                ev.id,
                ev.score,
                ev.nivel_autismo,
                ev.created_at,
                p.codigo,
                p.nombre_paciente,
                p.edad,
                p.distrito
            FROM evaluaciones ev
            INNER JOIN pacientes p ON p.id = ev.paciente_id
            ORDER BY ev.created_at DESC
            LIMIT 40;
            """
        )

    stats = fetch_one(
        """
        SELECT
            COUNT(*) AS total_evaluaciones,
            COUNT(DISTINCT paciente_id) AS total_pacientes,
            ROUND(AVG(score), 2) AS score_promedio
        FROM evaluaciones;
        """
    )

    level_rows = fetch_all(
        """
        SELECT nivel_autismo, COUNT(*) AS total
        FROM evaluaciones
        GROUP BY nivel_autismo;
        """
    )
    level_distribution = build_level_distribution(level_rows)

    return render_template(
        "specialist_dashboard.html",
        evaluations=evaluations,
        stats=stats or {},
        level_distribution=level_distribution,
        query_text=query_text,
    )


@app.route("/evaluacion/<int:evaluacion_id>")
@login_required("admin", "especialista")
def evaluation_detail(evaluacion_id):
    evaluation = build_evaluation_detail(evaluacion_id)
    if not evaluation:
        flash("La evaluación solicitada no existe.", "error")
        return redirect(url_for("dashboard_redirect"))

    return render_template(
        "evaluation_detail.html",
        evaluation=evaluation,
        can_add_notes=session.get("user_role") == "especialista",
    )


@app.route("/evaluacion/<int:evaluacion_id>/nota", methods=["POST"])
@login_required("especialista")
def add_note(evaluacion_id):
    note = request.form.get("nota", "").strip()
    if not note:
        flash("Escribe una nota antes de guardarla.", "error")
        return redirect(url_for("evaluation_detail", evaluacion_id=evaluacion_id))

    specialist = get_specialist_by_user_id(session.get("user_id"))
    if not specialist:
        flash("No se encontro el perfil del especialista autenticado.", "error")
        return redirect(url_for("specialist_dashboard"))

    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO notas_especialista (evaluacion_id, especialista_id, nota)
            VALUES (%s, %s, %s);
            """,
            (evaluacion_id, specialist["id"], note),
        )
        conn.commit()
        flash("Nota guardada correctamente.", "success")
    finally:
        cur.close()
        conn.close()

    return redirect(url_for("evaluation_detail", evaluacion_id=evaluacion_id))


if __name__ == "__main__":
    app.run(debug=True)
