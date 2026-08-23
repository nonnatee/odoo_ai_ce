# -*- coding: utf-8 -*-
import json
import logging
from odoo import models, fields, api
from ..tools.extractor import chunk_text, extract_text_from_attachment, compute_checksum, cosine_similarity

_logger = logging.getLogger(__name__)

class AiCeVectorChunk(models.Model):
    _name = "ai_ce.vector.chunk"
    _description = "Semantic Knowledge Vector Chunk"
    _order = "res_model asc, res_id asc, chunk_index asc"

    res_model = fields.Char(string="Source Model", required=True, index=True)
    res_id = fields.Integer(string="Source Record ID", required=True, index=True)
    chunk_index = fields.Integer(string="Chunk Index", default=0)
    
    content_text = fields.Text(string="Chunk Text Content", required=True)
    embedding_json = fields.Text(string="Embedding Vector (JSON Float Array)")
    checksum = fields.Char(string="MD5 Checksum", index=True)
    
    create_date = fields.Datetime(string="Indexed On", readonly=True)

    @api.model
    def index_record(self, res_model, res_id, text_content, provider=None):
        """Chunk and index text content with vector embeddings."""
        if not text_content or len(text_content.strip()) < 20:
            return 0
            
        prov = provider or self.env['ai_ce.provider'].search([('active', '=', True)], order='priority asc', limit=1)
        if not prov:
            return 0
            
        chunks = chunk_text(text_content, chunk_size=800, overlap=100)
        indexed_count = 0
        
        # Remove existing stale chunks
        self.search([('res_model', '=', res_model), ('res_id', '=', res_id)]).unlink()
        
        for idx, chunk in enumerate(chunks):
            embedding = prov.get_embedding(chunk)
            self.create({
                'res_model': res_model,
                'res_id': res_id,
                'chunk_index': idx,
                'content_text': chunk,
                'embedding_json': json.dumps(embedding) if embedding else "[]",
                'checksum': compute_checksum(chunk)
            })
            indexed_count += 1
            
        return indexed_count

    @api.model
    def search_similar(self, query_text, provider=None, limit=3, min_similarity=0.3):
        """
        Perform semantic similarity retrieval for a given query string.
        """
        prov = provider or self.env['ai_ce.provider'].search([('active', '=', True)], order='priority asc', limit=1)
        if not prov:
            return []
            
        query_vector = prov.get_embedding(query_text)
        if not query_vector:
            return []
            
        all_chunks = self.search([], limit=500)
        scored = []
        
        for chk in all_chunks:
            if not chk.embedding_json or chk.embedding_json == "[]":
                continue
            try:
                vec = json.loads(chk.embedding_json)
                score = cosine_similarity(query_vector, vec)
                if score >= min_similarity:
                    scored.append({
                        "id": chk.id,
                        "res_model": chk.res_model,
                        "res_id": chk.res_id,
                        "text": chk.content_text,
                        "score": score
                    })
            except Exception:
                continue
                
        scored.sort(key=lambda x: x['score'], reverse=True)
        return scored[:limit]
