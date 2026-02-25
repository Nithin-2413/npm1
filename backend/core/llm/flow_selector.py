import os
import logging
from typing import List, Dict, Any, Optional
import chromadb
from sentence_transformers import SentenceTransformer
from groq import Groq
import json
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class FlowSelector:
    """
    Semantic flow selection using ChromaDB embeddings + LLM ranking
    """
    
    def __init__(self, chroma_url: Optional[str] = None):
        # Initialize embedding model
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Initialize ChromaDB client
        chroma_url = chroma_url or os.getenv("CHROMADB_URL", "http://localhost:8000")
        try:
            self.chroma_client = chromadb.HttpClient(host=chroma_url.replace("http://", "").replace(":8000", ""), port=8000)
            self.collection = self.chroma_client.get_or_create_collection(
                name="flow_templates",
                metadata={"description": "QA automation flow templates"}
            )
            logger.info("ChromaDB connected successfully")
        except Exception as e:
            logger.warning(f"ChromaDB connection failed: {e}. Running without vector search.")
            self.chroma_client = None
            self.collection = None
        
        # Initialize Groq for ranking
        groq_key = os.getenv("GROQ_API_KEY")
        if groq_key and groq_key != "your-groq-api-key-here":
            self.groq_client = Groq(api_key=groq_key)
        else:
            self.groq_client = None
            logger.warning("GROQ_API_KEY not configured. Flow selection will use embedding similarity only.")
        
        self.flows_embedded = False
    
    def embed_flows(self, flows: List[Dict[str, Any]]) -> None:
        """
        Embed all flow descriptions into ChromaDB
        Only re-embed when flows change
        """
        if not self.collection:
            logger.warning("ChromaDB not available, skipping embedding")
            return
        
        try:
            # Check if already embedded
            if self.flows_embedded:
                logger.info("Flows already embedded, skipping")
                return
            
            # Clear existing embeddings
            try:
                self.chroma_client.delete_collection("flow_templates")
                self.collection = self.chroma_client.create_collection(
                    name="flow_templates",
                    metadata={"description": "QA automation flow templates"}
                )
            except:
                pass
            
            # Prepare documents for embedding
            ids = []
            documents = []
            metadatas = []
            
            for flow in flows:
                flow_id = flow['id']
                # Create rich text description for embedding
                doc_text = f"{flow['name']}. {flow.get('description', '')}. Category: {flow.get('category', 'general')}. Parameters: {', '.join(flow.get('required_params', []) + flow.get('optional_params', []))}"
                
                ids.append(flow_id)
                documents.append(doc_text)
                metadatas.append({
                    "name": flow['name'],
                    "category": flow.get('category', 'general'),
                    "required_params": json.dumps(flow.get('required_params', [])),
                    "description": flow.get('description', '')
                })
            
            # Add to ChromaDB (it will auto-generate embeddings)
            self.collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas
            )
            
            self.flows_embedded = True
            logger.info(f"Embedded {len(flows)} flows into ChromaDB")
        
        except Exception as e:
            logger.error(f"Failed to embed flows: {e}")
    
    async def select_flow(self, user_input: str, all_flows: List[Dict[str, Any]], top_k: int = 3) -> Dict[str, Any]:
        """
        Select best matching flow using semantic search + LLM ranking
        
        Returns:
        {
            \"flow_id\": str | null,
            \"confidence\": 0.0-1.0,
            \"reasoning\": str,
            \"top_matches\": [{\"flow_id\": str, \"name\": str, \"similarity\": float}, ...]
        }
        """
        
        # Ensure flows are embedded
        if not self.flows_embedded and self.collection:
            self.embed_flows(all_flows)
        
        # Step 1: Semantic search to get top-k candidates
        top_candidates = await self._semantic_search(user_input, top_k)
        
        if not top_candidates:
            logger.warning("No candidates found from semantic search, using all flows")
            top_candidates = [{"flow_id": f['id'], "name": f['name'], "similarity": 0.5} for f in all_flows[:top_k]]
        
        # Step 2: LLM ranking to pick the best one
        if self.groq_client and len(top_candidates) > 1:
            result = await self._llm_rank_flows(user_input, top_candidates, all_flows)
        else:
            # Fallback: use highest similarity
            best = top_candidates[0]
            result = {
                "flow_id": best['flow_id'],
                "confidence": min(best['similarity'], 0.9),
                "reasoning": f"Best semantic match based on similarity score {best['similarity']:.2f}",
                "top_matches": top_candidates
            }
        
        logger.info(f\"Selected flow: {result['flow_id']} (confidence: {result['confidence']:.2f})\")\n        return result
    
    async def _semantic_search(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        \"\"\"Perform semantic search using ChromaDB\"\"\"
        if not self.collection:
            return []
        
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=top_k
            )
            
            candidates = []
            if results and results['ids'] and len(results['ids']) > 0:
                for i, flow_id in enumerate(results['ids'][0]):
                    # ChromaDB returns distances (lower is better), convert to similarity (higher is better)
                    distance = results['distances'][0][i] if 'distances' in results else 0.5
                    similarity = max(0.0, 1.0 - distance)  # Convert distance to similarity
                    
                    candidates.append({
                        "flow_id": flow_id,
                        "name": results['metadatas'][0][i]['name'],
                        "similarity": similarity
                    })
            
            return candidates
        
        except Exception as e:
            logger.error(f\"Semantic search failed: {e}\")
            return []
    
    async def _llm_rank_flows(self, user_input: str, candidates: List[Dict[str, Any]], all_flows: List[Dict[str, Any]]) -> Dict[str, Any]:
        \"\"\"Use LLM to rank and select best flow from candidates\"\"\"
        
        # Get full flow details for candidates
        candidate_details = []
        for cand in candidates:
            flow = next((f for f in all_flows if f['id'] == cand['flow_id']), None)
            if flow:
                candidate_details.append({
                    \"id\": flow['id'],
                    \"name\": flow['name'],
                    \"description\": flow.get('description', ''),
                    \"required_params\": flow.get('required_params', []),
                    \"similarity\": cand['similarity']
                })
        
        system_prompt = \"\"\"You are an expert at matching user requests to test automation flows.
        
Given a user request and top matching flows, select the BEST flow and explain why.

Return JSON format:
{
  \"flow_id\": \"selected_flow_id\",
  \"confidence\": 0.0-1.0,
  \"reasoning\": \"explanation of why this flow was chosen\"
}

Be decisive - always pick exactly one flow. If none match well, pick the closest and set confidence < 0.6.\"\"\"
        
        user_prompt = f\"\"\"User Request: \"{user_input}\"

Top Matching Flows:
{json.dumps(candidate_details, indent=2)}

Which flow best matches the user's request? Return JSON only.\"\"\"
        
        try:
            response = self.groq_client.chat.completions.create(
                model=\"llama-3.3-70b-versatile\",
                messages=[
                    {\"role\": \"system\", \"content\": system_prompt},
                    {\"role\": \"user\", \"content\": user_prompt}
                ],
                temperature=0.2,
                max_tokens=256,
                response_format={\"type\": \"json_object\"}
            )
            
            result = json.loads(response.choices[0].message.content)
            result['top_matches'] = candidates
            
            return result
        
        except Exception as e:
            logger.error(f\"LLM ranking failed: {e}\")
            # Fallback to highest similarity
            best = candidates[0]
            return {
                \"flow_id\": best['flow_id'],
                \"confidence\": min(best['similarity'], 0.8),
                \"reasoning\": f\"Selected based on semantic similarity ({best['similarity']:.2f}). LLM ranking unavailable.\",
                \"top_matches\": candidates
            }


# Global instance
flow_selector = FlowSelector()
