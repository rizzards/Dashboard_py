"""
Advanced Query Optimizer 

Handles:
1. Multi-division queries: "What is P&L in Q4 2024?" → Gets ALL divisions
2. Multi-date queries: "Compare Q3 and Q4 2024" → Gets both quarters
3. Specific queries: "Tech division P&L Q4 2024" → Precise results
4. Comprehensive queries: "P&L across all divisions for Q3 and Q4" → Complete coverage

Strategy:
- Query decomposition: Break complex queries into entity-specific sub-queries
- Metadata-aware retrieval: Use filters to ensure coverage
- Hierarchical aggregation: Combine results intelligently
- Entity detection: Automatically identify divisions and dates in query
"""

import re
from typing import List, Dict, Any, Set, Tuple, Optional
from dataclasses import dataclass
from collections import defaultdict
from llama_index.core import VectorStoreIndex, QueryBundle
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.schema import NodeWithScore


@dataclass
class QueryEntity:
    """Represents an entity mentioned in the query."""
    entity_type: str  # 'division', 'quarter', 'year', 'metric', 'topic'
    value: str
    normalized: str


class EntityExtractor:
    """Extract entities (divisions, dates, metrics) from queries."""
    
    # Known business divisions
    DIVISIONS = {
        'technology', 'tech', 'healthcare', 'health', 'retail', 
        'finance', 'financial services', 'operations', 'ops',
        'manufacturing', 'sales', 'marketing', 'corporate'
    }
    
    # Financial metrics
    METRICS = {
        'p&l', 'profit and loss', 'pl', 'revenue', 'sales', 'income',
        'ebitda', 'margin', 'cash flow', 'expenses', 'costs',
        'profit', 'loss', 'earnings', 'balance sheet'
    }
    
    # Topics
    TOPICS = {
        'performance', 'highlights', 'summary', 'overview',
        'analysis', 'trends', 'growth', 'decline'
    }
    
    @classmethod
    def extract_entities(cls, query: str) -> Dict[str, List[QueryEntity]]:
        """
        Extract all entities from query.
        
        Returns:
            {
                'divisions': [QueryEntity(...)],
                'quarters': [QueryEntity(...)],
                'years': [QueryEntity(...)],
                'metrics': [QueryEntity(...)],
                'topics': [QueryEntity(...)]
            }
        """
        query_lower = query.lower()
        entities = defaultdict(list)
        
        # Extract divisions
        for division in cls.DIVISIONS:
            pattern = r'\b' + re.escape(division) + r'\b'
            if re.search(pattern, query_lower):
                entities['divisions'].append(QueryEntity(
                    entity_type='division',
                    value=division,
                    normalized=cls._normalize_division(division)
                ))
        
        # Extract quarters
        quarter_patterns = [
            (r'\bQ([1-4])\b', lambda m: f"Q{m.group(1)}"),
            (r'\b([1-4])st\s+quarter\b', lambda m: f"Q{m.group(1)}"),
            (r'\b([1-4])nd\s+quarter\b', lambda m: f"Q{m.group(1)}"),
            (r'\b([1-4])rd\s+quarter\b', lambda m: f"Q{m.group(1)}"),
            (r'\b([1-4])th\s+quarter\b', lambda m: f"Q{m.group(1)}"),
        ]
        
        for pattern, formatter in quarter_patterns:
            for match in re.finditer(pattern, query_lower):
                quarter = formatter(match)
                entities['quarters'].append(QueryEntity(
                    entity_type='quarter',
                    value=quarter,
                    normalized=quarter
                ))
        
        # Extract years
        year_pattern = r'\b(20\d{2})\b'
        for match in re.finditer(year_pattern, query):
            year = match.group(1)
            entities['years'].append(QueryEntity(
                entity_type='year',
                value=year,
                normalized=year
            ))
        
        # Extract metrics
        for metric in cls.METRICS:
            pattern = r'\b' + re.escape(metric) + r'\b'
            if re.search(pattern, query_lower):
                entities['metrics'].append(QueryEntity(
                    entity_type='metric',
                    value=metric,
                    normalized=cls._normalize_metric(metric)
                ))
        
        # Extract topics
        for topic in cls.TOPICS:
            pattern = r'\b' + re.escape(topic) + r'\b'
            if re.search(pattern, query_lower):
                entities['topics'].append(QueryEntity(
                    entity_type='topic',
                    value=topic,
                    normalized=topic
                ))
        
        # Remove duplicates
        for key in entities:
            seen = set()
            unique = []
            for entity in entities[key]:
                if entity.normalized not in seen:
                    seen.add(entity.normalized)
                    unique.append(entity)
            entities[key] = unique
        
        return dict(entities)
    
    @classmethod
    def _normalize_division(cls, division: str) -> str:
        """Normalize division names."""
        mapping = {
            'tech': 'Technology',
            'technology': 'Technology',
            'health': 'Healthcare',
            'healthcare': 'Healthcare',
            'retail': 'Retail',
            'finance': 'Finance',
            'financial services': 'Finance',
            'ops': 'Operations',
            'operations': 'Operations',
        }
        return mapping.get(division.lower(), division.title())
    
    @classmethod
    def _normalize_metric(cls, metric: str) -> str:
        """Normalize metric names."""
        mapping = {
            'p&l': 'profit_and_loss',
            'profit and loss': 'profit_and_loss',
            'pl': 'profit_and_loss',
            'revenue': 'revenue',
            'sales': 'revenue',
            'ebitda': 'ebitda',
            'margin': 'margin',
            'cash flow': 'cash_flow',
        }
        return mapping.get(metric.lower(), metric.lower())
    
    @classmethod
    def detect_query_type(cls, entities: Dict[str, List[QueryEntity]]) -> str:
        """
        Detect query type based on entities.
        
        Returns:
            - 'general': No specific division/date
            - 'specific': Specific division AND date
            - 'multi_division': Multiple divisions OR no division specified
            - 'multi_date': Multiple dates
            - 'comprehensive': Multiple divisions AND dates
        """
        num_divisions = len(entities.get('divisions', []))
        num_quarters = len(entities.get('quarters', []))
        num_years = len(entities.get('years', []))
        
        has_date = num_quarters > 0 or num_years > 0
        multi_date = num_quarters > 1 or (num_quarters > 0 and num_years > 1)
        
        if num_divisions == 1 and has_date and not multi_date:
            return 'specific'
        elif num_divisions == 0 and has_date:
            return 'multi_division'  # Should get ALL divisions
        elif multi_date:
            if num_divisions <= 1:
                return 'multi_date_multi_division'  # All divisions, multiple dates
            else:
                return 'comprehensive'  # Multiple specific divisions and dates
        elif num_divisions > 1:
            return 'multi_division'
        else:
            return 'general'


