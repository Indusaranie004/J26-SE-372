import os

TOP_K = int(os.getenv('TOP_K', 100))
RRF_K = int(os.getenv('RRF_K', 60))
CHROMA_HOST = os.getenv('CHROMA_HOST', 'localhost')
CHROMA_PORT = int(os.getenv('CHROMA_PORT', 8000))
COLLECTION = os.getenv('CHROMA_COLLECTION', 'legal_bge_m3')
CORPUS_PATH = os.getenv('CORPUS_PATH', 'component-b/data/mock_corpus.json')
GT1_PATH = os.getenv('GT1_PATH', 'component-b/data/mock_gt1.json')