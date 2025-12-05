import os
from datetime import datetime
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    make_response,
)
from miterap_model import MiterapModel
from fpdf import FPDF  # pip install fpdf2
import psycopg2

# ==========================
# CONFIG FLASK
# ==========================
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev_secret_key")

# ==========================
# CONFIG BD POSTGRES
# ==========================
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "CONECTEA")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "adriano13")
DB_PORT = int(os.getenv("DB_PORT", 5432))



def get_connection():
    return psycopg2.connect(
        host=DB_HOST,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        port=DB_PORT,
    )


# ==========================
# CARGA DEL MODELO
# ==========================
modelo = MiterapModel(artifacts_dir="artifacts")


# ---------------------------
# HOME / LOBBY
# ---------------------------
@app.route("/")
def home():
    return render_template("lobby.html")   # pagina de bienvenida


# ---------------------------
# REGISTRO DE DATOS PERSONALES
# ---------------------------
@app.route("/registro", methods=["GET", "POST"])
def registro():
    if request.method == "POST":
        datos = {
            "nombre_padre": request.form.get("nombre_padre", ""),
            "nombre_madre": request.form.get("nombre_madre", ""),
            "nombre_paciente": request.form.get("nombre_paciente", ""),
            "distrito": request.form.get("distrito", ""),
            "telefono": request.form.get("telefono", ""),
            "correo": request.form.get("correo", ""),
        }

        # 1) Guardar en la BD
        try:
            conn = get_connection()
            cur = conn.cursor()

            # Insertamos y recuperamos el id autoincremental
            cur.execute(
                """
                INSERT INTO registros_pacientes
                  (nombre_padre, nombre_madre, nombre_paciente, distrito, telefono, correo)
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
            id_registro = cur.fetchone()[0]

            # Generar código tipo CT-2025-00001
            anio = datetime.now().year
            codigo = f"CT-{anio}-{id_registro:05d}"

            # Actualizar el registro con el código
            cur.execute(
                """
                UPDATE registros_pacientes
                SET codigo = %s
                WHERE id = %s;
                """,
                (codigo, id_registro),
            )

            conn.commit()

        finally:
            cur.close()
            conn.close()

        # 2) Guardar en sesion para usar luego
        datos["id_registro"] = id_registro
        datos["codigo"] = codigo   # lo usaremos luego para guardar las respuestas
        session["datos_personales"] = datos

        # 3) Ir al formulario del test
        return redirect(url_for("formulario"))

    # GET -> mostramos el formulario de datos personales
    return render_template("registro.html")


# ---------------------------
# FORMULARIO (40 PREGUNTAS)
# ---------------------------
@app.route("/formulario", methods=["GET"])
def formulario():
    return render_template("index.html")   # formulario de 40 preguntas


# ---------------------------
# PROCESAR FORMULARIO
# ---------------------------
@app.route("/procesar", methods=["POST"])
def procesar():
    try:
        sexo = request.form.get("sexo")
        edad_str = request.form.get("edad")

        if not sexo or edad_str is None:
            raise ValueError("Debes ingresar sexo y edad.")

        edad = int(edad_str)

        # Leer las 40 preguntas
        respuestas_q = []
        for i in range(1, 41):
            valor_str = request.form.get(f"Q{i}")
            if valor_str is None or valor_str == "":
                raise ValueError(f"Falta respuesta en la pregunta Q{i}.")
            respuestas_q.append(int(valor_str))

        # Llamar al modelo
        resultado_modelo = modelo.predecir_desde_cuestionario(sexo, edad, respuestas_q)

        # Score bruto (0-40)
        score = float(resultado_modelo["score"])
        # Porcentaje (0–100) para la barrita
        score_pct = score / 40 * 100

        # ------------- ACTUALIZAR REGISTRO EN BD + GUARDAR RESPUESTAS -------------
        datos_pers = session.get("datos_personales")
        if datos_pers and "id_registro" in datos_pers:
            try:
                conn = get_connection()
                cur = conn.cursor()

                # 1) Actualizar datos del registro principal
                cur.execute(
                    """
                    UPDATE registros_pacientes
                    SET sexo = %s,
                        edad = %s,
                        score = %s,
                        nivel_autismo = %s
                    WHERE id = %s;
                    """,
                    (
                        sexo,
                        edad,
                        score,
                        resultado_modelo["clase_predicha_texto"],
                        datos_pers["id_registro"],
                    ),
                )

                # 2) Insertar respuestas del cuestionario ligadas al CODIGO
                codigo = datos_pers.get("codigo")
                if codigo:
                    cur.execute(
                        """
                        INSERT INTO respuestas_cuestionario (
                            codigo,
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
                        (codigo, *respuestas_q),
                    )

                conn.commit()
            finally:
                cur.close()
                conn.close()

        # Guardamos el resultado en sesion
        session["resultado"] = {
            "score": score,
            "score_pct": score_pct,  # para la flechita en la barra
            "clase_predicha_texto": resultado_modelo["clase_predicha_texto"],
            "probabilidades": {
                k: float(v) for k, v in resultado_modelo["probabilidades"].items()
            },
        }

        # Guardar datos del nino para mostrarlos y usarlos en el PDF
        session["datos_nino"] = {
            "sexo": sexo,
            "edad": edad,
            "respuestas": respuestas_q,
        }

        return redirect(url_for("resultado"))

    except Exception as e:
        # Si hay error, volvemos al formulario mostrando el mensaje
        return render_template("index.html", error=str(e))


# ---------------------------
# PÁGINA DE RESULTADO
# ---------------------------
@app.route("/resultado", methods=["GET"])
def resultado():
    data = session.get("resultado")
    if not data:
        # Si no hay datos, manda al formulario de nuevo
        return redirect(url_for("formulario"))

    # No hacemos pop para reutilizar en el PDF
    datos_personales = session.get("datos_personales")
    datos_nino = session.get("datos_nino")

    return render_template(
        "resultado.html",
        resultado=data,
        datos_personales=datos_personales,
        datos_nino=datos_nino,
    )


# ---------------------------
# DESCARGAR PDF
# ---------------------------
@app.route("/descargar_pdf", methods=["GET"])
def descargar_pdf():
    # Datos guardados en sesion
    data_eval = session.get("resultado")
    datos_personales = session.get("datos_personales")
    datos_nino = session.get("datos_nino")

    # Si no hay datos de evaluacion, redirige al formulario
    if not data_eval:
        return redirect(url_for("formulario"))

    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Titulo
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Reporte de Evaluacion - ConecTEA", ln=1, align="C")
    pdf.ln(5)

    # Datos del apoderado
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "Datos del apoderado:", ln=1)

    pdf.set_font("Arial", "", 11)
    if datos_personales:
        pdf.cell(0, 6, f"Nombre del padre: {datos_personales.get('nombre_padre', '')}", ln=1)
        pdf.cell(0, 6, f"Nombre de la madre: {datos_personales.get('nombre_madre', '')}", ln=1)
        pdf.cell(0, 6, f"Nombre del paciente: {datos_personales.get('nombre_paciente', '')}", ln=1)
        pdf.cell(0, 6, f"Distrito: {datos_personales.get('distrito', '')}", ln=1)
        pdf.cell(0, 6, f"Telefono: {datos_personales.get('telefono', '')}", ln=1)
        pdf.cell(0, 6, f"Correo: {datos_personales.get('correo', '')}", ln=1)
    else:
        pdf.cell(0, 6, "No se registraron datos personales.", ln=1)

    pdf.ln(5)

    # Datos del nino(a)
    if datos_nino:
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 8, "Datos del nino(a):", ln=1)

        pdf.set_font("Arial", "", 11)
        pdf.cell(0, 6, f"Sexo: {datos_nino.get('sexo', '')}", ln=1)
        pdf.cell(0, 6, f"Edad: {datos_nino.get('edad', '')} anos", ln=1)
        pdf.ln(5)

    # Resultado principal
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "Resultado de la prediccion:", ln=1)

    pdf.set_font("Arial", "", 11)
    pdf.cell(0, 6, f"Score total (0-40): {data_eval['score']}", ln=1)
    pdf.cell(0, 6, f"Nivel de autismo: {data_eval['clase_predicha_texto']}", ln=1)
    pdf.ln(4)

    # Probabilidades
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "Probabilidades:", ln=1)
    pdf.set_font("Arial", "", 11)

    for nivel, prob in data_eval["probabilidades"].items():
        pdf.cell(0, 6, f"{nivel}: {round(prob, 3)}", ln=1)

    # Tabla de respuestas Q1..Q40
    respuestas = []
    if datos_nino and "respuestas" in datos_nino:
        respuestas = datos_nino["respuestas"]

    if respuestas:
        pdf.ln(6)
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 8, "Respuestas al cuestionario:", ln=1)

        # Encabezados
        pdf.set_font("Arial", "B", 10)
        pdf.cell(30, 6, "Pregunta", border=1)
        pdf.cell(40, 6, "Respuesta", border=1, ln=1)

        # Filas
        pdf.set_font("Arial", "", 10)
        for idx, valor in enumerate(respuestas, start=1):
            pdf.cell(30, 6, f"Q{idx}", border=1)
            pdf.cell(40, 6, "Si" if valor == 1 else "No", border=1, ln=1)

    # Salida a bytes (compatible con todas las versiones)
    raw_pdf = pdf.output(dest="S")
    if isinstance(raw_pdf, str):
        pdf_bytes = raw_pdf.encode("latin-1")
    else:
        pdf_bytes = bytes(raw_pdf)

    response = make_response(pdf_bytes)
    response.headers.set("Content-Type", "application/pdf")
    response.headers.set(
        "Content-Disposition", "attachment", filename="reporte_conectea.pdf"
    )
    return response


# ==========================
# MAIN
# ==========================
if __name__ == "__main__":
    app.run(debug=True)