class EntityAwareRetriever:
    """
    Retriever that ensures coverage across entities.
    Handles multi-division and multi-date queries intelligently.
    """
    
    def __init__(
        self,
        index: VectorStoreIndex,
        base_top_k: int = 5,
        entities_per_query: int = 3,
        debug: bool = True
    ):
        """
        Args:
            index: VectorStoreIndex to retrieve from
            base_top_k: Base number of results per entity combination
            entities_per_query: How many results per entity (division/date combo)
            debug: Print debug information
        """
        self.index = index
        self.base_top_k = base_top_k
        self.entities_per_query = entities_per_query
        self.debug = debug
        self.entity_extractor = EntityExtractor()
    
    def retrieve(self, query: str) -> List[NodeWithScore]:
        """
        Retrieve with entity awareness.
        Ensures coverage across all relevant divisions and dates.
        """
        
        if self.debug:
            print(f"\n{'='*80}")
            print(f"ENTITY-AWARE RETRIEVAL")
            print(f"{'='*80}")
            print(f"Query: {query}")
        
        # Extract entities from query
        entities = self.entity_extractor.extract_entities(query)
        query_type = self.entity_extractor.detect_query_type(entities)
        
        if self.debug:
            print(f"\nDetected Query Type: {query_type}")
            print(f"\nExtracted Entities:")
            for entity_type, entity_list in entities.items():
                if entity_list:
                    values = [e.normalized for e in entity_list]
                    print(f"  {entity_type}: {values}")
        
        # Route to appropriate retrieval strategy
        if query_type == 'specific':
            return self._retrieve_specific(query, entities)
        
        elif query_type == 'multi_division':
            return self._retrieve_multi_division(query, entities)
        
        elif query_type == 'multi_date_multi_division':
            return self._retrieve_multi_date_multi_division(query, entities)
        
        elif query_type == 'comprehensive':
            return self._retrieve_comprehensive(query, entities)
        
        else:  # general
            return self._retrieve_general(query)
    
    def _retrieve_specific(
        self,
        query: str,
        entities: Dict[str, List[QueryEntity]]
    ) -> List[NodeWithScore]:
        """
        Retrieve for specific division + date.
        Example: "Tech division P&L in Q4 2024"
        """
        
        if self.debug:
            print(f"\n→ Strategy: SPECIFIC retrieval")
        
        division = entities['divisions'][0].normalized
        
        # Build quarter-year filter
        quarters = [e.value for e in entities.get('quarters', [])]
        years = [e.value for e in entities.get('years', [])]
        
        if self.debug:
            print(f"  Target: {division}, {quarters}, {years}")
        
        # Retrieve with metadata filter
        nodes = self._retrieve_with_metadata(
            query=query,
            division=division,
            quarters=quarters,
            years=years,
            top_k=self.base_top_k * 2  # Get more for specific queries
        )
        
        if self.debug:
            print(f"  Retrieved: {len(nodes)} nodes")
        
        return nodes
    
    def _retrieve_multi_division(
        self,
        query: str,
        entities: Dict[str, List[QueryEntity]]
    ) -> List[NodeWithScore]:
        """
        Retrieve across ALL divisions for given date.
        Example: "What is P&L in Q4 2024?" → Get ALL divisions
        """
        
        if self.debug:
            print(f"\n→ Strategy: MULTI-DIVISION retrieval")
            print(f"  Goal: Get results from ALL divisions")
        
        quarters = [e.value for e in entities.get('quarters', [])]
        years = [e.value for e in entities.get('years', [])]
        
        # Get all divisions from index
        all_divisions = self._get_all_divisions_from_index()
        
        if not all_divisions:
            # Fallback: Known divisions
            all_divisions = ['Technology', 'Healthcare', 'Retail', 'Finance', 'Operations']
        
        if self.debug:
            print(f"  Divisions to query: {all_divisions}")
            print(f"  Date filter: Q{quarters} {years}")
        
        # Retrieve separately for each division
        all_nodes = []
        for division in all_divisions:
            if self.debug:
                print(f"\n  Querying {division}...")
            
            nodes = self._retrieve_with_metadata(
                query=query,
                division=division,
                quarters=quarters,
                years=years,
                top_k=self.entities_per_query  # e.g., 3 per division
            )
            
            if self.debug:
                print(f"    → Retrieved {len(nodes)} nodes")
            
            all_nodes.extend(nodes)
        
        # Deduplicate and re-rank
        all_nodes = self._deduplicate_nodes(all_nodes)
        all_nodes = sorted(all_nodes, key=lambda n: n.score, reverse=True)
        
        if self.debug:
            print(f"\n  Total after deduplication: {len(all_nodes)} nodes")
            print(f"  Coverage: {self._check_division_coverage(all_nodes)}")
        
        return all_nodes
    
    def _retrieve_multi_date_multi_division(
        self,
        query: str,
        entities: Dict[str, List[QueryEntity]]
    ) -> List[NodeWithScore]:
        """
        Retrieve across multiple dates AND all divisions.
        Example: "Compare P&L for Q3 and Q4 2024 across all divisions"
        """
        
        if self.debug:
            print(f"\n→ Strategy: MULTI-DATE + MULTI-DIVISION retrieval")
        
        quarters = [e.value for e in entities.get('quarters', [])]
        years = [e.value for e in entities.get('years', [])]
        all_divisions = self._get_all_divisions_from_index()
        
        if not all_divisions:
            all_divisions = ['Technology', 'Healthcare', 'Retail', 'Finance', 'Operations']
        
        if self.debug:
            print(f"  Divisions: {all_divisions}")
            print(f"  Quarters: {quarters}")
            print(f"  Years: {years}")
        
        # Retrieve for each (division, date) combination
        all_nodes = []
        
        for division in all_divisions:
            for quarter in quarters if quarters else [None]:
                for year in years if years else [None]:
                    
                    if self.debug:
                        date_str = f"{quarter} {year}" if quarter and year else "any date"
                        print(f"\n  Querying {division} - {date_str}...")
                    
                    nodes = self._retrieve_with_metadata(
                        query=query,
                        division=division,
                        quarters=[quarter] if quarter else [],
                        years=[year] if year else [],
                        top_k=self.entities_per_query  # Small per combination
                    )
                    
                    if self.debug:
                        print(f"    → Retrieved {len(nodes)} nodes")
                    
                    all_nodes.extend(nodes)
        
        # Deduplicate and re-rank
        all_nodes = self._deduplicate_nodes(all_nodes)
        all_nodes = sorted(all_nodes, key=lambda n: n.score, reverse=True)
        
        if self.debug:
            print(f"\n  Total: {len(all_nodes)} nodes")
            print(f"  Coverage:")
            print(f"    Divisions: {self._check_division_coverage(all_nodes)}")
            print(f"    Dates: {self._check_date_coverage(all_nodes)}")
        
        return all_nodes
    
    def _retrieve_comprehensive(
        self,
        query: str,
        entities: Dict[str, List[QueryEntity]]
    ) -> List[NodeWithScore]:
        """
        Retrieve for specific divisions across multiple dates.
        Example: "Tech and Healthcare P&L for Q3 and Q4 2024"
        """
        
        if self.debug:
            print(f"\n→ Strategy: COMPREHENSIVE retrieval")
        
        divisions = [e.normalized for e in entities.get('divisions', [])]
        quarters = [e.value for e in entities.get('quarters', [])]
        years = [e.value for e in entities.get('years', [])]
        
        if self.debug:
            print(f"  Divisions: {divisions}")
            print(f"  Quarters: {quarters}")
            print(f"  Years: {years}")
        
        all_nodes = []
        
        for division in divisions:
            for quarter in quarters if quarters else [None]:
                for year in years if years else [None]:
                    
                    if self.debug:
                        date_str = f"{quarter} {year}" if quarter and year else "any"
                        print(f"\n  Querying {division} - {date_str}...")
                    
                    nodes = self._retrieve_with_metadata(
                        query=query,
                        division=division,
                        quarters=[quarter] if quarter else [],
                        years=[year] if year else [],
                        top_k=self.entities_per_query
                    )
                    
                    if self.debug:
                        print(f"    → Retrieved {len(nodes)} nodes")
                    
                    all_nodes.extend(nodes)
        
        all_nodes = self._deduplicate_nodes(all_nodes)
        all_nodes = sorted(all_nodes, key=lambda n: n.score, reverse=True)
        
        if self.debug:
            print(f"\n  Total: {len(all_nodes)} nodes")
        
        return all_nodes
    
    def _retrieve_general(self, query: str) -> List[NodeWithScore]:
        """Standard retrieval without entity awareness."""
        
        if self.debug:
            print(f"\n→ Strategy: GENERAL retrieval")
        
        retriever = VectorIndexRetriever(
            index=self.index,
            similarity_top_k=self.base_top_k
        )
        
        nodes = retriever.retrieve(query)
        
        if self.debug:
            print(f"  Retrieved: {len(nodes)} nodes")
        
        return nodes
    
    def _retrieve_with_metadata(
        self,
        query: str,
        division: Optional[str] = None,
        quarters: Optional[List[str]] = None,
        years: Optional[List[str]] = None,
        top_k: int = 5
    ) -> List[NodeWithScore]:
        """
        Retrieve with metadata filters.
        Note: This is a simplified version. In production, use MetadataFilters.
        """
        
        # Standard retrieval (metadata filtering depends on your index setup)
        retriever = VectorIndexRetriever(
            index=self.index,
            similarity_top_k=top_k * 3  # Get more, filter later
        )
        
        nodes = retriever.retrieve(query)
        
        # Post-filter by metadata
        filtered = []
        for node in nodes:
            metadata = node.node.metadata
            
            # Check division match
            if division:
                node_division = metadata.get('business_unit', '').lower()
                if division.lower() not in node_division and node_division not in division.lower():
                    continue
            
            # Check quarter match
            if quarters:
                node_quarter = metadata.get('quarter', '')
                if node_quarter and node_quarter not in quarters:
                    continue
            
            # Check year match
            if years:
                node_year = metadata.get('year', '')
                if node_year and node_year not in years:
                    continue
            
            filtered.append(node)
        
        return filtered[:top_k]
    
    def _get_all_divisions_from_index(self) -> List[str]:
        """Get all unique divisions from indexed documents."""
        
        # This is a simplified version
        # In production, you'd query the index for unique metadata values
        
        divisions = set()
        
        # Sample retrieval to discover divisions
        try:
            retriever = VectorIndexRetriever(index=self.index, similarity_top_k=50)
            nodes = retriever.retrieve("division business unit")
            
            for node in nodes:
                division = node.node.metadata.get('business_unit')
                if division:
                    divisions.add(division)
                
                # Also check entities
                entities = node.node.metadata.get('entities', [])
                for entity in entities:
                    if any(div in entity.lower() for div in EntityExtractor.DIVISIONS):
                        divisions.add(entity)
        
        except:
            pass
        
        return list(divisions) if divisions else []
    
    def _deduplicate_nodes(self, nodes: List[NodeWithScore]) -> List[NodeWithScore]:
        """Remove duplicate nodes based on content similarity."""
        
        seen_texts = set()
        unique_nodes = []
        
        for node in nodes:
            # Use first 100 chars as signature
            signature = node.node.text[:100]
            
            if signature not in seen_texts:
                seen_texts.add(signature)
                unique_nodes.append(node)
        
        return unique_nodes
    
    def _check_division_coverage(self, nodes: List[NodeWithScore]) -> Dict[str, int]:
        """Check which divisions are covered in results."""
        
        coverage = defaultdict(int)
        
        for node in nodes:
            division = node.node.metadata.get('business_unit', 'Unknown')
            coverage[division] += 1
        
        return dict(coverage)
    
    def _check_date_coverage(self, nodes: List[NodeWithScore]) -> Dict[str, int]:
        """Check which dates are covered in results."""
        
        coverage = defaultdict(int)
        
        for node in nodes:
            quarter_year = node.node.metadata.get('quarter_year', 'Unknown')
            coverage[quarter_year] += 1
        
        return dict(coverage)


