import pandas as pd
from catboost import CatBoostClassifier, Pool


def load_models(model_dir: str = "catboost_info") -> list:
    """
    Загружает по одной модели CatBoostClassifier из каждой папки fold-0..fold-4.
    """
    models = []
    for i in range(5):
        m = CatBoostClassifier()
        m.load_model(f"{model_dir}/fold-{i}/model")
        models.append(m)
    return models


def predict_ratings(features_df: pd.DataFrame, models: list = None) -> pd.DataFrame:
    """
    Предсказывает Sybil score и our_rating на основании обученных моделей.
    Учитывает порядок и список признаков, которые ожидали модели при обучении.
    """
    # Загружаем модели
    if models is None:
        models = load_models()
    # Определяем имена признаков по первой модели
    feature_names = models[0].feature_names_
    # Готовим матрицу признаков в нужном порядке, отсутствующие заполняем 0
    X = features_df.drop(columns=["address"], errors="ignore")
    X = X.reindex(columns=feature_names, fill_value=0)

    # Усредняем probabilistic predictions
    preds_sum = None
    for model in models:
        pool = Pool(data=X)
        proba = model.predict(pool, prediction_type="Probability")[:, 1]
        preds_sum = proba if preds_sum is None else preds_sum + proba
    preds = preds_sum / len(models)

    # Преобразование вероятности в рейтинг по порогам
    thresholds = [0.024642, 0.097071, 0.176236]
    labels = ["A", "B", "C", "D"]

    def to_label(p):
        idx = sum(p > t for t in thresholds)
        return labels[idx]

    # Собираем финальный DataFrame
    result = features_df.copy()
    result["sybil_score"] = preds
    result["our_rating"] = result["sybil_score"].apply(to_label)
    return result[["address", "sybil_score", "our_rating"]]
