import json
import os
from datetime import datetime
from functools import wraps
from urllib.parse import urlparse

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
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

DATABASE_URL = os.getenv("DATABASE_URL")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "CONECTEA")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_PORT = int(os.getenv("DB_PORT", 5432))

DEFAULT_ADMIN_NAME = os.getenv("ADMIN_NAME", "Administrador")
DEFAULT_ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")
DEFAULT_ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

LOCATION_OPTIONS = {
    "Lima": [
        "Ancon",
        "Ate",
        "Barranco",
        "Brena",
        "Carabayllo",
        "Chaclacayo",
        "Chorrillos",
        "Cieneguilla",
        "Comas",
        "El Agustino",
        "Independencia",
        "Jesus Maria",
        "La Molina",
        "La Victoria",
        "Lima",
        "Lince",
        "Los Olivos",
        "Lurigancho",
        "Lurin",
        "Magdalena del Mar",
        "Miraflores",
        "Pachacamac",
        "Pucusana",
        "Pueblo Libre",
        "Puente Piedra",
        "Punta Hermosa",
        "Punta Negra",
        "Rimac",
        "San Bartolo",
        "San Borja",
        "San Isidro",
        "San Juan de Lurigancho",
        "San Juan de Miraflores",
        "San Luis",
        "San Martin de Porres",
        "San Miguel",
        "Santa Anita",
        "Santa Maria del Mar",
        "Santa Rosa",
        "Santiago de Surco",
        "Surquillo",
        "Villa El Salvador",
        "Villa Maria del Triunfo",
    ],
    "Callao": [
        "Bellavista",
        "Callao",
        "Carmen de la Legua Reynoso",
        "La Perla",
        "La Punta",
        "Mi Peru",
        "Ventanilla",
    ],
    "Canete": [
        "Asia",
        "Calango",
        "Cerro Azul",
        "Chilca",
        "Imperial",
        "Mala",
        "Nuevo Imperial",
        "San Vicente de Canete",
    ],
    "Huaral": [
        "Aucallama",
        "Chancay",
        "Huaral",
        "Ihuari",
        "Sumbilca",
    ],
    "Huaura": [
        "Caleta de Carquin",
        "Huacho",
        "Hualmay",
        "Huaura",
        "Santa Maria",
        "Vegueta",
    ],
}

SCHEMA_READY = False

modelo = MiterapModel(artifacts_dir="artifacts")


def get_connection():
    if DATABASE_URL:
        normalized_url = DATABASE_URL.replace("postgres://", "postgresql://", 1)
        parsed = urlparse(normalized_url)
        connect_kwargs = {
            "host": parsed.hostname,
            "dbname": parsed.path.lstrip("/"),
            "user": parsed.username,
            "password": parsed.password,
            "port": parsed.port or 5432,
        }

        ssl_mode = os.getenv("DB_SSLMODE")
        if ssl_mode:
            connect_kwargs["sslmode"] = ssl_mode

        return psycopg2.connect(**connect_kwargs)

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
                dni VARCHAR(20),
                nombre_paciente VARCHAR(150) NOT NULL,
                provincia VARCHAR(120),
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
        cur.execute("ALTER TABLE pacientes ADD COLUMN IF NOT EXISTS dni VARCHAR(20);")
        cur.execute("ALTER TABLE pacientes ADD COLUMN IF NOT EXISTS provincia VARCHAR(120);")

        cur.execute("SELECT id FROM usuarios WHERE rol = 'admin' LIMIT 1;")
        admin = cur.fetchone()
        if not admin:
            if not DEFAULT_ADMIN_EMAIL or not DEFAULT_ADMIN_PASSWORD:
                raise RuntimeError(
                    "Configura ADMIN_EMAIL y ADMIN_PASSWORD para crear el usuario administrador inicial."
                )
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
            p.dni,
            p.provincia,
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