class StructuredResponseFormatter:
    """Format responses to ensure all entities are covered."""
    
    @staticmethod
    def format_multi_entity_response(
        response: str,
        retrieved_nodes: List[NodeWithScore],
        entities: Dict[str, List[QueryEntity]]
    ) -> str:
        """
        Format response to clearly show coverage across entities.
        Adds structure to ensure all divisions/dates are addressed.
        """
        
        # Group nodes by division
        by_division = defaultdict(list)
        for node in retrieved_nodes:
            division = node.node.metadata.get('business_unit', 'General')
            by_division[division].append(node)
        
        # Check if response already has structure
        if len(by_division) > 1 and '**' not in response:
            # Add structure
            structured = "# Summary Across Divisions\n\n"
            structured += response + "\n\n"
            structured += "# Breakdown by Division\n\n"
            
            for division, nodes in sorted(by_division.items()):
                if nodes:
                    structured += f"## {division}\n"
                    quarter_year = nodes[0].node.metadata.get('quarter_year', '')
                    if quarter_year:
                        structured += f"*{quarter_year}*\n\n"
                    
                    # Add brief content from this division
                    structured += f"{nodes[0].node.text[:200]}...\n\n"
            
            return structured
        
        return response


def integrate_entity_aware_retrieval(rag_system, debug: bool = True):
    """
    Integrate entity-aware retrieval into existing RAG system.
    
    Usage:
        rag = SpatialBlockRAG(...)
        rag.create_initial_index("./financial_docs")
        
        # Enable entity-aware retrieval
        integrate_entity_aware_retrieval(rag)
        
        # Now queries automatically handle multi-entity scenarios
        response = rag.query("What is P&L in Q4 2024?")
        # Returns results from ALL divisions!
    """
    
    # Replace standard query method with entity-aware version
    original_query = rag_system.query
    
    def entity_aware_query(query: str, use_cache: bool = True, debug_mode: bool = debug):
        """Enhanced query with entity awareness."""
        
        # Create entity-aware retriever
        entity_retriever = EntityAwareRetriever(
            index=rag_system.index,
            base_top_k=5,
            entities_per_query=3,
            debug=debug_mode
        )
        
        # Extract entities
        entities = EntityExtractor.extract_entities(query)
        
        # Retrieve with entity awareness
        nodes = entity_retriever.retrieve(query)
        
        if debug_mode:
            print(f"\n{'='*80}")
            print(f"FINAL RETRIEVAL SUMMARY")
            print(f"{'='*80}")
            print(f"Total nodes: {len(nodes)}")
            if nodes:
                print(f"Top score: {nodes[0].score:.3f}")
                print(f"\nDivision coverage:")
                coverage = entity_retriever._check_division_coverage(nodes)
                for div, count in coverage.items():
                    print(f"  {div}: {count} nodes")
        
        # Generate response using retrieved nodes
        from llama_index.core.response_synthesizers import get_response_synthesizer
        
        synthesizer = get_response_synthesizer(
            llm=rag_system.llm,
            response_mode="compact"
        )
        
        response = synthesizer.synthesize(query, nodes=nodes)
        
        # Format response for multi-entity queries
        response_str = str(response)
        response_str = StructuredResponseFormatter.format_multi_entity_response(
            response_str, nodes, entities
        )
        
        return response_str
    
    # Replace query method
    rag_system.query = entity_aware_query
    
    print("✓ Entity-aware retrieval enabled")
    print("  - Multi-division queries: Retrieves from ALL divisions")
    print("  - Multi-date queries: Covers all specified dates")
    print("  - Specific queries: Precise targeting")


