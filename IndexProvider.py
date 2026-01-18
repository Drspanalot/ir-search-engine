from inverted_index_gcp import InvertedIndex


class IndexProvider:
    """טעינת האינדקסים ההפוכים עבור חלקי המאמר השונים"""
    def __init__(self, base_path="."):
        # קריאת האינדקסים שנוצרו ב-GCP [cite: 29, 44]
        self.body_index = InvertedIndex.read_index(base_path, "body")
        self.title_index = InvertedIndex.read_index(base_path, "title")
        self.anchor_index = InvertedIndex.read_index(base_path, "anchor")