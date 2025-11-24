"""
Spatial Block-Based RAG with Comprehensive Debugging
Debug version with extensive logging and error handling
"""

import os
import io
import json
import hashlib
import re
import pickle
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime
from dataclasses import dataclass
from collections import defaultdict

import pdfplumber
from llama_index.core import (
    VectorStoreIndex,
    Document,
    StorageContext,
    load_index_from_storage,
    Settings
)
from llama_index.core.node_parser import SentenceSplitter
from llama_index.llms.azure_openai import AzureOpenAI
from llama_index.embeddings.azure_openai import AzureOpenAIEmbedding
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.postprocessor import SimilarityPostprocessor

try:
    import chromadb
    from llama_index.vector_stores.chroma import ChromaVectorStore
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False


@dataclass
class ContentBlock:
    """Represents a spatially-defined content block on a slide."""
    bbox: Tuple[float, float, float, float]
    text: str
    block_type: str
    page_number: int
    block_id: str
    table_data: Optional[List[List[str]]] = None
    entities: List[str] = None
    metrics: List[str] = None


class SpecialCharacterNormalizer:
    """Normalize financial special characters and acronyms."""
    
    NORMALIZATIONS = {
        'P&L': 'Profit and Loss (P&L)',
        'M&A': 'Mergers and Acquisitions (M&A)',
        'R&D': 'Research and Development (R&D)',
        'G&A': 'General and Administrative (G&A)',
        'YoY': 'Year-over-Year (YoY)',
        'QoQ': 'Quarter-over-Quarter (QoQ)',
        'MoM': 'Month-over-Month (MoM)',
        'EBITDA': 'EBITDA (Earnings Before Interest, Taxes, Depreciation, and Amortization)',
        'CAPEX': 'Capital Expenditure (CAPEX)',
        'OPEX': 'Operating Expense (OPEX)',
        'EPS': 'Earnings Per Share (EPS)',
        'ROI': 'Return on Investment (ROI)',
        'ROE': 'Return on Equity (ROE)',
        'ROA': 'Return on Assets (ROA)',
        'FCF': 'Free Cash Flow (FCF)',
        'CAGR': 'Compound Annual Growth Rate (CAGR)',
        'LTM': 'Last Twelve Months (LTM)',
        'NTM': 'Next Twelve Months (NTM)',
        'CoGS': 'Cost of Goods Sold (CoGS)',
        'SG&A': 'Selling, General and Administrative (SG&A)',
    }
    
    @classmethod
    def normalize(cls, text: str) -> str:
        """Normalize text by expanding financial abbreviations."""
        if not text:
            return text
        
        normalized = text
        replacements_made = []
        
        for abbrev, full_form in cls.NORMALIZATIONS.items():
            pattern = r'\b' + re.escape(abbrev) + r'\b'
            if re.search(pattern, text, re.IGNORECASE):
                normalized = re.sub(pattern, full_form, normalized, count=1, flags=re.IGNORECASE)
                replacements_made.append(abbrev)
        
        if replacements_made:
            print(f"      Normalized: {', '.join(replacements_made)}")
        
        return normalized
    
    @classmethod
    def extract_entities(cls, text: str) -> List[str]:
        """Extract entity references."""
        entities = []
        
        patterns = [
            r'\b([A-Z][a-z]+ (?:Division|Group|Segment|Unit|Business))\b',
            r'\b([A-Z][A-Z]+ (?:Division|Group|Segment))\b',
            r'\b((?:North|South|East|West) (?:America|Europe|Asia))\b',
            r'\b(EMEA|APAC|LATAM|NA|EU|AMER)\b',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            entities.extend(matches)
        
        return list(set(entities))
    
    @classmethod
    def extract_metrics(cls, text: str) -> List[str]:
        """Extract financial metrics mentioned."""
        metrics = []
        
        metric_keywords = [
            'revenue', 'sales', 'income', 'profit', 'loss', 'margin',
            'ebitda', 'cash flow', 'eps', 'growth', 'decline',
            'expenses', 'costs', 'assets', 'liabilities', 'equity'
        ]
        
        text_lower = text.lower()
        for metric in metric_keywords:
            if metric in text_lower:
                metrics.append(metric)
        
        return list(set(metrics))


class SpatialBlockExtractor:
    """Extract content blocks based on spatial layout."""
    
    def __init__(self, llm: Optional[AzureOpenAI] = None):
        self.llm = llm
        self.normalizer = SpecialCharacterNormalizer()
    
    def extract_blocks_from_page(
        self,
        page,
        page_number: int,
        debug: bool = True
    ) -> List[ContentBlock]:
        """Extract content blocks from page with detailed logging."""
        
        if debug:
            print(f"\n    === Page {page_number} Extraction ===")
        
        blocks = []
        
        # Try multiple extraction strategies
        words = self._extract_words_safely(page, debug)
        
        if not words:
            print(f"    ⚠ WARNING: No words extracted from page {page_number}")
            # Try fallback: extract text without words
            text = page.extract_text()
            if text:
                print(f"    ℹ Fallback: Using full text extraction ({len(text)} chars)")
                block = ContentBlock(
                    bbox=(0, 0, page.width, page.height),
                    text=text,
                    block_type='text',
                    page_number=page_number,
                    block_id=f"p{page_number}_fulltext"
                )
                blocks.append(block)
                return blocks
            else:
                print(f"    ✗ ERROR: Could not extract any text from page {page_number}")
                return []
        
        if debug:
            print(f"    ✓ Extracted {len(words)} words")
        
        # Extract tables
        tables = page.extract_tables()
        if debug:
            print(f"    ✓ Found {len(tables)} tables")
        
        # Cluster words into blocks
        text_blocks = self._cluster_words_into_blocks(words, page_number, debug)
        
        if debug:
            print(f"    ✓ Created {len(text_blocks)} text blocks")
        
        # Add text blocks
        blocks.extend(text_blocks)
        
        # Add table blocks
        for i, table in enumerate(tables):
            if table and len(table) > 1:
                table_text = self._table_to_text(table)
                
                # Estimate table position (fallback if bbox not available)
                bbox = (0, 0, page.width, page.height / 2)
                
                block = ContentBlock(
                    bbox=bbox,
                    text=table_text,
                    block_type='table',
                    page_number=page_number,
                    block_id=f"p{page_number}_table{i}",
                    table_data=table
                )
                blocks.append(block)
                
                if debug:
                    print(f"    ✓ Table {i}: {len(table)} rows, {len(table[0])} columns")
        
        # Classify blocks
        blocks = self._classify_blocks(blocks)
        
        # Extract entities and metrics
        for block in blocks:
            block.entities = self.normalizer.extract_entities(block.text)
            block.metrics = self.normalizer.extract_metrics(block.text)
        
        if debug:
            print(f"    📊 Block Summary:")
            type_counts = defaultdict(int)
            for b in blocks:
                type_counts[b.block_type] += 1
            for btype, count in type_counts.items():
                print(f"      - {btype}: {count}")
        
        return blocks
    
    def _extract_words_safely(self, page, debug: bool) -> List[Dict]:
        """Try multiple strategies to extract words."""
        
        # Strategy 1: Standard extraction
        try:
            words = page.extract_words(x_tolerance=3, y_tolerance=3)
            if words and len(words) > 0:
                if debug:
                    print(f"    ✓ Strategy 1 (standard): {len(words)} words")
                return words
        except Exception as e:
            if debug:
                print(f"    ⚠ Strategy 1 failed: {e}")
        
        # Strategy 2: More tolerant
        try:
            words = page.extract_words(x_tolerance=5, y_tolerance=5)
            if words and len(words) > 0:
                if debug:
                    print(f"    ✓ Strategy 2 (tolerant): {len(words)} words")
                return words
        except Exception as e:
            if debug:
                print(f"    ⚠ Strategy 2 failed: {e}")
        
        # Strategy 3: Very tolerant
        try:
            words = page.extract_words(x_tolerance=10, y_tolerance=10, keep_blank_chars=False)
            if words and len(words) > 0:
                if debug:
                    print(f"    ✓ Strategy 3 (very tolerant): {len(words)} words")
                return words
        except Exception as e:
            if debug:
                print(f"    ⚠ Strategy 3 failed: {e}")
        
        return []
    
    def _cluster_words_into_blocks(
        self,
        words: List[Dict],
        page_number: int,
        debug: bool = False
    ) -> List[ContentBlock]:
        """Cluster words into blocks based on spatial proximity."""
        
        if not words:
            return []
        
        vertical_threshold = 15
        
        # Group by vertical position
        lines = defaultdict(list)
        for word in words:
            y_key = round(word['top'] / vertical_threshold) * vertical_threshold
            lines[y_key].append(word)
        
        sorted_lines = sorted(lines.items(), key=lambda x: x[0])
        
        # Group lines into blocks
        blocks = []
        current_block_words = []
        current_y_range = None
        
        for y_pos, line_words in sorted_lines:
            if current_y_range is None:
                current_y_range = [y_pos, y_pos]
                current_block_words = line_words
            elif y_pos - current_y_range[1] <= vertical_threshold * 2:
                current_y_range[1] = y_pos
                current_block_words.extend(line_words)
            else:
                if current_block_words:
                    block = self._words_to_block(current_block_words, page_number, len(blocks))
                    blocks.append(block)
                current_y_range = [y_pos, y_pos]
                current_block_words = line_words
        
        if current_block_words:
            block = self._words_to_block(current_block_words, page_number, len(blocks))
            blocks.append(block)
        
        # Filter out very small blocks
        blocks = [b for b in blocks if len(b.text.strip()) > 5]
        
        return blocks
    
    def _words_to_block(
        self,
        words: List[Dict],
        page_number: int,
        block_index: int
    ) -> ContentBlock:
        """Convert words to ContentBlock."""
        
        x0 = min(w['x0'] for w in words)
        y0 = min(w['top'] for w in words)
        x1 = max(w['x1'] for w in words)
        y1 = max(w['bottom'] for w in words)
        
        words_sorted = sorted(words, key=lambda w: (w['top'], w['x0']))
        text = ' '.join(w['text'] for w in words_sorted)
        
        return ContentBlock(
            bbox=(x0, y0, x1, y1),
            text=text,
            block_type='text',
            page_number=page_number,
            block_id=f"p{page_number}_block{block_index}"
        )
    
    def _classify_blocks(self, blocks: List[ContentBlock]) -> List[ContentBlock]:
        """Classify blocks as headers vs content."""
        
        for i, block in enumerate(blocks):
            if block.block_type == 'table':
                continue
            
            text = block.text.strip()
            is_short = len(text) < 100
            is_all_caps = text.isupper() and len(text) > 3
            word_count = len(text.split())
            
            if is_short and word_count <= 15 and is_all_caps:
                block.block_type = 'header'
        
        return blocks
    
    def _table_to_text(self, table: List[List[str]]) -> str:
        """Convert table to text."""
        if not table or len(table) < 2:
            return ""
        
        lines = []
        headers = [str(cell) if cell else "" for cell in table[0]]
        
        for row in table[1:]:
            cells = [str(cell) if cell else "" for cell in row]
            row_parts = []
            
            for header, value in zip(headers, cells):
                if header and value:
                    row_parts.append(f"{header}: {value}")
            
            if row_parts:
                lines.append(", ".join(row_parts))
        
        return "\n".join(lines)
    
    def create_enriched_documents(
        self,
        blocks: List[ContentBlock],
        pdf_path: str,
        file_metadata: Dict[str, Any],
        debug: bool = True
    ) -> List[Document]:
        """Create documents from blocks with context."""
        
        if debug:
            print(f"\n    === Creating Documents ===")
        
        documents = []
        block_contexts = self._build_block_hierarchy(blocks)
        
        for i, block in enumerate(blocks):
            # Skip tiny blocks
            if len(block.text.strip()) < 10:
                continue
            
            context = block_contexts.get(block.block_id, {})
            content_parts = []
            
            # Add hierarchical context
            if context.get('headers'):
                header_text = ' > '.join(context['headers'])
                content_parts.append(f"Section: {header_text}")
            
            # Normalize special characters
            normalized_text = self.normalizer.normalize(block.text)
            content_parts.append(normalized_text)
            
            # Add related blocks
            if context.get('related_blocks'):
                for related in context['related_blocks'][:2]:  # Max 2 related
                    content_parts.append(f"Related: {related[:200]}")
            
            full_content = "\n\n".join(content_parts)
            
            # Create metadata
            doc_metadata = {
                'file_name': Path(pdf_path).name,
                'page_number': block.page_number,
                'block_id': block.block_id,
                'block_type': block.block_type,
                'entities': block.entities or [],
                'metrics': block.metrics or [],
                'has_table': block.block_type == 'table',
                'section_headers': context.get('headers', []),
                **file_metadata
            }
            
            doc = Document(
                text=full_content,
                metadata=doc_metadata,
                excluded_llm_metadata_keys=['file_path'],
                excluded_embed_metadata_keys=['file_path']
            )
            
            documents.append(doc)
            
            if debug and i < 3:  # Print first 3 documents
                print(f"\n    Document {i+1}:")
                print(f"      Content: {full_content[:150]}...")
                print(f"      Metadata: {doc_metadata.get('block_type')}, "
                      f"Page {doc_metadata.get('page_number')}")
        
        if debug:
            print(f"\n    ✓ Created {len(documents)} documents from {len(blocks)} blocks")
        
        return documents
    
    def _build_block_hierarchy(self, blocks: List[ContentBlock]) -> Dict[str, Dict[str, Any]]:
        """Build hierarchical relationships between blocks."""
        
        hierarchy = {}
        current_headers = []
        
        for i, block in enumerate(blocks):
            context = {
                'headers': list(current_headers),
                'related_blocks': []
            }
            
            if block.block_type == 'header':
                current_headers.append(block.text.strip())
                current_headers = current_headers[-2:]
            
            # Find related blocks nearby
            for j in range(i + 1, min(i + 3, len(blocks))):
                other = blocks[j]
                if other.block_type != 'header':
                    context['related_blocks'].append(other.text)
                    break
            
            hierarchy[block.block_id] = context
        
        return hierarchy


class SpatialBlockRAG:
    """Complete RAG system with debugging."""
    
    def __init__(
        self,
        azure_endpoint: str,
        azure_api_key: str,
        azure_deployment_name: str,
        azure_embedding_deployment: str,
        persist_dir: str = "./storage",
        cache_dir: str = "./cache",
        use_vector_db: str = "local",
        api_version: str = "2024-02-15-preview",
        debug: bool = True
    ):
        """Initialize with debug mode."""
        
        self.persist_dir = persist_dir
        self.cache_dir = cache_dir
        self.use_vector_db = use_vector_db
        self.debug = debug
        
        os.makedirs(persist_dir, exist_ok=True)
        os.makedirs(cache_dir, exist_ok=True)
        
        print("\n" + "="*80)
        print("INITIALIZING SPATIAL BLOCK RAG")
        print("="*80)
        
        # Initialize LLM
        print("\n1. Initializing LLM...")
        try:
            self.llm = AzureOpenAI(
                model="gpt-4",
                deployment_name=azure_deployment_name,
                api_key=azure_api_key,
                azure_endpoint=azure_endpoint,
                api_version=api_version,
                temperature=0.1,
                max_tokens=1000
            )
            print("   ✓ LLM initialized")
        except Exception as e:
            print(f"   ✗ LLM initialization failed: {e}")
            raise
        
        # Initialize embeddings
        print("\n2. Initializing embeddings...")
        try:
            self.embed_model = AzureOpenAIEmbedding(
                model="text-embedding-3-large",
                deployment_name=azure_embedding_deployment,
                api_key=azure_api_key,
                azure_endpoint=azure_endpoint,
                api_version=api_version,
                embed_batch_size=100
            )
            print("   ✓ Embeddings initialized")
        except Exception as e:
            print(f"   ✗ Embedding initialization failed: {e}")
            raise
        
        Settings.llm = self.llm
        Settings.embed_model = self.embed_model
        Settings.chunk_size = 512
        Settings.chunk_overlap = 50
        
        print(f"\n3. Settings:")
        print(f"   - Chunk size: {Settings.chunk_size}")
        print(f"   - Chunk overlap: {Settings.chunk_overlap}")
        print(f"   - Vector DB: {use_vector_db}")
        
        self.block_extractor = SpatialBlockExtractor(llm=None)  # Disable LLM enrichment for speed
        
        self.index = None
        self.query_engine = None
        
        self.doc_registry_path = os.path.join(persist_dir, "doc_registry.json")
        self.doc_registry = self._load_doc_registry()
        
        self.query_cache = {}
        self.cache_file = os.path.join(cache_dir, "query_cache.pkl")
        self._load_query_cache()
        
        print("\n✓ Initialization complete")
    
    def _load_doc_registry(self) -> Dict:
        if os.path.exists(self.doc_registry_path):
            with open(self.doc_registry_path, 'r') as f:
                return json.load(f)
        return {}
    
    def _save_doc_registry(self):
        with open(self.doc_registry_path, 'w') as f:
            json.dump(self.doc_registry, f, indent=2)
    
    def _compute_file_hash(self, filepath: str) -> str:
        hash_md5 = hashlib.md5()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def save_index(self):
        """Save index with validation."""
        if not self.index:
            raise ValueError("No index to save")
        
        print(f"\n💾 Saving index to {self.persist_dir}...")
        
        try:
            if self.use_vector_db == "local":
                self.index.storage_context.persist(persist_dir=self.persist_dir)
            elif self.use_vector_db == "chroma":
                metadata = {
                    'index_type': 'chroma',
                    'created_at': datetime.now().isoformat()
                }
                with open(os.path.join(self.persist_dir, 'index_metadata.json'), 'w') as f:
                    json.dump(metadata, f)
            
            self._save_doc_registry()
            print(f"✓ Index saved successfully")
            print(f"  - Documents: {len(self.doc_registry)}")
            
        except Exception as e:
            print(f"✗ Error saving index: {e}")
            raise
    
    def load_index(self) -> bool:
        """Load index with validation."""
        try:
            print(f"\n📂 Loading index from {self.persist_dir}...")
            
            if self.use_vector_db == "local":
                storage_context = StorageContext.from_defaults(persist_dir=self.persist_dir)
                self.index = load_index_from_storage(storage_context)
            elif self.use_vector_db == "chroma":
                if not CHROMA_AVAILABLE:
                    raise ValueError("ChromaDB not installed")
                
                db = chromadb.PersistentClient(path=self.persist_dir)
                chroma_collection = db.get_or_create_collection("financial_blocks")
                vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
                self.index = VectorStoreIndex.from_vector_store(vector_store)
            
            self.doc_registry = self._load_doc_registry()
            
            print(f"✓ Index loaded successfully")
            print(f"  - Documents: {len(self.doc_registry)}")
            
            return True
            
        except Exception as e:
            print(f"✗ Could not load index: {e}")
            return False
    
    def load_and_process_pdfs(self, docs_path: str) -> List[Document]:
        """Load PDFs with detailed logging."""
        
        print("\n" + "="*80)
        print("PROCESSING PDFs")
        print("="*80)
        
        all_documents = []
        pdf_files = list(Path(docs_path).rglob("*.pdf"))
        
        if not pdf_files:
            print(f"\n✗ ERROR: No PDF files found in {docs_path}")
            return []
        
        print(f"\n✓ Found {len(pdf_files)} PDF files")
        
        for pdf_idx, pdf_path in enumerate(pdf_files, 1):
            pdf_path_str = str(pdf_path)
            filename = pdf_path.name
            
            print(f"\n{'='*80}")
            print(f"PDF {pdf_idx}/{len(pdf_files)}: {filename}")
            print(f"{'='*80}")
            
            try:
                # Extract file metadata
                file_metadata = self._extract_file_metadata(filename)
                print(f"  Metadata: {file_metadata}")
                
                # Extract blocks
                all_blocks = []
                
                with pdfplumber.open(pdf_path_str) as pdf:
                    print(f"  Total pages: {len(pdf.pages)}")
                    
                    for page_num, page in enumerate(pdf.pages, start=1):
                        print(f"\n  📄 Processing page {page_num}/{len(pdf.pages)}...")
                        
                        blocks = self.block_extractor.extract_blocks_from_page(
                            page, page_num, debug=self.debug
                        )
                        all_blocks.extend(blocks)
                        
                        print(f"    ✓ Page {page_num}: {len(blocks)} blocks extracted")
                
                print(f"\n  📊 Total blocks from {filename}: {len(all_blocks)}")
                
                if len(all_blocks) == 0:
                    print(f"  ⚠ WARNING: No blocks extracted from {filename}")
                    continue
                
                # Create documents
                documents = self.block_extractor.create_enriched_documents(
                    all_blocks, pdf_path_str, file_metadata, debug=self.debug
                )
                
                if len(documents) == 0:
                    print(f"  ⚠ WARNING: No documents created from {filename}")
                    continue
                
                all_documents.extend(documents)
                
                # Update registry
                file_hash = self._compute_file_hash(pdf_path_str)
                self.doc_registry[pdf_path_str] = {
                    'hash': file_hash,
                    'indexed_at': datetime.now().isoformat(),
                    'num_blocks': len(all_blocks),
                    'num_documents': len(documents),
                    'metadata': file_metadata
                }
                
                print(f"\n  ✓ SUCCESS: {len(documents)} documents created from {filename}")
                
            except Exception as e:
                print(f"\n  ✗ ERROR processing {filename}: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        print(f"\n{'='*80}")
        print(f"PROCESSING COMPLETE")
        print(f"{'='*80}")
        print(f"✓ Total documents created: {len(all_documents)}")
        print(f"✓ Total files processed: {len(self.doc_registry)}")
        
        if len(all_documents) == 0:
            print("\n✗ ERROR: No documents were created!")
            print("  Possible issues:")
            print("  - PDFs may be scanned images (not text)")
            print("  - PDF format not compatible with pdfplumber")
            print("  - Text extraction settings need adjustment")
        
        return all_documents
    
    def _extract_file_metadata(self, filename: str) -> Dict[str, Any]:
        """Extract metadata from filename."""
        metadata = {}
        
        quarter_match = re.search(r'Q([1-4])', filename, re.IGNORECASE)
        year_match = re.search(r'(20\d{2})', filename)
        
        if quarter_match:
            metadata['quarter'] = f"Q{quarter_match.group(1)}"
        if year_match:
            metadata['year'] = year_match.group(1)
        
        if 'quarter' in metadata and 'year' in metadata:
            quarter_end = {'Q1': '03-31', 'Q2': '06-30', 'Q3': '09-30', 'Q4': '12-31'}
            month_day = quarter_end.get(metadata['quarter'])
            metadata['date'] = f"{metadata['year']}-{month_day}"
            metadata['quarter_year'] = f"{metadata['quarter']} {metadata['year']}"
        
        return metadata
    
    def create_initial_index(self, docs_path: str):
        """Create index with validation."""
        
        print("\n" + "="*80)
        print("CREATING INITIAL INDEX")
        print("="*80)
        
        # Load documents
        documents = self.load_and_process_pdfs(docs_path)
        
        if not documents:
            print("\n✗ ERROR: No documents to index!")
            return
        
        print(f"\n📝 Creating vector index from {len(documents)} documents...")
        print("   (This may take several minutes...)")
        
        try:
            self._create_index(documents)
            print("✓ Index created successfully")
            
            # Save
            self.save_index()
            
            # Validate
            self._validate_index()
            
        except Exception as e:
            print(f"\n✗ ERROR creating index: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def _create_index(self, documents: List[Document]):
        """Create index."""
        
        node_parser = SentenceSplitter(
            chunk_size=Settings.chunk_size,
            chunk_overlap=Settings.chunk_overlap
        )
        
        if self.use_vector_db == "local":
            self.index = VectorStoreIndex.from_documents(
                documents,
                transformations=[node_parser],
                show_progress=True
            )
        elif self.use_vector_db == "chroma":
            if not CHROMA_AVAILABLE:
                raise ValueError("ChromaDB not installed")
            
            db = chromadb.PersistentClient(path=self.persist_dir)
            chroma_collection = db.get_or_create_collection("financial_blocks")
            vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
            storage_context = StorageContext.from_defaults(vector_store=vector_store)
            
            self.index = VectorStoreIndex.from_documents(
                documents,
                storage_context=storage_context,
                transformations=[node_parser],
                show_progress=True
            )
    
    def _validate_index(self):
        """Validate index after creation."""
        
        print("\n🔍 Validating index...")
        
        if not self.index:
            print("  ✗ Index is None!")
            return
        
        try:
            # Try a simple retrieval
            retriever = VectorIndexRetriever(index=self.index, similarity_top_k=3)
            nodes = retriever.retrieve("revenue")
            
            print(f"  ✓ Index is queryable")
            print(f"  ✓ Test retrieval returned {len(nodes)} nodes")
            
            if nodes:
                print(f"  ✓ Sample node score: {nodes[0].score:.3f}")
            
        except Exception as e:
            print(f"  ✗ Index validation failed: {e}")
    
    def create_query_engine(
        self,
        similarity_top_k: int = 7,
        similarity_cutoff: float = 0.6
    ):
        """Create query engine with validation."""
        
        print("\n" + "="*80)
        print("CREATING QUERY ENGINE")
        print("="*80)
        
        if not self.index:
            print("✗ ERROR: No index available. Create or load index first!")
            raise ValueError("Index not created or loaded")
        
        print(f"  Settings:")
        print(f"    - Top K: {similarity_top_k}")
        print(f"    - Similarity cutoff: {similarity_cutoff}")
        
        try:
            retriever = VectorIndexRetriever(
                index=self.index,
                similarity_top_k=similarity_top_k
            )
            
            self.query_engine = RetrieverQueryEngine(
                retriever=retriever,
                node_postprocessors=[
                    SimilarityPostprocessor(similarity_cutoff=similarity_cutoff)
                ]
            )
            
            print("✓ Query engine created successfully")
            
        except Exception as e:
            print(f"✗ ERROR creating query engine: {e}")
            raise
    
    def query(
        self,
        query: str,
        use_cache: bool = True,
        debug: bool = True
    ) -> str:
        """Query with detailed debugging."""
        
        if not self.query_engine:
            print("\n⚠ Query engine not created. Creating now...")
            self.create_query_engine()
        
        if debug:
            print("\n" + "="*80)
            print(f"QUERY: {query}")
            print("="*80)
        
        # Check cache
        cache_key = hashlib.md5(query.encode()).hexdigest()
        
        if use_cache and cache_key in self.query_cache:
            cached = self.query_cache[cache_key]
            age = datetime.now() - datetime.fromisoformat(cached['timestamp'])
            if age.total_seconds() / 3600 < 24:
                if debug:
                    print("✓ Using cached result")
                return cached['response']
        
        try:
            if debug:
                print("\n🔍 Retrieving relevant chunks...")
            
            # Execute query
            response = self.query_engine.query(query)
            
            if debug:
                print(f"\n📊 Retrieved {len(response.source_nodes)} source nodes")
                for i, node in enumerate(response.source_nodes[:3], 1):
                    print(f"\n  Node {i}:")
                    print(f"    Score: {node.score:.3f}")
                    print(f"    Content: {node.text[:200]}...")
                    print(f"    Metadata: {node.metadata.get('block_type')}, "
                          f"Page {node.metadata.get('page_number')}")
            
            response_str = str(response)
            
            if debug:
                print(f"\n💬 Response ({len(response_str)} chars):")
                print(f"    {response_str[:300]}...")
            
            # Cache
            if use_cache:
                self.query_cache[cache_key] = {
                    'response': response_str,
                    'timestamp': datetime.now().isoformat()
                }
                self._save_query_cache()
            
            return response_str
            
        except Exception as e:
            print(f"\n✗ ERROR during query: {e}")
            import traceback
            traceback.print_exc()
            return f"Error: {str(e)}"
    
    def _load_query_cache(self):
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'rb') as f:
                    self.query_cache = pickle.load(f)
                print(f"  ✓ Loaded {len(self.query_cache)} cached queries")
            except:
                self.query_cache = {}
    
    def _save_query_cache(self):
        with open(self.cache_file, 'wb') as f:
            pickle.dump(self.query_cache, f)


def main():
    """Demo with comprehensive debugging."""
    from dotenv import load_dotenv
    load_dotenv()
    
    print("\n" + "="*80)
    print("SPATIAL BLOCK RAG - DEBUG MODE")
    print("="*80)
    
    # Validate environment
    if not os.getenv("AZURE_OPENAI_ENDPOINT"):
        print("\n✗ ERROR: AZURE_OPENAI_ENDPOINT not set in environment")
        print("  Please create .env file with Azure credentials")
        return
    
    rag = SpatialBlockRAG(
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        azure_api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        azure_deployment_name=os.getenv("AZURE_DEPLOYMENT_NAME", "gpt-4"),
        azure_embedding_deployment=os.getenv("AZURE_EMBEDDING_DEPLOYMENT", "text-embedding-3-large"),
        use_vector_db="local",  # Use local for easier debugging
        debug=True
    )
    
    # Try to load existing index
    if not rag.load_index():
        print("\n📁 No existing index found. Creating new index...")
        rag.create_initial_index("./financial_docs")
    
    # Create query engine
    rag.create_query_engine(similarity_top_k=5, similarity_cutoff=0.5)
    
    # Test queries
    print("\n" + "="*80)
    print("TEST QUERIES")
    print("="*80)
    
    test_queries = [
        "What was the revenue?",
        "Show me P&L summary",
        "What are the key metrics?"
    ]
    
    for query in test_queries:
        print(f"\n{'='*80}")
        response = rag.query(query, debug=True)
        print(f"\n✓ Query complete")


if __name__ == "__main__":
    main()