class ReportPDF(FPDF):
    def __init__(self, logo_path=None, codigo="SIN-CODIGO"):
        super().__init__()
        self.logo_path = logo_path
        self.codigo = codigo or "SIN-CODIGO"

    def header(self):
        self.set_fill_color(248, 244, 238)
        self.rect(0, 0, 210, 28, style="F")
        self.set_fill_color(214, 120, 84)
        self.rect(0, 0, 210, 4, style="F")
        self.set_draw_color(229, 220, 210)
        self.line(self.l_margin, 28, self.w - self.r_margin, 28)

        if self.logo_path and os.path.exists(self.logo_path):
            self.image(self.logo_path, x=self.l_margin, y=8, w=16)

        self.set_xy(44, 9)
        self.set_text_color(41, 51, 65)
        self.set_font("Helvetica", "B", 18)
        self.cell(0, 8, pdf_safe("Reporte de Evaluacion"), new_x="LMARGIN", new_y="NEXT")
        self.set_x(44)
        self.set_font("Helvetica", "", 10)
        self.set_text_color(95, 105, 118)
        self.cell(0, 5, pdf_safe("CONECTEA"), new_x="LMARGIN", new_y="NEXT")

        self.set_xy(150, 11)
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(240, 124, 86)
        self.cell(44, 5, pdf_safe("CODIGO"), align="R", new_x="LMARGIN", new_y="NEXT")
        self.set_x(150)
        self.set_font("Helvetica", "", 11)
        self.set_text_color(41, 51, 65)
        self.cell(44, 5, pdf_safe(self.codigo), align="R", new_x="LMARGIN", new_y="NEXT")

        self.set_y(46)
        self.set_text_color(31, 41, 55)


