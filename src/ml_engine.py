from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np


def get_cluster_names() -> list[str]:
    """Zwraca listę nazw klastrów używanych do mapowania star_class."""
    return ['Naukowy', 'Techniczny', 'Projektowy', 'Archiwalny', 'Ogólny']


def analyze_texts(texts: list[str], filenames: list[str] = None) -> list[dict]:
    """
    Generuje metadane Sci-Fi dla listy tekstów bez użycia API zewnętrznego.

    Args:
        texts: lista oczyszczonych tekstów notatek
        filenames: lista nazw plików (opcjonalna, do suggested_links)

    Returns:
        Lista słowników: [{brief, star_class, energy_level, suggested_links, content}, ...]
    """
    n_docs = len(texts)
    if n_docs == 0:
        return []

    # 1. TF-IDF
    vectorizer = TfidfVectorizer(max_features=1000, stop_words='english', min_df=1)
    tfidf_matrix = vectorizer.fit_transform(texts)

    # 2. KMeans
    if n_docs >= 3:
        n_clusters = min(5, n_docs)
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        clusters = kmeans.fit_predict(tfidf_matrix)
    else:
        clusters = np.zeros(n_docs, dtype=int)

    # 3. Cosine similarity
    sim_matrix = cosine_similarity(tfidf_matrix)

    # 4. Metadata per text
    results = []
    cluster_names = get_cluster_names()

    for i, text in enumerate(texts):
        # brief: pierwsze 15 słów + kropka
        words = text.split()
        brief = ' '.join(words[:15]) + '.'

        # star_class z mapowania klastra
        cluster_idx = int(clusters[i])
        star_class = cluster_names[cluster_idx] if cluster_idx < len(cluster_names) else cluster_names[-1]

        # energy_level: 1-10 w zależności od długości tekstu
        energy = min(10, max(1, len(text) // 1000 + 1))
        energy_level = str(energy)

        # suggested_links: top 5 podobnych dokumentów (pomijając samego siebie)
        sim_scores = sim_matrix[i].copy()
        sim_scores[i] = -1.0
        top_indices = np.argsort(sim_scores)[::-1][:5]

        if filenames is not None:
            suggested_links = [filenames[idx] for idx in top_indices]
        else:
            suggested_links = [str(idx) for idx in top_indices]

        # content: pierwsze 3000 znaków
        content = text[:3000]

        results.append({
            'brief': brief,
            'star_class': star_class,
            'energy_level': energy_level,
            'suggested_links': suggested_links,
            'content': content
        })

    return results


if __name__ == '__main__':
    sample_texts = [
        "Machine learning is a subset of artificial intelligence that enables systems to learn from data. "
        "It involves algorithms that improve through experience. Deep learning uses neural networks with many layers.",
        "Python is a high-level programming language with dynamic semantics. It is widely used for web development, "
        "data analysis, and automation. Its simple syntax makes it accessible.",
        "The history of computing dates back to early mechanical calculators. Modern computers evolved through "
        "vacuum tubes, transistors, and integrated circuits. Today we have powerful processors."
    ]
    sample_filenames = ["ml_notes.md", "python_notes.md", "history_notes.md"]

    output = analyze_texts(sample_texts, sample_filenames)
    for item in output:
        print(item)
