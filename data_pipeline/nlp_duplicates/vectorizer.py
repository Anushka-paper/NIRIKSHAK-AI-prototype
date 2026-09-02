import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def compute_similarity_matrix(texts: list[str]):
    """
    Computes text similarity vectors and cosine similarity matrix (§9).
    Uses TF-IDF + n-gram vectorization for ultra-fast performance on government boilerplate text.
    """
    if not texts:
        return np.array([[]])

    vectorizer = TfidfVectorizer(ngram_range=(1, 3), min_df=1)
    tfidf_matrix = vectorizer.fit_transform(texts)
    
    sim_matrix = cosine_similarity(tfidf_matrix)
    return sim_matrix

