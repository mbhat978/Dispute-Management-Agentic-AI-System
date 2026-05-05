"""
Fraud Analyst Agent for Banking Dispute Management System

This specialized agent handles all fraud-related analysis including
fraud risk scoring and dispute fraud detection (friendly fraud).
"""

from typing import Dict, Any, List, Tuple
from loguru import logger
from datetime import datetime
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    from .tools_wrapper import calculate_fraud_risk_score_tool, detect_dispute_fraud_tool
except ImportError:
    from agents.tools_wrapper import calculate_fraud_risk_score_tool, detect_dispute_fraud_tool


class FraudAnalystAgent:
    """
    Specialized agent for fraud analysis and detection.
    Handles fraud risk scoring and friendly fraud detection.
    """
    
    def __init__(self):
        self.agent_name = "FraudAnalystAgent"
        
    def execute_fraud_analysis(
        self,
        tool_steps: List[Dict[str, Any]],
        audit_trail: List[str]
    ) -> Dict[str, Any]:
        """
        Execute fraud analysis tools in parallel using ThreadPoolExecutor.
        
        Args:
            tool_steps: List of fraud analysis tool execution plans
            audit_trail: Audit trail to append execution logs
            
        Returns:
            Dictionary with fraud analysis results and updated audit trail
        """
        gathered_data = {}
        
        logger.info(f"[{self.agent_name}] Starting parallel fraud analysis for {len(tool_steps)} tools")
        
        def execute_step(step: Dict[str, Any]) -> Tuple[str, str, Dict[str, Any], Dict[str, Any]]:
            """Execute a single fraud tool step and return results."""
            tool_name = step["tool"]
            tool_input = step["input"]
            data_key = step["data_key"]
            
            logger.info(f"[{self.agent_name}] Executing fraud tool: {tool_name}")
            
            try:
                result = self._execute_fraud_tool(tool_name, tool_input)
                logger.success(f"[{self.agent_name}] Fraud tool {tool_name} completed successfully")
                return tool_name, data_key, tool_input, result
            except Exception as e:
                logger.error(f"[{self.agent_name}] Fraud tool {tool_name} failed: {str(e)}")
                return tool_name, data_key, tool_input, {"error": str(e)}
        
        # Execute fraud tools in parallel using ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=len(tool_steps)) as executor:
            # Submit all tasks
            future_to_step = {executor.submit(execute_step, step): step for step in tool_steps}
            
            # Collect results as they complete
            for future in as_completed(future_to_step):
                try:
                    tool_name, data_key, tool_input, result = future.result()
                    
                    # Store results
                    gathered_data[data_key] = result
                    
                    # Add to audit trail with fraud-specific insights
                    audit_trail.append(
                        f"{self.agent_name} THOUGHT: Need to analyze fraud indicators using {tool_name}"
                    )
                    audit_trail.append(
                        f"{self.agent_name} ACTION: Executing {tool_name} with input {json.dumps(tool_input, default=str)}"
                    )
                    
                    # Log fraud-specific insights
                    if tool_name == "calculate_fraud_risk_score" and "error" not in result:
                        risk_score = result.get("fraud_risk_score", 0)
                        risk_level = result.get("risk_level", "unknown")
                        logger.warning(
                            f"[{self.agent_name}] Fraud Risk Assessment: Score={risk_score}, Level={risk_level}"
                        )
                        audit_trail.append(
                            f"{self.agent_name} OBSERVATION: Fraud risk score calculated - "
                            f"Score: {risk_score}/100, Risk Level: {risk_level.upper()}"
                        )
                    elif tool_name == "detect_dispute_fraud" and "error" not in result:
                        is_friendly_fraud = result.get("is_friendly_fraud", False)
                        propensity_score = result.get("customer_propensity_score", 0)
                        logger.warning(
                            f"[{self.agent_name}] Friendly Fraud Detection: "
                            f"Detected={is_friendly_fraud}, Propensity={propensity_score}"
                        )
                        audit_trail.append(
                            f"{self.agent_name} OBSERVATION: Dispute fraud analysis complete - "
                            f"Friendly Fraud: {is_friendly_fraud}, Customer Propensity: {propensity_score}/100"
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
            f"[{self.agent_name}] Parallel fraud analysis complete. "
            f"Analyzed {len(gathered_data)} fraud indicators"
        )
        
        return {
            "gathered_data": gathered_data,
            "audit_trail": audit_trail
        }
    
    def _execute_fraud_tool(self, tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single fraud analysis tool and return results."""
        
        if tool_name == "calculate_fraud_risk_score":
            logger.info(
                f"[{self.agent_name}] Calculating fraud risk score for "
                f"transaction_id={tool_input.get('transaction_id')}, "
                f"customer_id={tool_input.get('customer_id')}"
            )
            return calculate_fraud_risk_score_tool.invoke(tool_input)
            
        elif tool_name == "detect_dispute_fraud":
            logger.info(
                f"[{self.agent_name}] Detecting friendly fraud patterns for "
                f"customer_id={tool_input.get('customer_id')}"
            )
            return detect_dispute_fraud_tool.invoke(tool_input)
            
        else:
            return {"error": f"Unsupported fraud tool: {tool_name}"}


# Singleton instance
fraud_analyst_agent = FraudAnalystAgent()


def execute_fraud_analysis_tools(
    tool_steps: List[Dict[str, Any]],
    audit_trail: List[str]
) -> Dict[str, Any]:
    """
    Public interface for executing fraud analysis tools.
    
    Args:
        tool_steps: List of fraud tool execution plans
        audit_trail: Audit trail to append logs
        
    Returns:
        Dictionary with fraud analysis results and updated audit trail
    """
    return fraud_analyst_agent.execute_fraud_analysis(tool_steps, audit_trail)


# Made with Bob