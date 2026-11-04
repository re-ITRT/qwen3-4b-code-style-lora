import numpy as np
from numbers import Real
from typing import Sequence
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.utils.multiclass import unique_labels
from sklearn.utils.validation import check_array, check_is_fitted, check_X_y


class KNN(ClassifierMixin, BaseEstimator):
    def __init__(self, n_neighbors: int = 5) -> None:
        self.n_neighbors = n_neighbors

    def fit(
        self, X: Sequence[Sequence[Real]], y: Sequence[Real]
    ) -> "KNN":
        X, y = check_X_y(X, y)
        self.classes_ = unique_labels(y)
        self.X_ = X
        self.y_ = y
        return self

    def predict(self, X: Sequence[Sequence[Real]]) -> np.ndarray:
        check_is_fitted(self, ["X_", "y_"])
        X = check_array(X)
        distances = np.sqrt(
            np.sum((X[:, None, :] - self.X_[None, :, :]) ** 2, axis=2)
        )
        indices = np.argsort(distances, axis=1)[:, : self.n_neighbors]
        nearest_labels = self.y_[indices]
        predictions = np.empty(len(X), dtype=self.classes_.dtype)
        for i, row in enumerate(nearest_labels):
            values, counts = np.unique(row, return_counts=True)
            predictions[i] = values[np.argmax(counts)]
        return predictions