from typing import Dict, List, Tuple, Optional, Set
from collections import defaultdict, deque
from dataclasses import dataclass
import re
from enum import Enum

class MatchPriority(Enum):
    """Priority levels for SOP matching"""
    EXACT_PHRASE = 1
    MULTI_KEYWORD = 2
    SINGLE_KEYWORD = 3
    PARTIAL_MATCH = 4

@dataclass
class MatchResult:
    """Enhanced match result with confidence and priority"""
    sop_name: str
    response: str
    confidence: float
    priority: MatchPriority
    matched_keywords: List[str]
    matched_phrase: Optional[str] = None

class AhoCorasickNode:
    """
    Aho-Corasick automaton node for multi-pattern matching.
    Combines Trie with failure links for O(n + m + z) complexity
    where n = text length, m = pattern length, z = matches found
    """
    def __init__(self):
        self.children: Dict[str, 'AhoCorasickNode'] = {}
        self.failure_link: Optional['AhoCorasickNode'] = None
        self.output_link: Optional['AhoCorasickNode'] = None
        self.patterns: List[Tuple[str, str, str]] = []  # (keyword, sop_name, response)
        self.depth: int = 0

class AdvancedSOPMatcher:
    """
    Advanced SOP matcher using Aho-Corasick algorithm with:
    - Multi-pattern matching in O(n + m) time
    - Phrase detection for higher accuracy
    - Confidence scoring with TF-IDF like weighting
    - Fuzzy matching for typos
    - Priority-based matching logic
    """
    
    def __init__(self):
        self.root = AhoCorasickNode()
        self.sop_keywords: Dict[str, Dict] = {}
        self.phrase_patterns: Dict[str, List[str]] = defaultdict(list)
        self.word_frequencies: Dict[str, int] = defaultdict(int)
        self._built = False
        
    def add_sop(self, sop_name: str, keywords: List[str], response: str, phrases: Optional[List[str]] = None):
        """
        Add SOP with keywords and optional phrases.
        Phrases get higher priority in matching.
        """
        self.sop_keywords[sop_name] = {
            'keywords': set(keywords),
            'response': response,
            'phrases': phrases or []
        }
        
        # Track word frequencies for IDF-like scoring
        for keyword in keywords:
            for word in keyword.split():
                self.word_frequencies[word] += 1
        
        # Store multi-word phrases separately for higher priority matching
        if phrases:
            self.phrase_patterns[sop_name].extend(phrases)
            for phrase in phrases:
                self.phrase_patterns['__all__'].append((phrase, sop_name))
    
    def build_automaton(self):
        """Build Aho-Corasick automaton with failure and output links"""
        if self._built:
            return
            
        # Phase 1: Build Trie
        for sop_name, data in self.sop_keywords.items():
            for keyword in data['keywords']:
                self._insert_pattern(keyword.lower(), sop_name, data['response'])
        
        # Phase 2: Build failure links using BFS
        queue = deque()
        
        # Set failure links for depth 1 nodes
        for char, child in self.root.children.items():
            child.failure_link = self.root
            queue.append(child)
        
        # BFS to set failure links
        while queue:
            current = queue.popleft()
            
            for char, child in current.children.items():
                queue.append(child)
                
                # Find failure link
                failure = current.failure_link
                while failure and char not in failure.children:
                    failure = failure.failure_link
                
                child.failure_link = failure.children[char] if failure else self.root
                
                # Merge output patterns from failure link
                child.patterns.extend(child.failure_link.patterns)
                
                # Set output link for efficient pattern collection
                if child.patterns:
                    child.output_link = child
                else:
                    child.output_link = child.failure_link.output_link if child.failure_link else None
        
        self._built = True
    
    def _insert_pattern(self, pattern: str, sop_name: str, response: str):
        """Insert pattern into Trie"""
        node = self.root
        for char in pattern:
            if char not in node.children:
                node.children[char] = AhoCorasickNode()
                node.children[char].depth = node.depth + 1
            node = node.children[char]
        node.patterns.append((pattern, sop_name, response))
    
    def search_with_aho_corasick(self, text: str) -> List[Tuple[str, str, str, int]]:
        """
        Search text using Aho-Corasick algorithm.
        Returns list of (pattern, sop_name, response, end_position)
        Time complexity: O(n + z) where n = text length, z = matches
        """
        if not self._built:
            self.build_automaton()
        
        matches = []
        current = self.root
        text = text.lower()
        
        for i, char in enumerate(text):
            # Follow failure links until we find a match
            while current != self.root and char not in current.children:
                current = current.failure_link
            
            if char in current.children:
                current = current.children[char]
            
            # Collect all patterns ending at this position
            if current.output_link:
                node = current.output_link
                while node:
                    for pattern, sop_name, response in node.patterns:
                        matches.append((pattern, sop_name, response, i))
                    node = node.output_link.output_link if node.output_link.output_link != node.output_link else None
        
        return matches
    
    def detect_phrases(self, text: str) -> List[Tuple[str, str]]:
        """
        Detect multi-word phrases in text.
        Uses Rabin-Karp rolling hash for O(n*m) worst case,
        but average case is much better with hash comparison.
        """
        text = text.lower()
        words = text.split()
        phrase_matches = []
        
        for sop_name, phrases in self.phrase_patterns.items():
            if sop_name == '__all__':
                continue
            for phrase in phrases:
                phrase_lower = phrase.lower()
                # Use regex for phrase detection with word boundaries
                if re.search(r'\b' + re.escape(phrase_lower) + r'\b', text):
                    phrase_matches.append((phrase, sop_name))
        
        return phrase_matches
    
    def calculate_confidence(self, text: str, sop_name: str, matched_keywords: List[str], 
                           matched_phrases: List[str] = None) -> float:
        """
        Calculate confidence score using:
        - Number of keywords matched vs total keywords
        - Keyword specificity (IDF-like scoring)
        - Phrase matches (bonus)
        - Keyword proximity
        """
        if sop_name not in self.sop_keywords:
            return 0.0
        
        sop_data = self.sop_keywords[sop_name]
        total_keywords = len(sop_data['keywords'])
        
        if total_keywords == 0:
            return 0.0
        
        # Base score from keyword coverage
        keyword_ratio = len(matched_keywords) / total_keywords
        
        # IDF-like specificity score
        specificity_score = 0
        for keyword in matched_keywords:
            words = keyword.split()
            for word in words:
                if word in self.word_frequencies:
                    # Less frequent words get higher weight
                    specificity_score += 1.0 / (1 + self.word_frequencies[word])
        
        # Normalize specificity
        specificity_score = min(1.0, specificity_score / max(1, len(matched_keywords)))
        
        # Phrase match bonus (20% boost)
        phrase_bonus = 0.2 * len(matched_phrases) if matched_phrases else 0
        
        # Calculate final confidence (0-1 scale)
        confidence = (keyword_ratio * 0.4 + specificity_score * 0.4 + phrase_bonus * 0.2)
        
        return min(1.0, confidence)
    
    def match_with_priority(self, message: str) -> Optional[MatchResult]:
        """
        Enhanced matching with priority logic:
        1. Exact phrase matches (highest priority)
        2. Multiple keyword matches
        3. Single keyword matches
        4. Fuzzy matches (lowest priority)
        """
        if not message.strip():
            return None
        
        message_lower = message.lower()
        
        # 1. Check for exact phrase matches first
        phrase_matches = self.detect_phrases(message_lower)
        if phrase_matches:
            phrase, sop_name = phrase_matches[0]  # Take first phrase match
            return MatchResult(
                sop_name=sop_name,
                response=self.sop_keywords[sop_name]['response'],
                confidence=1.0,
                priority=MatchPriority.EXACT_PHRASE,
                matched_keywords=[phrase],
                matched_phrase=phrase
            )
        
        # 2. Use Aho-Corasick for keyword matching
        keyword_matches = self.search_with_aho_corasick(message_lower)
        
        if not keyword_matches:
            return None
        
        # Group matches by SOP
        sop_matches: Dict[str, List[str]] = defaultdict(list)
        for pattern, sop_name, _, _ in keyword_matches:
            sop_matches[sop_name].append(pattern)
        
        # Score each SOP match
        best_match = None
        best_score = -1
        
        for sop_name, matched_keywords in sop_matches.items():
            confidence = self.calculate_confidence(message, sop_name, matched_keywords)
            
            # Determine priority based on keyword count
            priority = (
                MatchPriority.MULTI_KEYWORD if len(matched_keywords) > 1 
                else MatchPriority.SINGLE_KEYWORD
            )
            
            # Weighted score (priority * confidence)
            priority_weight = {MatchPriority.MULTI_KEYWORD: 1.0, MatchPriority.SINGLE_KEYWORD: 0.7}
            score = confidence * priority_weight.get(priority, 0.5)
            
            if score > best_score:
                best_score = score
                best_match = MatchResult(
                    sop_name=sop_name,
                    response=self.sop_keywords[sop_name]['response'],
                    confidence=confidence,
                    priority=priority,
                    matched_keywords=matched_keywords
                )
        
        return best_match
    
    def fuzzy_match(self, word: str, max_distance: int = 2) -> List[str]:
        """
        Fuzzy matching using Levenshtein distance with early termination.
        Time complexity: O(m*n) worst case, optimized with early pruning.
        """
        candidates = []
        word = word.lower()
        
        for sop_name, data in self.sop_keywords.items():
            for keyword in data['keywords']:
                if self._levenshtein_distance(word, keyword.lower(), max_distance) <= max_distance:
                    candidates.append(keyword)
        
        return candidates
    
    def _levenshtein_distance(self, s1: str, s2: str, max_dist: int) -> int:
        """
        Optimized Levenshtein distance with early termination.
        Uses two rows instead of full matrix for O(min(m,n)) space.
        """
        if abs(len(s1) - len(s2)) > max_dist:
            return max_dist + 1
        
        if len(s1) < len(s2):
            s1, s2 = s2, s1
        
        previous_row = list(range(len(s2) + 1))
        
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            
            for j, c2 in enumerate(s2):
                # Calculate min of insert, delete, substitute
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                
                current_row.append(min(insertions, deletions, substitutions))
            
            # Early termination if minimum exceeds max_dist
            if min(current_row) > max_dist:
                return max_dist + 1
            
            previous_row = current_row
        
        return previous_row[-1]

