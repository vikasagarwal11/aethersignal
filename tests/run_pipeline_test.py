"""
Test script for AetherSignal Unified AE Pipeline
Tests end-to-end ingestion from all sources.
"""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path.parent))

from src.ae_pipeline import AEPipeline
import pandas as pd

def main():
    """Run pipeline test."""
    print("=" * 60)
    print("AetherSignal Unified AE Pipeline Test")
    print("=" * 60)
    
    # Initialize pipeline
    print("\n📦 Initializing pipeline...")
    pipeline = AEPipeline()
    
    # Test drug
    test_drug = "Ozempic"  # or "semaglutide"
    days_back = 7
    
    print(f"\n🔍 Running pipeline for: {test_drug}")
    print(f"   Days back: {days_back}")
    
    # Run pipeline
    try:
        df = pipeline.run(
            drug=test_drug,
            days_back=days_back,
            include_social=True,
            include_faers=True,
            include_literature=True,
            include_free_apis=True,
            store_results=True
        )
        
        # Display results
        print("\n" + "=" * 60)
        print("RESULTS")
        print("=" * 60)
        
        if df.empty:
            print("⚠️  No results found")
        else:
            print(f"\n✅ Total records: {len(df)}")
            print(f"\n📊 By source:")
            source_counts = df["source"].value_counts()
            for source, count in source_counts.items():
                print(f"   {source}: {count}")
            
            print(f"\n📋 Sample records (first 5):")
            print(df[["timestamp", "drug", "reaction", "source", "confidence", "severity"]].head().to_string())
            
            # Check storage
            print(f"\n💾 Storage stats:")
            stats = pipeline.storage.get_stats()
            print(f"   Total records in DB: {stats.get('total_records', 0)}")
            if stats.get('by_source'):
                print(f"   By source: {stats['by_source']}")
        
        print("\n" + "=" * 60)
        print("✅ Test complete!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

