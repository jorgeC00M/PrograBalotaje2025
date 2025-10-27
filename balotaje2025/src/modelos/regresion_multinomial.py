import pandas as pd
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report
from sklearn.model_selection import train_test_split

def entrenar_multinomial(df: pd.DataFrame, target: str, features: list[str], test_size=0.25, seed=42):
    X = df[features].copy(); y = df[target].copy()

    num = X.select_dtypes(include="number").columns.tolist()
    cat = [c for c in X.columns if c not in num]

    pre = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(with_mean=False), num),
            ("cat", OneHotEncoder(handle_unknown="ignore"), cat),
        ],
        remainder="drop",
        sparse_threshold=0.3
    )

    clf = LogisticRegression(multi_class="multinomial", solver="lbfgs", max_iter=1000)
    pipe = Pipeline([("pre", pre), ("clf", clf)])

    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=test_size, random_state=seed, stratify=y)
    pipe.fit(Xtr, ytr)
    pred = pipe.predict(Xte)

    # OJO: classes_ viene del estimador final, no del Pipeline
    classes = pipe.named_steps["clf"].classes_

    acc = accuracy_score(yte, pred)
    cm = confusion_matrix(yte, pred, labels=classes)
    report = classification_report(yte, pred, output_dict=True, zero_division=0)

    return {
        "pipeline": pipe,
        "accuracy": float(acc),
        "confusion_matrix": cm.tolist(),
        "classes": classes.tolist(),
        "report": report,
        "features": features,
    }