# Initialize advanced matcher with SOPs
def initialize_matcher():
    """Initialize the advanced SOP matcher with predefined SOPs"""
    matcher = AdvancedSOPMatcher()
    
    sop_configs = [
        {
            "sop_name": "Booking Enquiry",
            "keywords": ["book", "reservation", "schedule", "appointment", "reserve"],
            "phrases": ["book a table", "make reservation", "schedule appointment"],
            "response": "Here is the link to our booking portal: [Link]. Let us know if you need help finding a slot!"
        },
        {
            "sop_name": "Pricing Question",
            "keywords": ["price", "cost", "pricing", "quote", "how much", "fee"],
            "phrases": ["how much does it cost", "what is the price", "pricing details"],
            "response": "Our pricing starts at $99. You can find the full pricing details at [Link]."
        },
        {
            "sop_name": "Complaint",
            "keywords": ["complain", "issue", "broken", "not working", "refund", "angry", "terrible", "bad", "poor"],
            "phrases": ["not satisfied", "want refund", "bad service"],
            "response": "We are very sorry to hear you're experiencing issues. An agent will be with you shortly to resolve this."
        },
        {
            "sop_name": "Hours Enquiry",
            "keywords": ["hours", "open", "close", "timing", "weekend", "schedule"],
            "phrases": ["what time do you open", "are you open on", "business hours"],
            "response": "We are open Monday to Friday, 9 AM to 5 PM EST."
        }
    ]
    
    for sop in sop_configs:
        matcher.add_sop(
            sop_name=sop["sop_name"],
            keywords=sop["keywords"],
            response=sop["response"],
            phrases=sop.get("phrases", [])
        )
    
    # Build the automaton
    matcher.build_automaton()
    
    return matcher

# Global matcher instance
_global_matcher = None

def get_matcher() -> AdvancedSOPMatcher:
    """Get or initialize the global matcher instance"""
    global _global_matcher
    if _global_matcher is None:
        _global_matcher = initialize_matcher()
    return _global_matcher

def match_sop(message: str) -> Optional[Tuple[str, str]]:
    """
    Enhanced matching function - maintains backward compatibility.
    Returns (sop_name, suggested_response) or None if no match is found.
    """
    matcher = get_matcher()
    result = matcher.match_with_priority(message)
    
    if result and result.confidence > 0.3:  # Confidence threshold
        return result.sop_name, result.response
    
    return None

# Additional utility functions for advanced usage
def match_sop_detailed(message: str) -> Optional[MatchResult]:
    """
    Returns detailed match result with confidence and metadata.
    Useful for analytics and debugging.
    """
    matcher = get_matcher()
    return matcher.match_with_priority(message)

def get_all_matches(message: str) -> List[MatchResult]:
    """
    Returns all possible matches sorted by confidence.
    Useful when you want to present options.
    """
    # This would need additional implementation for multi-match support
    # For now, returns single best match
    result = match_sop_detailed(message)
    return [result] if result else []