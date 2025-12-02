"""
Copilot Engine - Multi-step reasoning agent for Safety Copilot
Enhanced with Wave 5 optimizations: caching, compression, streaming
"""

import json
import logging
from typing import Dict, Any, Optional, Iterator
from src.local_llm.model_router import ModelRouter
from src.ai_intelligence.model_runtime.model_router_v2 import ModelRouterV2
from src.ai_intelligence.cache.semantic_cache import SemanticCache
from src.ai_intelligence.prompt_optimizer.compressor import optimize_prompt
from .tool_router import ToolRouter

logger = logging.getLogger(__name__)


class CopilotEngine:
    """Main engine for Safety Copilot with tool-based reasoning and optimizations."""
    
    def __init__(self):
        self.router = ModelRouter()
        self.router_v2 = ModelRouterV2()
        self.tools = ToolRouter()
        self.cache = SemanticCache()
    
    def ask(self, query: str, context: Optional[Dict[str, Any]] = None, stream: bool = False) -> str:
        """
        Process a user query with tool-based reasoning.
        Enhanced with caching, compression, and streaming.
        
        Args:
            query: User query
            context: Optional context dictionary
            stream: Whether to stream response (returns generator)
        
        Returns:
            Response string or generator for streaming
        """
        try:
            # Check cache first
            cached = self.cache.get(query)
            if cached:
                logger.debug("Cache hit for copilot query")
                return cached
            
            # Step 1: Optimize prompt
            optimized_query = optimize_prompt(query)
            
            # Step 2: Classify intent and extract parameters
            intent_result = self._classify_intent(optimized_query)
            
            if not intent_result:
                return "Sorry, I couldn't understand the request. Please try rephrasing."
            
            tool_name = intent_result.get("tool")
            params = intent_result.get("params", {})
            
            # Step 3: Execute tool
            tool_result = self.tools.handle(tool_name, params)
            
            if "error" in tool_result:
                return f"I encountered an error: {tool_result['error']}. Please try again."
            
            # Step 4: Format and explain result
            if stream:
                return self._format_response_stream(query, tool_result, tool_name)
            else:
                response = self._format_response(query, tool_result, tool_name)
                # Cache response
                self.cache.set(query, response)
                return response
            
        except Exception as e:
            logger.error(f"Copilot engine error: {e}")
            return f"I encountered an error processing your request: {str(e)}. Please try again."
    
    def _format_response_stream(self, query: str, tool_result: Dict[str, Any], tool_name: str) -> Iterator[str]:
        """
        Format tool result with streaming response.
        
        Args:
            query: Original user query
            tool_result: Tool execution result
            tool_name: Name of tool used
        
        Yields:
            Response chunks
        """
        summary = tool_result.get("summary", "")
        
        # Generate explanation using streaming LLM
        explanation_prompt = f"""
        The user asked: "{query}"
        
        I executed the {tool_name} tool and got this result:
        {json.dumps(tool_result, indent=2)}
        
        Provide a clear, concise explanation for a safety scientist. Focus on:
        - What was found
        - Key insights
        - Any important details
        
        Keep it under 200 words.
        """
        
        try:
            # Try streaming first
            try:
                for chunk in self._stream_openai(explanation_prompt):
                    yield chunk
            except Exception:
                # Fallback to non-streaming
                explanation = self.router_v2.run(explanation_prompt, mode="summary")
                yield explanation
        except Exception:
            # Fallback to summary
            yield summary or f"Tool {tool_name} completed. Result: {json.dumps(tool_result, indent=2)}"
    
    def _stream_openai(self, prompt: str) -> Iterator[str]:
        """Stream response from OpenAI."""
        try:
            from openai import OpenAI
            import os
            
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            
            stream = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a pharmacovigilance expert assistant."},
                    {"role": "user", "content": prompt}
                ],
                stream=True
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error(f"Streaming error: {e}")
            yield "Error generating streaming response."
    
    def _classify_intent(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Classify user intent and extract parameters.
        
        Args:
            query: User query
        
        Returns:
            Intent dictionary with tool name and parameters
        """
        # Intent classification prompt
        intent_prompt = f"""
        Analyze this pharmacovigilance query and determine which tool to use.
        
        Available tools:
        - faers_query: Query FAERS database (requires: drug, optional: reaction)
        - social_query: Query social media AEs (requires: drug, optional: reaction)
        - literature_query: Query literature/PubMed (requires: drug, optional: reaction)
        - mechanism_ai: Explain drug-AE mechanism (requires: drug, reaction)
        - causality: Assess causality (requires: drug, reaction)
        - label_gap: Check if AE is in FDA label (requires: drug, reaction)
        - novelty: Detect novel signals (requires: drug, optional: reaction)
        - trend: Analyze trends (requires: drug, optional: reaction)
        
        Query: "{query}"
        
        Return JSON only with this structure:
        {{
            "tool": "tool_name",
            "params": {{
                "drug": "drug_name",
                "reaction": "reaction_name"  // if mentioned
            }}
        }}
        """
        
        try:
            # Use optimized router for intent classification
            response = self.router_v2.run(intent_prompt, mode="extraction", use_local_first=True)
            
            # Try to extract JSON from response
            # Remove markdown code blocks if present
            response = response.strip()
            if response.startswith("```"):
                response = response.split("```")[1]
                if response.startswith("json"):
                    response = response[4:]
            response = response.strip()
            
            # Parse JSON
            parsed = json.loads(response)
            # Cache intent classification
            cache_key = f"intent_{query}"
            self.cache.set(cache_key, json.dumps(parsed))
            return parsed
            
        except json.JSONDecodeError:
            # Fallback: simple keyword-based classification
            return self._fallback_intent_classification(query)
        except Exception as e:
            logger.warning(f"Intent classification error: {e}")
            return self._fallback_intent_classification(query)
    
    def _fallback_intent_classification(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Fallback intent classification using keyword matching.
        
        Args:
            query: User query
        
        Returns:
            Intent dictionary
        """
        query_lower = query.lower()
        
        # Extract drug and reaction (simple pattern matching)
        import re
        
        # Look for drug mentions
        drug_patterns = [
            r"(?:drug|medication|product)\s+(?:called|named|is)?\s+([A-Z][a-z]+)",
            r"([A-Z][a-z]+)\s+(?:drug|medication)"
        ]
        drug = None
        for pattern in drug_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                drug = match.group(1)
                break
        
        # Look for reaction mentions
        reaction_patterns = [
            r"(?:reaction|adverse event|AE|side effect)\s+(?:called|named|is)?\s+([a-z\s]+)",
            r"([a-z\s]+)\s+(?:reaction|adverse event|AE)"
        ]
        reaction = None
        for pattern in reaction_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                reaction = match.group(1).strip()
                break
        
        # Determine tool based on keywords
        if "mechanism" in query_lower or "how does" in query_lower or "why" in query_lower:
            tool = "mechanism_ai"
        elif "causality" in query_lower or "causal" in query_lower:
            tool = "causality"
        elif "label" in query_lower or "fda" in query_lower:
            tool = "label_gap"
        elif "novel" in query_lower or "new" in query_lower:
            tool = "novelty"
        elif "trend" in query_lower or "over time" in query_lower:
            tool = "trend"
        elif "social" in query_lower or "reddit" in query_lower or "twitter" in query_lower:
            tool = "social_query"
        elif "literature" in query_lower or "pubmed" in query_lower or "paper" in query_lower:
            tool = "literature_query"
        else:
            tool = "faers_query"  # Default
        
        params = {}
        if drug:
            params["drug"] = drug
        if reaction:
            params["reaction"] = reaction
        
        return {
            "tool": tool,
            "params": params
        }
    
    def _format_response(self, query: str, tool_result: Dict[str, Any], tool_name: str) -> str:
        """
        Format tool result into user-friendly response.
        
        Args:
            query: Original user query
            tool_result: Tool execution result
            tool_name: Name of tool used
        
        Returns:
            Formatted response string
        """
        summary = tool_result.get("summary", "")
        
        # Generate explanation using LLM
        explanation_prompt = f"""
        The user asked: "{query}"
        
        I executed the {tool_name} tool and got this result:
        {json.dumps(tool_result, indent=2)}
        
        Provide a clear, concise explanation for a safety scientist. Focus on:
        - What was found
        - Key insights
        - Any important details
        
        Keep it under 200 words.
        """
        
        # Optimize prompt
        explanation_prompt = optimize_prompt(explanation_prompt)
        
        try:
            # Use optimized router
            explanation = self.router_v2.run(explanation_prompt, mode="summary", use_local_first=True)
            # Cache response
            result_key = f"response_{tool_name}_{hash(str(tool_result))}"
            self.cache.set(result_key, explanation)
            return explanation
        except Exception:
            # Fallback to summary
            response = summary or f"Tool {tool_name} completed. Result: {json.dumps(tool_result, indent=2)}"
            result_key = f"response_{tool_name}_{hash(str(tool_result))}"
            self.cache.set(result_key, response)
            return response

