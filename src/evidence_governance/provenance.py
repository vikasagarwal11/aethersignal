"""
Provenance Module - Phase 3L Step 3
Exports ProvenanceTracker (registry) and ProvenanceEngine (scoring).
"""

from .provenance_engine import ProvenanceEngine
from .provenance_tracker import ProvenanceTracker

# Global instances
_provenance_engine: ProvenanceEngine = None
_provenance_tracker: ProvenanceTracker = None


def get_provenance_engine() -> ProvenanceEngine:
    """Get or create global provenance engine instance."""
    global _provenance_engine
    if _provenance_engine is None:
        _provenance_engine = ProvenanceEngine()
    return _provenance_engine


def get_provenance_tracker() -> ProvenanceTracker:
    """Get or create global provenance tracker instance."""
    global _provenance_tracker
    if _provenance_tracker is None:
        _provenance_tracker = ProvenanceTracker()
    return _provenance_tracker


# Convenience function
def get_provenance() -> ProvenanceEngine:
    """Convenience function to get provenance engine."""
    return get_provenance_engine()


class ProvenanceTracker:
    """
    Tracks provenance (source, platform, version, etc.) for all evidence.
    """
    
    def __init__(self):
        """Initialize provenance tracker."""
        self.provenance_records: Dict[str, Dict[str, Any]] = {}
        self.storage_file = PROVENANCE_STORAGE / "provenance_registry.jsonl"
        
        if PROVENANCE_ENABLED:
            ensure_directories()
            self._load_existing_records()
    
    def record_provenance(
        self,
        record_id: str,
        source: str,
        platform: Optional[str] = None,
        ingest_date: Optional[datetime] = None,
        version: Optional[str] = None,
        source_url: Optional[str] = None,
        source_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Record provenance for a record.
        
        Args:
            record_id: Unique record identifier
            source: Source name (faers, social, literature, etc.)
            platform: Platform name (reddit, x, pubmed, etc.)
            ingest_date: Date of ingestion
            version: Source version/API version
            source_url: Original source URL
            source_id: Source-specific ID
            metadata: Optional additional metadata
        
        Returns:
            Provenance record dictionary
        """
        if not PROVENANCE_ENABLED:
            return {}
        
        evidence_class_weight = get_evidence_class_weight(source)
        
        provenance = {
            "provenance_id": str(uuid.uuid4()),
            "record_id": record_id,
            "source": source,
            "platform": platform or source,
            "ingest_date": (ingest_date or datetime.utcnow()).isoformat(),
            "version": version or "1.0",
            "source_url": source_url,
            "source_id": source_id,
            "evidence_class": source,
            "evidence_class_weight": evidence_class_weight,
            "metadata": metadata or {},
            "recorded_at": datetime.utcnow().isoformat()
        }
        
        self.provenance_records[record_id] = provenance
        
        # Persist to file
        try:
            with open(self.storage_file, "a") as f:
                f.write(json.dumps(provenance) + "\n")
        except Exception as e:
            logger.error(f"Error persisting provenance: {e}")
        
        return provenance
    
    def get_provenance(self, record_id: str) -> Optional[Dict[str, Any]]:
        """
        Get provenance for a record.
        
        Args:
            record_id: Record identifier
        
        Returns:
            Provenance record or None
        """
        if not PROVENANCE_ENABLED:
            return None
        
        return self.provenance_records.get(record_id)
    
    def get_source_breakdown(self) -> Dict[str, int]:
        """
        Get breakdown of records by source.
        
        Returns:
            Dictionary mapping source to count
        """
        if not PROVENANCE_ENABLED:
            return {}
        
        breakdown = {}
        for provenance in self.provenance_records.values():
            source = provenance.get("source", "unknown")
            breakdown[source] = breakdown.get(source, 0) + 1
        
        return breakdown
    
    def _load_existing_records(self):
        """Load existing provenance records from storage."""
        if not self.storage_file.exists():
            return
        
        try:
            with open(self.storage_file, "r") as f:
                for line in f:
                    if line.strip():
                        record = json.loads(line)
                        record_id = record.get("record_id")
                        if record_id:
                            self.provenance_records[record_id] = record
            
            logger.info(f"Loaded {len(self.provenance_records)} provenance records")
        except Exception as e:
            logger.error(f"Error loading provenance records: {e}")

