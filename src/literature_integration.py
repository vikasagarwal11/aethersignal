"""
Literature Integration for AetherSignal
Integrates PubMed and ClinicalTrials.gov APIs for literature enrichment.

This module provides optional literature integration that can enhance:
- Signal validation against published literature
- Social AE module (validating patient reports against clinical evidence)
- Case assessment (finding relevant clinical trials and publications)
"""

import requests
from typing import Dict, List, Optional
from datetime import datetime
import time
import xml.etree.ElementTree as ET


def search_pubmed(drug: str, reaction: Optional[str] = None, max_results: int = 10) -> List[Dict]:
    """
    Search PubMed for articles related to drug and reaction.
    
    Uses NCBI E-utilities API (free, no API key required).
    
    Args:
        drug: Drug name
        reaction: Optional reaction/adverse event
        max_results: Maximum number of results to return
        
    Returns:
        List of dictionaries with article information
    """
    try:
        # Build search query
        query_parts = [drug]
        if reaction:
            query_parts.append(reaction)
        query = " AND ".join(query_parts)
        
        # Step 1: Search PubMed (E-utilities esearch)
        search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        search_params = {
            'db': 'pubmed',
            'term': query,
            'retmax': max_results,
            'retmode': 'json',
            'sort': 'relevance'
        }
        
        response = requests.get(search_url, params=search_params, timeout=10)
        if response.status_code != 200:
            return []
        
        data = response.json()
        pmids = data.get('esearchresult', {}).get('idlist', [])
        
        if not pmids:
            return []
        
        # Step 2: Fetch article details (E-utilities efetch)
        fetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
        fetch_params = {
            'db': 'pubmed',
            'id': ','.join(pmids[:max_results]),
            'retmode': 'xml'
        }
        
        response = requests.get(fetch_url, params=fetch_params, timeout=15)
        if response.status_code != 200:
            return []
        
        # Parse XML response
        try:
            root = ET.fromstring(response.content)
            articles = []
            
            # PubMed XML namespace
            ns = {'pubmed': 'http://www.ncbi.nlm.nih.gov'}
            
            for article in root.findall('.//pubmed:PubmedArticle', ns):
                # Extract PMID
                pmid_elem = article.find('.//pubmed:PMID', ns)
                pmid = pmid_elem.text if pmid_elem is not None else ''
                
                # Extract title
                title_elem = article.find('.//pubmed:ArticleTitle', ns)
                title = title_elem.text if title_elem is not None else f"PubMed ID: {pmid}"
                
                # Extract authors
                authors = []
                author_list = article.find('.//pubmed:AuthorList', ns)
                if author_list is not None:
                    for author in author_list.findall('.//pubmed:Author', ns):
                        last_name = author.find('.//pubmed:LastName', ns)
                        first_name = author.find('.//pubmed:ForeName', ns)
                        if last_name is not None:
                            author_name = last_name.text
                            if first_name is not None:
                                author_name += f" {first_name.text}"
                            authors.append(author_name)
                
                # Extract publication date
                pub_date_elem = article.find('.//pubmed:PubDate', ns)
                year = None
                if pub_date_elem is not None:
                    year_elem = pub_date_elem.find('.//pubmed:Year', ns)
                    if year_elem is not None:
                        year = year_elem.text
                
                # Extract journal
                journal_elem = article.find('.//pubmed:Journal/pubmed:Title', ns)
                journal = journal_elem.text if journal_elem is not None else ''
                
                # Extract abstract (first paragraph)
                abstract_elem = article.find('.//pubmed:AbstractText', ns)
                abstract = abstract_elem.text if abstract_elem is not None else ''
                
                articles.append({
                    'pmid': pmid,
                    'url': f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                    'title': title,
                    'authors': ', '.join(authors[:3]) + (' et al.' if len(authors) > 3 else ''),
                    'journal': journal,
                    'year': year,
                    'abstract': abstract[:200] + '...' if len(abstract) > 200 else abstract,
                })
            
            return articles
            
        except ET.ParseError:
            # Fallback: return basic info if XML parsing fails
            articles = []
            for pmid in pmids[:max_results]:
                articles.append({
                    'pmid': pmid,
                    'url': f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                    'title': f"PubMed ID: {pmid}",
                    'authors': '',
                    'journal': '',
                    'year': None,
                    'abstract': '',
                })
            return articles
        
    except Exception as e:
        # Silently fail - literature integration is optional
        return []


def search_clinical_trials(drug: str, condition: Optional[str] = None, max_results: int = 10) -> List[Dict]:
    """
    Search ClinicalTrials.gov for trials related to drug and condition.
    
    Uses ClinicalTrials.gov API v2 (free, no API key required).
    
    Args:
        drug: Drug/intervention name
        condition: Optional condition/disease
        max_results: Maximum number of results to return
        
    Returns:
        List of dictionaries with trial information
    """
    try:
        # Build search query
        query_parts = []
        if drug:
            query_parts.append(f"intervention={drug}")
        if condition:
            query_parts.append(f"condition={condition}")
        
        # ClinicalTrials.gov API v2
        api_url = "https://clinicaltrials.gov/api/v2/studies"
        params = {
            'query.cond': condition or '',
            'query.term': drug,
            'pageSize': max_results,
            'format': 'json'
        }
        
        response = requests.get(api_url, params=params, timeout=10)
        if response.status_code != 200:
            return []
        
        data = response.json()
        studies = data.get('studies', [])
        
        trials = []
        for study in studies[:max_results]:
            protocol_section = study.get('protocolSection', {})
            identification_module = protocol_section.get('identificationModule', {})
            
            trials.append({
                'nct_id': identification_module.get('nctId', ''),
                'title': identification_module.get('briefTitle', ''),
                'status': protocol_section.get('statusModule', {}).get('overallStatus', ''),
                'url': f"https://clinicaltrials.gov/study/{identification_module.get('nctId', '')}",
                'phase': protocol_section.get('designModule', {}).get('phases', []),
            })
        
        return trials
        
    except Exception as e:
        # Silently fail - literature integration is optional
        return []


def enrich_signal_with_literature(drug: str, reaction: str) -> Dict:
    """
    Enrich a drug-reaction signal with literature evidence.
    
    Args:
        drug: Drug name
        reaction: Reaction/adverse event
        
    Returns:
        Dictionary with literature evidence
    """
    pubmed_results = search_pubmed(drug, reaction, max_results=5)
    clinical_trials = search_clinical_trials(drug, reaction, max_results=5)
    
    return {
        'pubmed_articles': pubmed_results,
        'clinical_trials': clinical_trials,
        'total_pubmed': len(pubmed_results),
        'total_trials': len(clinical_trials),
    }

