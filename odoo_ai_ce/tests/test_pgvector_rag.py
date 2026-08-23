# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase
from ..tools.extractor import chunk_text, cosine_similarity

class TestAiCePgvectorRag(TransactionCase):

    def test_chunk_text(self):
        text = "Paragraph 1 is about Odoo ERP architecture.\n\nParagraph 2 is about Autonomous AI Agents.\n\nParagraph 3 is about pgvector embeddings."
        chunks = chunk_text(text, chunk_size=80, overlap=10)
        self.assertGreaterEqual(len(chunks), 2)

    def test_cosine_similarity(self):
        vec_a = [1.0, 0.0, 0.0]
        vec_b = [1.0, 0.0, 0.0]
        vec_c = [0.0, 1.0, 0.0]

        # Identical vectors should have similarity 1.0
        self.assertAlmostEqual(cosine_similarity(vec_a, vec_b), 1.0, places=4)
        # Orthogonal vectors should have similarity 0.0
        self.assertAlmostEqual(cosine_similarity(vec_a, vec_c), 0.0, places=4)