def add_pdf_section_title(pdf, title):
    pdf.ln(4)
    y = pdf.get_y()
    pdf.set_fill_color(255, 248, 242)
    pdf.set_draw_color(235, 223, 211)
    pdf.rect(pdf.l_margin, y, pdf.w - pdf.l_margin - pdf.r_margin, 9, style="DF")
    pdf.set_xy(pdf.l_margin + 4, y + 1.4)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(103, 72, 50)
    pdf.cell(0, 6, pdf_safe(title), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    pdf.set_text_color(31, 41, 55)


def add_pdf_info_grid(pdf, items, columns=2):
    gap = 6
    width = (pdf.w - pdf.l_margin - pdf.r_margin - gap * (columns - 1)) / columns
    row_height = 16

    for start in range(0, len(items), columns):
        row_items = items[start:start + columns]
        y = pdf.get_y()
        max_height = row_height

        for column, (label, value) in enumerate(row_items):
            x = pdf.l_margin + column * (width + gap)
            text_value = pdf_safe(value) or "-"
            extra_lines = max(1, int(len(text_value) / 30) + 1)
            box_height = max(row_height, 9 + extra_lines * 4.6)
            max_height = max(max_height, box_height)

            pdf.set_fill_color(252, 250, 247)
            pdf.set_draw_color(231, 225, 217)
            pdf.rect(x, y, width, box_height, style="DF")
            pdf.set_fill_color(240, 234, 227)
            pdf.rect(x, y, width, 5.5, style="F")

            pdf.set_xy(x + 3, y + 1.1)
            pdf.set_font("Helvetica", "B", 8)
            pdf.set_text_color(121, 100, 84)
            pdf.cell(width - 6, 4, pdf_safe(label.upper()))

            pdf.set_xy(x + 3, y + 7.8)
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(31, 41, 55)
            pdf.multi_cell(width - 6, 4.3, text_value)

        pdf.set_y(y + max_height + 4)


def probability_color(label):
    value = (label or "").lower()
    if "leve" in value:
        return (222, 181, 82)
    if "moderado" in value:
        return (223, 136, 67)
    if "severo" in value or "alto" in value:
        return (196, 89, 69)
    return (108, 146, 115)


def add_pdf_probabilities(pdf, probabilities):
    if not probabilities:
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 7, pdf_safe("No hay probabilidades disponibles."), new_x="LMARGIN", new_y="NEXT")
        return

    pdf.set_font("Helvetica", "B", 10)
    pdf.set_fill_color(242, 237, 231)
    pdf.set_text_color(80, 63, 49)
    pdf.cell(110, 8, "Nivel", border=1, fill=True)
    pdf.cell(0, 8, "Probabilidad", border=1, fill=True, new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(31, 41, 55)
    fill = False
    for nivel, prob in probabilities.items():
        pct = max(0, min(float(prob) * 100, 100))
        pdf.set_fill_color(251, 249, 246 if fill else 255)
        pdf.cell(110, 8, pdf_safe(nivel), border=1, fill=fill)
        pdf.cell(0, 8, pdf_safe(f"{pct:.1f}%"), border=1, fill=fill, new_x="LMARGIN", new_y="NEXT")
        fill = not fill


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
            respuesta = "Si" if value == 1 else "No"
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
    pdf.set_title("Reporte de Evaluacion - CONECTEA")
    pdf.set_author("CONECTEA")

    logo_path = os.path.join(app.root_path, "static", "images", "logo.png")
    codigo = ""
    if datos_personales:
        codigo = datos_personales.get("codigo", "")

    pdf = ReportPDF(logo_path=logo_path, codigo=codigo or "SIN-CODIGO")
    pdf.set_margins(12, 12, 12)
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.set_title("Reporte de Evaluación - CONECTEA")
    pdf.set_author("CONECTEA")

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(88, 98, 110)
    pdf.multi_cell(
        0,
        5,
        pdf_safe(
            "Documento generado a partir de la evaluacion completada en CONECTEA. "
            "Presenta un resumen legible para consulta y seguimiento."
        ),
    )
    pdf.ln(2)

    if datos_personales:
        add_pdf_section_title(pdf, "Datos del apoderado")
        add_pdf_info_grid(
            pdf,
            [
                ("Nombre del padre", datos_personales.get("nombre_padre", "-") or "-"),
                ("Nombre de la madre", datos_personales.get("nombre_madre", "-") or "-"),
                ("Paciente", datos_personales.get("nombre_paciente", "-") or "-"),
                ("DNI", datos_personales.get("dni", "-") or "-"),
                ("Provincia", datos_personales.get("provincia", "-") or "-"),
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
    add_pdf_summary_card(pdf, data_eval, pdf_date)

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
            "dni": evaluation.get("dni", ""),
            "nombre_paciente": evaluation.get("nombre_paciente", ""),
            "provincia": evaluation.get("provincia", ""),
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
            "dni": request.form.get("dni", "").strip(),
            "nombre_paciente": request.form.get("nombre_paciente", "").strip(),
            "provincia": request.form.get("provincia", "").strip(),
            "distrito": request.form.get("distrito", "").strip(),
            "telefono": request.form.get("telefono", "").strip(),
            "correo": request.form.get("correo", "").strip(),
        }

        if (
            not datos["dni"]
            or not datos["nombre_paciente"]
            or not datos["provincia"]
            or not datos["distrito"]
            or not datos["telefono"]
            or not datos["correo"]
        ):
            flash("Completa todos los campos obligatorios antes de continuar.", "error")
            return render_template(
                "registro.html",
                location_options=LOCATION_OPTIONS,
                form_data=datos,
            )

        if not datos["dni"].isdigit() or len(datos["dni"]) != 8:
            flash("El DNI del paciente debe tener 8 digitos.", "error")
            return render_template(
                "registro.html",
                location_options=LOCATION_OPTIONS,
                form_data=datos,
            )

        if datos["provincia"] not in LOCATION_OPTIONS or datos["distrito"] not in LOCATION_OPTIONS[datos["provincia"]]:
            flash("Selecciona una provincia y distrito validos.", "error")
            return render_template(
                "registro.html",
                location_options=LOCATION_OPTIONS,
                form_data=datos,
            )

        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO pacientes (
                    nombre_padre,
                    nombre_madre,
                    dni,
                    nombre_paciente,
                    provincia,
                    distrito,
                    telefono,
                    correo
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id;
                """,
                (
                    datos["nombre_padre"],
                    datos["nombre_madre"],
                    datos["dni"],
                    datos["nombre_paciente"],
                    datos["provincia"],
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
        flash("Datos del paciente guardados correctamente.", "success")
        return redirect(url_for("formulario"))

    return render_template("registro.html", location_options=LOCATION_OPTIONS, form_data={})


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

        flash("Evaluacion guardada correctamente.", "success")
        return redirect(url_for("resultado"))

    except Exception as exc:
        flash(str(exc), "error")
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
            p.dni,
            p.provincia,
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
                p.dni,
                p.edad,
                p.provincia,
                p.distrito
            FROM evaluaciones ev
            INNER JOIN pacientes p ON p.id = ev.paciente_id
            WHERE
                p.codigo ILIKE %s OR
                COALESCE(p.dni, '') ILIKE %s OR
                p.nombre_paciente ILIKE %s OR
                COALESCE(p.provincia, '') ILIKE %s OR
                COALESCE(p.distrito, '') ILIKE %s
            ORDER BY ev.created_at DESC;
            """,
            tuple([f"%{query_text}%"] * 5),
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
                p.dni,
                p.edad,
                p.provincia,
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