# Demo usage
def demo():
    """
    Demonstration of entity-aware retrieval.
    """
    
    print("="*80)
    print("ENTITY-AWARE RETRIEVAL DEMO")
    print("="*80)
    
    # Simulate different query types
    test_queries = [
        "What is P&L in Q4 2024?",  # Multi-division
        "Tech division P&L in Q4 2024",  # Specific
        "Compare Q3 and Q4 2024 performance",  # Multi-date, multi-division
        "Tech and Healthcare revenue for Q3 and Q4",  # Comprehensive
    ]
    
    extractor = EntityExtractor()
    
    for query in test_queries:
        print(f"\n{'='*80}")
        print(f"Query: {query}")
        print(f"{'='*80}")
        
        entities = extractor.extract_entities(query)
        query_type = extractor.detect_query_type(entities)
        
        print(f"\nQuery Type: {query_type}")
        print(f"\nExtracted Entities:")
        for entity_type, entity_list in entities.items():
            if entity_list:
                values = [e.normalized for e in entity_list]
                print(f"  {entity_type}: {values}")
        
        print(f"\nRetrieval Strategy:")
        if query_type == 'multi_division':
            print("  → Query ALL divisions separately")
            print("  → Get 3 results per division")
            print("  → Combine and deduplicate")
        elif query_type == 'specific':
            print("  → Query specific division + date")
            print("  → Get top 10 results")
        elif query_type == 'multi_date_multi_division':
            print("  → Query each (division × date) combination")
            print("  → Ensure complete coverage")


if __name__ == "__main__":
    demo()
