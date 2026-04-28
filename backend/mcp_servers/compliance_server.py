from mcp.server.fastmcp import FastMCP


mcp = FastMCP("Compliance", port=8002)


BANK_DISPUTE_POLICIES_MD = """
# Bank Dispute Policies

Rule 1: Duplicate transactions within 5 minutes are auto-approved. If two substantially identical card transactions for the same customer and merchant occur within a five-minute window, the dispute may be automatically approved for refund.

Rule 2: ATM hardware fault cases are auto-approved. If ATM logs confirm a hardware fault, cash dispense failure, or terminal malfunction tied to the disputed withdrawal, the refund should be automatically approved.

Rule 3: Loan and EMI disputes require human review. Any dispute involving loan repayment, EMI processing, foreclosure, or loan servicing must be routed for human review due to compliance and regulatory sensitivity.

Rule 4: High-value disputes above $10,000 require human review. These cases need enhanced scrutiny and senior authorization before any final action is taken.

Rule 5: International fraud anomalies may be auto-approved. If a disputed transaction is international and the customer history shows no normal pattern of international usage, the case may be approved and the card should be blocked as a precaution.

Rule 6: Failed transactions with account deduction are auto-approved. If transaction records show a failed status while customer funds were debited, the dispute should be approved for refund.

Rule 7: Insufficient, ambiguous, or contradictory evidence requires human review. When evidence does not clearly support approval or rejection, the case must be escalated to a human reviewer.

Rule 8: Gold and Platinum customers require higher scrutiny for auto-decisions. Premium-tier customers should have stronger supporting evidence before fully automated resolution is used.

Rule 9: Merchant disputes for unreceived services require human review. Chargebacks should be initiated, but auto-approvals are not permitted until evidence is manually reviewed.

Rule 10: Incorrect amount disputes can be auto-approved for a partial refund ONLY IF the verified receipt amount is lower than the billed ledger amount.

Rule 11: For 'Refund Not Received' cases, if the gateway status is 'Refund Pending at Gateway', the dispute must be auto-rejected with instructions for the customer to wait 3-5 business days.

Rule 12: For 'Refund Not Received' cases, if the merchant has not initiated a refund and the customer provides valid return evidence (receipt, tracking, etc.), the dispute should be auto-approved with provisional credit issued immediately.
""".strip()


@mcp.tool()
def query_compliance_policy(query: str) -> dict:
    """
    Search the bank dispute policy markdown and return the most relevant paragraph.

    Args:
        query: Natural language query describing the dispute or policy question.

    Returns:
        Dictionary containing the matched policy paragraph and metadata.
    """
    normalized_query = query.lower()
    paragraphs = [paragraph.strip() for paragraph in BANK_DISPUTE_POLICIES_MD.split("\n\n") if paragraph.strip()]

    scored_matches = []
    for paragraph in paragraphs:
        paragraph_lower = paragraph.lower()
        score = 0
        for keyword in normalized_query.split():
            cleaned_keyword = keyword.strip(".,:;!?()[]{}\"'")
            if cleaned_keyword and cleaned_keyword in paragraph_lower:
                score += 1
        if score > 0:
            scored_matches.append((score, paragraph))

    if scored_matches:
        scored_matches.sort(key=lambda item: item[0], reverse=True)
        best_match = scored_matches[0][1]
        return {
            "query": query,
            "matched": True,
            "policy_text": best_match,
            "source": "BANK_DISPUTE_POLICIES_MD",
        }

    return {
        "query": query,
        "matched": False,
        "policy_text": "No directly matching compliance policy found. Escalate to human review when policy guidance is unclear.",
        "source": "BANK_DISPUTE_POLICIES_MD",
    }


if __name__ == "__main__":
    mcp.run(transport="sse")

# Made with Bob
