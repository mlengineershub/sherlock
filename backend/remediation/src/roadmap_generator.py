"""
Enhanced roadmap generator with structured output.
"""

import logging
from typing import Dict, List, Any
from datetime import datetime
from fastapi import HTTPException
from backend.remediation.src.roadmap_utils import format_roadmap_steps, generate_roadmark_markdown

logger = logging.getLogger(__name__)

class RoadmapGenerator:
    """Generates structured remediation roadmaps."""
    
    def __init__(self, bedrock_client: Any):
        self.bedrock_client = bedrock_client
        
    def generate_roadmap(self, relevant_nodes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate structured remediation roadmap.
        Returns:
            {
                "timestamp": str,
                "raw_text": str,
                "structured": Dict[str, List[Dict[str, str]]],
                "markdown": str
            }
        """
        try:
            prompt = self._build_roadmap_prompt(relevant_nodes)
            logger.info(f"Generated roadmap prompt with {len(relevant_nodes)} relevant nodes")
            # Get model configuration from config
            from backend.remediation.config import MODEL_CONFIG
            model_config = MODEL_CONFIG.get("roadmap_generation", {})
            model_id = model_config.get("model_id", "anthropic.claude-3-5-haiku-20241022-v1:0")
            max_tokens = model_config.get("max_tokens", 1500)
            temperature = model_config.get("temperature", 0.5)
            
            logger.info(f"Using model {model_id} for roadmap generation")
            
            response = self.bedrock_client.invoke_model(
                prompt=prompt,
                model_id=model_id,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            structured = format_roadmap_steps(response.strip())
            markdown = generate_roadmark_markdown(structured)
            
            logger.info(f"Successfully generated roadmap with {sum(len(v) for v in structured.values())} actions")
            
            return {
                "timestamp": datetime.now().isoformat(),
                "raw_text": response.strip(),
                "structured": structured,
                "markdown": markdown
            }
            
        except Exception as e:
            logger.error(f"Failed to generate roadmap: {str(e)}", exc_info=True)
            
            # Try with fallback model if primary model fails
            try:
                logger.info("Attempting to generate roadmap with fallback model")
                
                fallback_model = "anthropic.claude-3-5-haiku-20241022-v1:0"
                
                prompt = self._build_roadmap_prompt(relevant_nodes)
                logger.info(f"Generated roadmap prompt with {len(relevant_nodes)} relevant nodes for fallback model")
                
                response = self.bedrock_client.invoke_model(
                    prompt=prompt,
                    model_id=fallback_model,
                    max_tokens=1500,
                    temperature=0.7
                )
                
                structured = format_roadmap_steps(response.strip())
                markdown = generate_roadmark_markdown(structured)
                
                logger.info(f"Successfully generated roadmap with fallback model with {sum(len(v) for v in structured.values())} actions")
                
                return {
                    "timestamp": datetime.now().isoformat(),
                    "raw_text": response.strip(),
                    "structured": structured,
                    "markdown": markdown,
                    "fallback_used": True
                }
                
            except Exception as fallback_error:
                logger.error(f"Fallback model also failed: {str(fallback_error)}", exc_info=True)
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to generate remediation roadmap: {str(e)}. Fallback also failed: {str(fallback_error)}"
                )
            
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate remediation roadmap: {str(e)}"
            )
        
    def _build_roadmap_prompt(self, relevant_nodes: List[Dict[str, Any]]) -> str:
        """Construct roadmap generation prompt."""
        try:
            prompt_parts = [
                "Create a prioritized cybersecurity remediation roadmap with:",
                "1. Immediate actions (next 24-48 hours)",
                "2. Short-term actions (next week)", 
                "3. Medium-term actions (next month)",
                "For each action, specify:",
                "- The specific action to take",
                "- The responsible party (in parentheses)",
                "- The rationale (after a dash)",
                "\nInputs:\n"
            ]
            
            for node_data in relevant_nodes:
                node = node_data["node"]
                prompt_parts.append(f"THREAT: {node['title']}")
                prompt_parts.append(f"DESCRIPTION: {node['description']}")
                
                for persp in node_data["perspectives"].values():
                    if persp["selected"] == True:
                        prompt_parts.append(f"- {persp['title']}: {persp['content']}")
                
                if node_data["user_input"]:
                    prompt_parts.append(f"- EXPERT NOTES: {node_data['user_input']}")
                
                prompt_parts.append("")
                
            return "\n".join(prompt_parts)
            
        except Exception as e:
            logger.error(f"Failed to build roadmap prompt: {str(e)}", exc_info=True)
            raise