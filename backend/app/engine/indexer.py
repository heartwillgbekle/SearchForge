from collections import defaultdict
from .preprocessor import tokenize


class InvertedIndex:
    def __init__(self):
        self.index = defaultdict(dict)
        self.documents = {}
        self.document_lengths = {}

    def add_document(self, doc_id, text):
        self.documents[doc_id] = text

        tokens = tokenize(text)
        self.document_lengths[doc_id] = len(tokens)

        for token in tokens:
            if doc_id not in self.index[token]:
                self.index[token][doc_id] = 0

            self.index[token][doc_id] += 1

    def build(self, documents):
        for doc_id, text in documents.items():
            self.add_document(doc_id, text)

    def get_postings(self, term):
        return self.index.get(term, {})

    def document_frequency(self, term):
        return len(self.index.get(term, {}))

    def term_frequency(self, term, doc_id):
        return self.index.get(term, {}).get(doc_id, 0)

    def total_documents(self):
        return len(self.documents)

    def total_terms(self):
        return len(self.index)
