import os
from dotenv import load_dotenv
load_dotenv()

TOP_K                          = int(os.getenv("TOP_K",                          100))
RRF_K                          = int(os.getenv("RRF_K",                          60))
CHROMA_HOST                    = os.getenv("CHROMA_HOST",                         "localhost")
CHROMA_PORT                    = int(os.getenv("CHROMA_PORT",                    "8000"))
COLLECTION_GENERIC             = os.getenv("COLLECTION_GENERIC",                  "legal_bge_m3_generic")
COLLECTION_BGEM3_FINETUNED     = os.getenv("COLLECTION_BGEM3_FINETUNED",          "legal_bge_m3_finetuned")
COLLECTION_ANGLEBERT_FINETUNED = os.getenv("COLLECTION_ANGLEBERT_FINETUNED",      "legal_anglebert_finetuned")
CORPUS_PATH                    = os.getenv("CORPUS_PATH",                         "data/mock_corpus.json")
GT1_PATH                       = os.getenv("GT1_PATH",                            "data/mock_gt1.json")
ANGLEBERT_CKPT                 = os.getenv("ANGLEBERT_CKPT",                      "")
BGE_FT_CKPT                    = os.getenv("BGE_FT_CKPT",                         "")

NEO4J_USE_MOCK = os.getenv("NEO4J_USE_MOCK", "true").lower() != "false"