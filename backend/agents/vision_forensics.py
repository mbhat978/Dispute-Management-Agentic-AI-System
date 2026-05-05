"""
Vision Forensics Agent for Banking Dispute Management System

This specialized agent handles all receipt and image analysis using
LLM Vision models for OCR and evidence verification.
"""

from typing import Dict, Any, List, Tuple
from loguru import logger
from datetime import datetime
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    from .. import mcp_client as banking_tools
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import HumanMessage
except ImportError:
    import mcp_client as banking_tools
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import HumanMessage


class VisionForensicsAgent:
    """
    Specialized agent for visual evidence analysis.
    Handles receipt OCR, image analysis, and evidence verification using Vision models.
    """
    
    def __init__(self):
        self.agent_name = "VisionForensicsAgent"
        
    def execute_vision_analysis(
        self,
        tool_steps: List[Dict[str, Any]],
        audit_trail: List[str]
    ) -> Dict[str, Any]:
        """
        Execute vision analysis tools in parallel using ThreadPoolExecutor.
        
        Args:
            tool_steps: List of vision tool execution plans
            audit_trail: Audit trail to append execution logs
            
        Returns:
            Dictionary with vision analysis results and updated audit trail
        """
        gathered_data = {}
        
        logger.info(f"[{self.agent_name}] Starting parallel vision forensics for {len(tool_steps)} tools")
        
        def execute_step(step: Dict[str, Any]) -> Tuple[str, str, Dict[str, Any], Dict[str, Any]]:
            """Execute a single vision tool step and return results."""
            tool_name = step["tool"]
            tool_input = step["input"]
            data_key = step["data_key"]
            
            logger.info(f"[{self.agent_name}] Executing vision tool: {tool_name}")
            
            try:
                result = self._execute_vision_tool(tool_name, tool_input)
                logger.success(f"[{self.agent_name}] Vision tool {tool_name} completed successfully")
                return tool_name, data_key, tool_input, result
            except Exception as e:
                logger.error(f"[{self.agent_name}] Vision tool {tool_name} failed: {str(e)}")
                return tool_name, data_key, tool_input, {"error": str(e)}
        
        # Execute vision tools in parallel using ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=len(tool_steps)) as executor:
            # Submit all tasks
            future_to_step = {executor.submit(execute_step, step): step for step in tool_steps}
            
            # Collect results as they complete
            for future in as_completed(future_to_step):
                try:
                    tool_name, data_key, tool_input, result = future.result()
                    
                    # Store results
                    gathered_data[data_key] = result
                    
                    # Add to audit trail with vision-specific insights
                    audit_trail.append(
                        f"{self.agent_name} THOUGHT: Need to analyze visual evidence using {tool_name}"
                    )
                    audit_trail.append(
                        f"{self.agent_name} ACTION: Executing {tool_name} for image analysis"
                    )
                    
                    # Log vision-specific insights
                    if tool_name == "analyze_receipt_evidence" and "error" not in result:
                        extracted_amount = result.get("extracted_amount", "N/A")
                        extracted_merchant = result.get("extracted_merchant", "N/A")
                        is_valid = result.get("is_valid_receipt", False)
                        logger.info(
                            f"[{self.agent_name}] Receipt Analysis: "
                            f"Amount={extracted_amount}, Merchant={extracted_merchant}, Valid={is_valid}"
                        )
                        audit_trail.append(
                            f"{self.agent_name} OBSERVATION: Receipt OCR complete - "
                            f"Extracted Amount: ${extracted_amount}, Merchant: {extracted_merchant}, "
                            f"Valid Receipt: {is_valid}"
                        )
                    elif tool_name == "calculate_timeline_from_evidence" and "error" not in result:
                        return_date = result.get("return_date_extracted", "N/A")
                        days_elapsed = result.get("days_elapsed", 0)
                        refund_stage = result.get("refund_stage", "unknown")
                        logger.info(
                            f"[{self.agent_name}] Timeline Analysis: "
                            f"Return Date={return_date}, Days Elapsed={days_elapsed}, Stage={refund_stage}"
                        )
                        audit_trail.append(
                            f"{self.agent_name} OBSERVATION: Evidence timeline calculated - "
                            f"Return Date: {return_date}, Days Elapsed: {days_elapsed}, "
                            f"Refund Stage: {refund_stage}"
                        )
                    else:
                        audit_trail.append(
                            f"{self.agent_name} OBSERVATION: {tool_name} returned {json.dumps(result, default=str)}"
                        )
                        
                except Exception as e:
                    step = future_to_step[future]
                    tool_name = step["tool"]
                    logger.error(f"[{self.agent_name}] Tool execution failed: {tool_name} - {str(e)}")
                    audit_trail.append(f"{self.agent_name} ERROR: {tool_name} failed - {str(e)}")
        
        logger.success(
            f"[{self.agent_name}] Parallel vision forensics complete. "
            f"Analyzed {len(gathered_data)} visual evidence items"
        )
        
        return {
            "gathered_data": gathered_data,
            "audit_trail": audit_trail
        }
    
    def _execute_vision_tool(self, tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single vision analysis tool and return results."""
        
        if tool_name == "analyze_receipt_evidence":
            logger.info(
                f"[{self.agent_name}] Analyzing receipt image with Vision OCR for "
                f"expected_merchant={tool_input.get('expected_merchant', 'unknown')}"
            )
            result_str = banking_tools.analyze_receipt_evidence(
                tool_input.get("receipt_base64", ""),
                tool_input.get("expected_merchant", "")
            )
            # Parse the JSON string returned by analyze_receipt_evidence
            return json.loads(result_str)
            
        elif tool_name == "calculate_timeline_from_evidence":
            logger.info(
                f"[{self.agent_name}] Calculating refund timeline from evidence image for "
                f"transaction_id={tool_input.get('transaction_id')}"
            )
            return self._analyze_timeline_evidence(tool_input)
            
        else:
            return {"error": f"Unsupported vision tool: {tool_name}"}
    
    def _analyze_timeline_evidence(self, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze return receipt or refund evidence to extract timeline information.
        Uses Vision model to extract return date and calculate refund stage.
        """
        try:
            evidence_base64 = tool_input.get("evidence_base64", "")
            if not evidence_base64:
                return {"error": "No return receipt evidence provided."}
                
            image_url = evidence_base64
            if not image_url.startswith("data:image"):
                image_url = f"data:image/jpeg;base64,{evidence_base64}"
                
            llm = ChatOpenAI(model="gpt-4o", temperature=0)
            prompt_text = """
            You are a forensic financial AI. Analyze this return receipt, cancellation email, or support ticket screenshot.
            Extract the exact DATE when the customer returned the item or cancelled the service.
            
            You MUST return ONLY a valid JSON object.
            Use this exact JSON schema:
            {
                "extracted_return_date": "YYYY-MM-DD",
                "is_valid_proof": boolean,
                "note": "brief explanation of what you found"
            }
            """
            message = HumanMessage(
                content=[
                    {"type": "text", "text": prompt_text},
                    {"type": "image_url", "image_url": {"url": image_url}}
                ]
            )
            
            # Run synchronously since we are inside the normal execution flow
            response = llm.invoke([message])
            content_str = str(response.content) if not isinstance(response.content, str) else response.content
            cleaned_content = content_str.replace("```json", "").replace("```", "").strip()
            parsed_json = json.loads(cleaned_content)
            
            return_date_str = parsed_json.get("extracted_return_date")
            is_valid = parsed_json.get("is_valid_proof", False)
            
            current_time = datetime.now()
            days_elapsed = 0
            
            if return_date_str and is_valid:
                try:
                    return_date = datetime.strptime(return_date_str, "%Y-%m-%d")
                    days_elapsed = (current_time - return_date).days
                except ValueError:
                    pass
                    
            if days_elapsed <= 3:
                stage = "merchant_review"
            elif days_elapsed <= 7:
                stage = "merchant_escalation"
            elif days_elapsed <= 14:
                stage = "bank_investigation"
            else:
                stage = "provisional_credit"
                
            return {
                "transaction_id": tool_input.get("transaction_id"),
                "return_date_extracted": return_date_str,
                "is_valid_proof": is_valid,
                "days_elapsed": days_elapsed,
                "refund_stage": stage,
                "vision_notes": parsed_json.get("note", "")
            }
        except Exception as e:
            logger.error(f"[{self.agent_name}] Vision analysis failed: {str(e)}")
            return {"error": f"Vision analysis failed: {str(e)}"}


# Singleton instance
vision_forensics_agent = VisionForensicsAgent()


def execute_vision_forensics_tools(
    tool_steps: List[Dict[str, Any]],
    audit_trail: List[str]
) -> Dict[str, Any]:
    """
    Public interface for executing vision forensics tools.
    
    Args:
        tool_steps: List of vision tool execution plans
        audit_trail: Audit trail to append logs
        
    Returns:
        Dictionary with vision analysis results and updated audit trail
    """
    return vision_forensics_agent.execute_vision_analysis(tool_steps, audit_trail)


# Made with Bob