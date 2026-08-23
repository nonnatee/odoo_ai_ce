# -*- coding: utf-8 -*-
import base64
import hashlib
import io
import math
import re

def chunk_text(text, chunk_size=1000, overlap=150):
    """
    Split text into overlapping chunks preserving sentence/paragraph boundaries.
    """
    if not text:
        return []
    
    paragraphs = re.split(r'\n\s*\n', text)
    chunks = []
    current_chunk = []
    current_length = 0
    
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        para_len = len(para)
        
        if current_length + para_len > chunk_size and current_chunk:
            combined = "\n\n".join(current_chunk)
            chunks.append(combined)
            # Keep tail for overlap
            overlap_text = combined[-overlap:] if len(combined) > overlap else combined
            current_chunk = [overlap_text, para]
            current_length = len(overlap_text) + para_len
        else:
            current_chunk.append(para)
            current_length += para_len
            
    if current_chunk:
        chunks.append("\n\n".join(current_chunk))
        
    return chunks

def extract_text_from_attachment(attachment):
    """
    Extract readable text from an ir.attachment record.
    """
    if not attachment.datas:
        return ""
    
    try:
        raw_bytes = base64.b64decode(attachment.datas)
        mimetype = attachment.mimetype or ""
        
        if "text" in mimetype or "markdown" in mimetype or "json" in mimetype:
            return raw_bytes.decode('utf-8', errors='replace')
        elif "pdf" in mimetype:
            # Basic PDF text stream extraction
            text_chunks = []
            for stream in re.findall(rb'stream[\r\n]+(.*?)[\r\n]+endstream', raw_bytes, re.DOTALL):
                try:
                    import zlib
                    decompressed = zlib.decompress(stream)
                    clean = re.sub(r'[^a-zA-Z0-9\s.,!?;:()\-\'\"]', '', decompressed.decode('latin-1', errors='ignore'))
                    if len(clean.strip()) > 20:
                        text_chunks.append(clean)
                except Exception:
                    pass
            if text_chunks:
                return "\n".join(text_chunks)
            return raw_bytes.decode('latin-1', errors='ignore')
        else:
            return raw_bytes.decode('utf-8', errors='ignore')
    except Exception:
        return ""

def compute_checksum(text):
    """Compute MD5 checksum for a text string."""
    return hashlib.md5(text.encode('utf-8')).hexdigest()

def cosine_similarity(vec_a, vec_b):
    """Compute cosine similarity between two float vectors."""
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.0
    dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot_product / (norm_a * norm_b)
