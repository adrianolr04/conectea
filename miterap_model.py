import joblib
import pandas as pd
from pathlib import Path
from typing import Sequence, Union


SCQ_YES_SCORED_ITEMS = {3, 4, 5, 6, 7, 8, 10, 11, 12, 13, 14, 15, 16, 17, 18}
SCQ_NO_SCORED_ITEMS = {
    2, 9, 19, 20, 21, 22, 23, 24, 25, 26,
    27, 28, 29, 30, 31, 32, 33, 34, 35, 36,
    37, 38, 39, 40,
}


def score_scq_responses(raw_responses: Sequence[int]):
    if len(raw_responses) != 40:
        raise ValueError("Debes ingresar exactamente 40 respuestas (Q1 a Q40).")

    normalized = [int(value) for value in raw_responses]
    has_phrase_speech = normalized[0] == 1
    scored_responses = []

    for index, answer in enumerate(normalized, start=1):
        if index == 1 or (not has_phrase_speech and 2 <= index <= 7):
            scored_responses.append(0)
        elif index in SCQ_YES_SCORED_ITEMS:
            scored_responses.append(1 if answer == 1 else 0)
        elif index in SCQ_NO_SCORED_ITEMS:
            scored_responses.append(1 if answer == 0 else 0)
        else:
            scored_responses.append(0)

    max_score = 39 if has_phrase_speech else 33
    return scored_responses, max_score


class MiterapModel:
    def __init__(self, artifacts_dir: Union[str, Path] = "artifacts"):
        artifacts_dir = Path(artifacts_dir)

        # Cargar artefactos
        self.model = joblib.load(artifacts_dir / "best_model.pkl")
        self.scaler = joblib.load(artifacts_dir / "scaler.pkl")
        self.sexo_encoder = joblib.load(artifacts_dir / "sexo_encoder.pkl")
        self.feature_columns = joblib.load(artifacts_dir / "feature_columns.pkl")

        # Mapa de clases → texto
        self.mapa_clases = {
            0: "Sin autismo",
            1: "Autismo leve",
            2: "Autismo moderado",
            3: "Autismo severo",
        }

    def predecir_desde_cuestionario(
        self,
        sexo: str,
        edad: int,
        respuestas_q: Sequence[int],
    ):
        """
        sexo: 'M', 'F', etc.
        edad: edad en años (int)
        respuestas_q: iterable con 40 números (Q1...Q40)
        """

        respuestas_puntuadas, max_score = score_scq_responses(respuestas_q)

        # ⚠️ Usa EXACTAMENTE los mismos nombres de columnas que en tu dataset
        datos = {"Sexo": sexo, "Edad": edad}  # <-- 'Edad' con mayúscula

        for i, valor in enumerate(respuestas_puntuadas, start=1):
            datos[f"Q{i}"] = valor

        df_nuevo = pd.DataFrame([datos])

        # Codificar Sexo igual que en entrenamiento
        df_nuevo["Sexo"] = self.sexo_encoder.transform(df_nuevo["Sexo"])

        # Comprobación útil: ver si falta alguna columna
        faltantes = [c for c in self.feature_columns if c not in df_nuevo.columns]
        if faltantes:
            raise ValueError(f"Faltan columnas en la entrada: {faltantes}")

        # Ordenar columnas
        df_nuevo = df_nuevo[self.feature_columns]

        # Escalar
        X_scaled = self.scaler.transform(df_nuevo)

        # Predicción
        clase_pred = int(self.model.predict(X_scaled)[0])
        probas = self.model.predict_proba(X_scaled)[0]

        score_crudo = int(sum(respuestas_puntuadas))
        texto_clase = self.mapa_clases.get(clase_pred, f"Clase {clase_pred}")

        resultado = {
            "score": score_crudo,
            "max_score": max_score,
            "respuestas_puntuadas": respuestas_puntuadas,
            "clase_predicha_num": clase_pred,
            "clase_predicha_texto": texto_clase,
            "probabilidades": {
                self.mapa_clases.get(i, f"Clase {i}"): float(probas[i])
                for i in range(len(probas))
            },
        }

        return resultado
