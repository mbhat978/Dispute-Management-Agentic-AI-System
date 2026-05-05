"""
Data Retrieval Agent for Banking Dispute Management System

This specialized agent handles all database queries and MCP tool calls
for retrieving transaction data, customer history, and other banking information.
"""

from typing import Dict, Any, List, Tuple
from loguru import logger
from datetime import datetime
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    from .. import mcp_client as banking_tools
except ImportError:
    import mcp_client as banking_tools


class DataRetrievalAgent:
    """
    Specialized agent for executing database and MCP tool calls.
    Handles all data retrieval operations planned by the Investigator Agent.
    """
    
    def __init__(self):
        self.agent_name = "DataRetrievalAgent"
        
    def execute_tools(
        self,
        tool_steps: List[Dict[str, Any]],
        audit_trail: List[str]
    ) -> Dict[str, Any]:
        """
        Execute a list of data retrieval tool steps in parallel using ThreadPoolExecutor.
        
        Args:
            tool_steps: List of tool execution plans from investigator
            audit_trail: Audit trail to append execution logs
            
        Returns:
            Dictionary with gathered data and updated audit trail
        """
        gathered_data = {}
        
        logger.info(f"[{self.agent_name}] Starting parallel data retrieval for {len(tool_steps)} tools")
        
        def execute_step(step: Dict[str, Any]) -> Tuple[str, str, Dict[str, Any], Dict[str, Any]]:
            """Execute a single tool step and return results."""
            tool_name = step["tool"]
            tool_input = step["input"]
            data_key = step["data_key"]
            
            logger.info(f"[{self.agent_name}] Executing tool: {tool_name}")
            
            try:
                result = self._execute_single_tool(tool_name, tool_input)
                logger.info(f"[{self.agent_name}] Tool {tool_name} completed successfully")
                return tool_name, data_key, tool_input, result
            except Exception as e:
                logger.error(f"[{self.agent_name}] Tool {tool_name} failed: {str(e)}")
                return tool_name, data_key, tool_input, {"error": str(e)}
        
        # Execute tools in parallel using ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=len(tool_steps)) as executor:
            # Submit all tasks
            future_to_step = {executor.submit(execute_step, step): step for step in tool_steps}
            
            # Collect results as they complete
            for future in as_completed(future_to_step):
                try:
                    tool_name, data_key, tool_input, result = future.result()
                    
                    # Store results
                    gathered_data[data_key] = result
                    
                    # Add to audit trail
                    audit_trail.append(
                        f"{self.agent_name} ACTION: Executing {tool_name} with input {json.dumps(tool_input, default=str)}"
                    )
                    audit_trail.append(
                        f"{self.agent_name} OBSERVATION: {tool_name} returned {json.dumps(result, default=str)}"
                    )
                except Exception as e:
                    step = future_to_step[future]
                    tool_name = step["tool"]
                    logger.error(f"[{self.agent_name}] Tool execution failed: {tool_name} - {str(e)}")
                    audit_trail.append(f"{self.agent_name} ERROR: {tool_name} failed - {str(e)}")
        
        logger.success(f"[{self.agent_name}] Parallel data retrieval complete. Retrieved {len(gathered_data)} data points")
        
        return {
            "gathered_data": gathered_data,
            "audit_trail": audit_trail
        }
    
    def _execute_single_tool(self, tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single MCP tool and return results."""
        
        # Transaction and customer data tools
        if tool_name == "get_transaction_details":
            return banking_tools.get_transaction_details(tool_input["transaction_id"])
            
        elif tool_name == "get_customer_history":
            return banking_tools.get_customer_history(
                tool_input["customer_id"],
                tool_input.get("limit", 5)
            )
            
        elif tool_name == "check_atm_logs":
            return banking_tools.check_atm_logs(tool_input["transaction_id"])
            
        elif tool_name == "get_loan_details":
            return banking_tools.get_loan_details(tool_input["customer_id"])
            
        elif tool_name == "check_merchant_refund_status":
            return banking_tools.check_merchant_refund_status(tool_input["transaction_id"])
            
        elif tool_name == "check_duplicate_transactions":
            trans_details = banking_tools.get_transaction_details(
                tool_input.get("transaction_id", 0)
            )
            if not trans_details:
                trans_details = {}
            return banking_tools.check_duplicate_transactions(
                customer_id=tool_input["customer_id"],
                merchant_name=trans_details.get("merchant_name", ""),
                amount=trans_details.get("amount", 0),
                date=trans_details.get("transaction_date", ""),
                time_window_hours=24
            )
            
        elif tool_name == "verify_receipt_amount":
            return banking_tools.verify_receipt_amount(
                tool_input["transaction_id"],
                tool_input.get("claimed_amount", 0.0)
            )
            
        elif tool_name == "get_delivery_tracking_status":
            return banking_tools.get_delivery_tracking_status(tool_input["transaction_id"])
            
        elif tool_name == "check_subscription_status":
            return banking_tools.check_subscription_status(
                tool_input["customer_id"],
                tool_input.get("merchant_name", "")
            )
            
        elif tool_name == "verify_subscription_cancellation":
            return banking_tools.verify_subscription_cancellation(
                tool_input["customer_id"],
                tool_input.get("merchant_name", ""),
                tool_input.get("cancellation_date", "")
            )
            
        elif tool_name == "get_refund_timeline":
            return banking_tools.get_refund_timeline(tool_input["transaction_id"])
            
        elif tool_name == "check_merchant_reputation_score":
            return banking_tools.check_merchant_reputation_score(
                tool_input.get("merchant_name", "")
            )
            
        elif tool_name == "get_merchant_dispute_history":
            return banking_tools.get_merchant_dispute_history(
                tool_input.get("merchant_name", "")
            )
            
        else:
            return {"error": f"Unsupported tool: {tool_name}"}


# Singleton instance
data_retrieval_agent = DataRetrievalAgent()


def execute_data_retrieval_tools(
    tool_steps: List[Dict[str, Any]],
    audit_trail: List[str]
) -> Dict[str, Any]:
    """
    Public interface for executing data retrieval tools.
    
    Args:
        tool_steps: List of tool execution plans
        audit_trail: Audit trail to append logs
        
    Returns:
        Dictionary with gathered data and updated audit trail
    """
    return data_retrieval_agent.execute_tools(tool_steps, audit_trail)


# Made with Bob