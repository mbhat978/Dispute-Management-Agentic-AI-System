"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import { AlertCircle, Brain, Building2, CheckCircle2, ChevronDown, ChevronUp, Landmark, Radio, Send, WifiOff, Upload, X } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

interface Customer {
  id: number;
  name: string;
  account_tier: string;
  current_account_balance: number;
}

interface Transaction {
  id: number;
  customer_id: number;
  amount: number;
  merchant_name: string;
  transaction_date: string;
  status: string;
  is_international: boolean;
  transaction_type?: string;
}

interface ProcessDisputeResponse {
  status: string;
  ticket_id: number;
  customer_id: number;
  customer_query: string;
  dispute_category: string;
  final_decision: string;
  gathered_data: Record<string, unknown>;
  audit_trail: unknown[];
  message: string;
  decision_reasoning?: {
    justification?: string;
  };
}

interface PastDispute {
  ticket_id: number;
  status: string;
  dispute_category: string;
  final_decision: string;
  created_at?: string;
  decision_reasoning?: any;
  audit_trail?: any[];
}

const API_BASE_URL = "http://localhost:8000";

interface ApiErrorResponse {
  status?: string;
  error?: {
    code?: string;
    message?: string;
    details?: Record<string, unknown>;
  };
  detail?: string | ApiErrorResponse;
}

function getErrorMessage(errorData: ApiErrorResponse | null | undefined, fallback: string): string {
  if (!errorData) return fallback;
  if (typeof errorData.detail === "string") return errorData.detail;
  if (typeof errorData.error?.message === "string") return errorData.error.message;
  if (typeof errorData.detail === "object" && errorData.detail && "error" in errorData.detail) {
    const nested = errorData.detail as ApiErrorResponse;
    if (typeof nested.error?.message === "string") return nested.error.message;
  }
  return fallback;
}

function formatDecisionMessage(decision: string): string {
  switch (decision) {
    case "auto_approved":
      return "Your refund has been auto-approved.";
    case "human_review_required":
      return "Your case has been forwarded to a specialist.";
    case "auto_rejected":
      return "Your dispute could not be auto-approved and has been declined.";
    default:
      return "Your dispute has been received and is under review.";
  }
}

interface LiveFeedState {
  dispute_category?: string | null;
  final_decision?: string | null;
  triage_confidence?: number | null;
  investigation_confidence?: number | null;
  decision_confidence?: number | null;
  audit_trail_count?: number;
  gathered_data_keys?: string[];
}

interface LiveFeedEvent {
  id: string;
  timestamp: string;
  eventType: string;
  message: string;
  ticket_id?: number | null;
  node?: string | null;
  final_decision?: string | null;
  dispute_category?: string | null;
  state?: LiveFeedState;
  isAgentUpdate?: boolean;
}

function formatStatus(status: string): string {
  return status
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

function formatDisputeCategory(category: string): string {
  const categoryMap: Record<string, string> = {
    "fraud": "Fraudulent Transaction",
    "duplicate": "Duplicate Charge",
    "atm_failure": "ATM Failure",
    "merchant_dispute": "Merchant Dispute",
    "failed_transaction": "Failed Transaction",
    "loan_dispute": "Loan Dispute",
    "refund_not_received": "Refund Not Received",
    "unknown": "Under Review"
  };
  
  return categoryMap[category] || formatStatus(category);
}

function formatEventLabel(eventType: string): string {
  return eventType
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

function getEventBadgeClass(eventType: string): string {
  switch (eventType) {
    case "processing_started":
      return "bg-blue-500 hover:bg-blue-600";
    case "agent_update":
      return "bg-purple-500 hover:bg-purple-600";
    case "processing_completed":
      return "bg-green-500 hover:bg-green-600";
    case "processing_failed":
      return "bg-red-500 hover:bg-red-600";
    case "connection":
      return "bg-emerald-500 hover:bg-emerald-600";
    case "heartbeat":
      return "bg-gray-500 hover:bg-gray-600";
    default:
      return "";
  }
}

function getNodeBadgeClass(node: string): { className: string; label: string } {
  switch (node.toLowerCase()) {
    case "triage":
      return { className: "bg-blue-500 hover:bg-blue-600 text-white", label: "🔍 Triage" };
    case "investigator":
      return { className: "bg-purple-500 hover:bg-purple-600 text-white", label: "🔬 Investigator" };
    case "decision":
      return { className: "bg-green-500 hover:bg-green-600 text-white", label: "⚖️ Decision" };
    case "re_investigate":
      return { className: "bg-orange-500 hover:bg-orange-600 text-white", label: "🔄 Re-Investigate" };
    default:
      return { className: "bg-slate-500 hover:bg-slate-600 text-white", label: `📋 ${node}` };
  }
}

function LiveAiFeed({
  activeTicketId,
  onProcessingCompleted
}: {
  activeTicketId: number | null;
  onProcessingCompleted?: () => void;
}) {
  const [events, setEvents] = useState<LiveFeedEvent[]>([]);
  const [connectionStatus, setConnectionStatus] = useState<"idle" | "connecting" | "connected" | "disconnected">("idle");
  const feedContainerRef = useRef<HTMLDivElement>(null);
  const feedEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new events arrive
  useEffect(() => {
    if (feedContainerRef.current) {
      feedContainerRef.current.scrollTo({
        top: feedContainerRef.current.scrollHeight,
        behavior: "smooth",
      });
      return;
    }

    feedEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [events]);

  useEffect(() => {
    setEvents([]); // Clear the feed history for the new dispute
    setConnectionStatus("connecting");
    console.log("[LiveAiFeed] Connecting to SSE stream...");

    let eventSource: EventSource | null = null;
    let reconnectTimeout: NodeJS.Timeout | null = null;

    const connect = () => {
      try {
        eventSource = new EventSource(`${API_BASE_URL}/api/disputes/stream`);

        const appendEvent = (eventType: string, rawData: string) => {
          try {
            if (eventType === "heartbeat") {
              return;
            }

            const parsed = JSON.parse(rawData) as {
              type?: string;
              timestamp?: string;
              message?: string;
              ticket_id?: number | null;
              node?: string | null;
              agent_name?: string | null;
              activity_summary?: string | null;
              final_decision?: string | null;
              dispute_category?: string | null;
              state?: LiveFeedState;
              data?: {
                type?: string;
                timestamp?: string;
                message?: string;
                ticket_id?: number | null;
                node?: string | null;
                agent_name?: string | null;
                activity_summary?: string | null;
                final_decision?: string | null;
                dispute_category?: string | null;
                state?: LiveFeedState;
              };
            };

            const payload = parsed.data ?? parsed;
            const normalizedEventType = payload.type ?? parsed.type ?? eventType;
            const isAgentUpdate = normalizedEventType === "agent_update";
            const resolvedNode = payload.node ?? null;
            const resolvedMessage =
              payload.message ??
              payload.activity_summary ??
              (isAgentUpdate && resolvedNode ? `${formatStatus(resolvedNode)} agent is reviewing your dispute.` : "AI workflow update received");

            console.log(`[LiveAiFeed] Received ${eventType}:`, parsed);

            if (activeTicketId != null && payload.ticket_id != null && payload.ticket_id !== activeTicketId) {
              console.log(`[LiveAiFeed] Filtering out event for ticket ${payload.ticket_id} (active: ${activeTicketId})`);
              return;
            }

            setEvents((current) => {
              const nextEvent: LiveFeedEvent = {
                id: `${normalizedEventType}-${payload.timestamp ?? parsed.timestamp ?? Date.now()}-${current.length}`,
                timestamp: payload.timestamp ?? parsed.timestamp ?? new Date().toISOString(),
                eventType: normalizedEventType,
                message: resolvedMessage,
                ticket_id: payload.ticket_id,
                node: resolvedNode,
                final_decision: payload.final_decision ?? payload.state?.final_decision ?? null,
                dispute_category: payload.dispute_category ?? payload.state?.dispute_category ?? null,
                state: payload.state,
                isAgentUpdate,
              };

              if (activeTicketId == null && payload.ticket_id == null && normalizedEventType !== "connection") {
                console.log(`[LiveAiFeed] Filtering out ${normalizedEventType} event (no active ticket)`);
                return current;
              }

              console.log(`[LiveAiFeed] Adding event to feed:`, nextEvent);
              return [...current, nextEvent].slice(-30);
            });
          } catch (streamError) {
            console.error("[LiveAiFeed] Failed to parse event:", streamError, rawData);
          }
        };

        const registerEventType = (eventType: string) => {
          eventSource?.addEventListener(eventType, (event) => {
            setConnectionStatus("connected");
            appendEvent(eventType, (event as MessageEvent).data);
            
            // Call the callback when processing completes successfully
            if ((eventType === "processing_completed" || eventType === "resume_completed") && onProcessingCompleted) {
              console.log("[LiveAiFeed] Processing completed - triggering data refresh");
              onProcessingCompleted();
            }
          });
        };

        registerEventType("connection");
        registerEventType("processing_started");
        registerEventType("agent_update");
        registerEventType("processing_completed");
        registerEventType("processing_failed");
        registerEventType("resume_started");
        registerEventType("resume_completed");
        registerEventType("heartbeat");

        eventSource.onopen = () => {
          console.log("[LiveAiFeed] SSE connection opened successfully");
          setConnectionStatus("connected");
        };

        eventSource.onerror = (error) => {
          console.error("[LiveAiFeed] SSE connection error:", {
            readyState: eventSource?.readyState,
            url: `${API_BASE_URL}/api/disputes/stream`,
            error: error
          });
          setConnectionStatus("disconnected");
          
          // Close the failed connection
          if (eventSource) {
            eventSource.close();
          }
        };
      } catch (err) {
        console.error("[LiveAiFeed] Failed to create EventSource:", err);
        setConnectionStatus("disconnected");
      }
    };

    connect();

    return () => {
      console.log("[LiveAiFeed] Cleaning up SSE connection");
      if (reconnectTimeout) {
        clearTimeout(reconnectTimeout);
      }
      if (eventSource) {
        eventSource.close();
      }
      setConnectionStatus("disconnected");
    };
  }, [activeTicketId]);

  const statusBadge = useMemo(() => {
    switch (connectionStatus) {
      case "idle":
        return {
          label: "Waiting",
          className: "bg-slate-500 hover:bg-slate-600",
          icon: <Radio className="h-3.5 w-3.5 mr-1" />,
        };
      case "connected":
        return {
          label: "Connected",
          className: "bg-green-500 hover:bg-green-600",
          icon: <Radio className="h-3.5 w-3.5 mr-1" />,
        };
      case "connecting":
        return {
          label: "Connecting",
          className: "bg-yellow-500 hover:bg-yellow-600 text-black",
          icon: <Radio className="h-3.5 w-3.5 mr-1 animate-pulse" />,
        };
      default:
        return {
          label: "Disconnected",
          className: "bg-red-500 hover:bg-red-600",
          icon: <WifiOff className="h-3.5 w-3.5 mr-1" />,
        };
    }
  }, [connectionStatus]);

  return (
    <Card className="border-slate-200 shadow-sm">
      <CardHeader>
        <div className="flex items-center justify-between gap-4">
          <div>
            <CardTitle className="flex items-center gap-2 text-slate-900">
              <Brain className="h-5 w-5 text-violet-600" />
              Live AI Feed
            </CardTitle>
            <CardDescription>
              Follow your dispute as our AI agents review evidence and work toward a decision.
            </CardDescription>
          </div>
          <Badge className={statusBadge.className}>
            {statusBadge.icon}
            {statusBadge.label}
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        {events.length === 0 ? (
          <div className="rounded-md border border-dashed p-6 text-sm text-muted-foreground">
            {!activeTicketId
              ? "Submit a dispute to start the live agent activity feed."
              : "Waiting for live updates for your submitted dispute."}
          </div>
        ) : (
          <div ref={feedContainerRef} className="space-y-3 max-h-[420px] overflow-y-auto pr-2">
            {events.map((event) => {
              const isAgentUpdate = event.isAgentUpdate ?? event.eventType === "agent_update";
              const nodeBadge = event.node ? getNodeBadgeClass(event.node) : null;
              
              return (
                <div
                  key={event.id}
                  className={`rounded-lg border p-4 ${
                    isAgentUpdate
                      ? "border-purple-300 bg-gradient-to-r from-purple-50 to-blue-50 shadow-sm"
                      : "border-slate-200 bg-slate-50"
                  }`}
                >
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      {isAgentUpdate ? (
                        <>
                          {nodeBadge && (
                            <Badge className={nodeBadge.className}>
                              {nodeBadge.label}
                            </Badge>
                          )}
                          <Badge className="bg-slate-800 hover:bg-slate-900 text-white">
                            <Brain className="mr-1 h-3.5 w-3.5" />
                            AI Thinking
                          </Badge>
                        </>
                      ) : (
                        <Badge className={getEventBadgeClass(event.eventType)}>
                          {formatEventLabel(event.eventType)}
                        </Badge>
                      )}
                      {!isAgentUpdate && event.node && (
                        <Badge variant="outline">
                          Step: {event.node}
                        </Badge>
                      )}
                      {event.ticket_id != null && (
                        <Badge variant="secondary">
                          Ticket #{event.ticket_id}
                        </Badge>
                      )}
                    </div>
                    <span className="text-xs text-muted-foreground">
                      {new Date(event.timestamp).toLocaleTimeString()}
                    </span>
                  </div>

                  <p className={`mt-3 text-sm leading-relaxed ${
                    isAgentUpdate ? "font-medium text-slate-800" : "text-slate-700"
                  }`}>
                    {isAgentUpdate && "🤖 "}{event.message}
                  </p>

                  {(event.dispute_category || event.final_decision || event.state) && (
                    <div className="mt-3 grid gap-2 md:grid-cols-2">
                      {(event.dispute_category || event.state?.dispute_category) && (
                        <div className="rounded-md bg-white p-3 text-xs text-slate-700">
                          <span className="font-semibold">Category:</span>{" "}
                          {formatDisputeCategory(event.dispute_category ?? event.state?.dispute_category ?? "")}
                        </div>
                      )}
                      {(event.final_decision || event.state?.final_decision) && (
                        <div className="rounded-md bg-white p-3 text-xs text-slate-700">
                          <span className="font-semibold">Decision:</span>{" "}
                          {formatStatus(event.final_decision ?? event.state?.final_decision ?? "")}
                        </div>
                      )}
                      {typeof event.state?.triage_confidence === "number" && (
                        <div className="rounded-md bg-white p-3 text-xs text-slate-700">
                          <span className="font-semibold">Triage Confidence:</span>{" "}
                          {(event.state.triage_confidence * 100).toFixed(1)}%
                        </div>
                      )}
                      {typeof event.state?.investigation_confidence === "number" && (
                        <div className="rounded-md bg-white p-3 text-xs text-slate-700">
                          <span className="font-semibold">Investigation Confidence:</span>{" "}
                          {(event.state.investigation_confidence * 100).toFixed(1)}%
                        </div>
                      )}
                      {typeof event.state?.decision_confidence === "number" && (
                        <div className="rounded-md bg-white p-3 text-xs text-slate-700">
                          <span className="font-semibold">Decision Confidence:</span>{" "}
                          {(event.state.decision_confidence * 100).toFixed(1)}%
                        </div>
                      )}
                      {typeof event.state?.audit_trail_count === "number" && (
                        <div className="rounded-md bg-white p-3 text-xs text-slate-700">
                          <span className="font-semibold">Audit Trail Entries:</span>{" "}
                          {event.state.audit_trail_count}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
            <div ref={feedEndRef} />
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export default function CustomerPortalPage() {
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [selectedCustomerId, setSelectedCustomerId] = useState("");
  const [selectedTransactionId, setSelectedTransactionId] = useState("");
  const [disputeReason, setDisputeReason] = useState("");
  const [customersLoading, setCustomersLoading] = useState(true);
  const [transactionsLoading, setTransactionsLoading] = useState(false);
  const [submitLoading, setSubmitLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [decisionResult, setDecisionResult] = useState<ProcessDisputeResponse | null>(null);
  const [showDecisionModal, setShowDecisionModal] = useState(false);
  const [activeStreamTicketId, setActiveStreamTicketId] = useState<number | null>(null);

  // New state for structured dispute form
  const [disputeType, setDisputeType] = useState("");
  const [loanAccountNumber, setLoanAccountNumber] = useState("");
  const [emiAmount, setEmiAmount] = useState("");
  const [atmLocation, setAtmLocation] = useState("");
  const [atmWithdrawalAmount, setAtmWithdrawalAmount] = useState("");
  const [merchantReceipt, setMerchantReceipt] = useState<File | null>(null);
  const [expectedAmount, setExpectedAmount] = useState("");
  const [chargedAmount, setChargedAmount] = useState("");
  const [additionalDetails, setAdditionalDetails] = useState("");

  // State for past disputes
  const [pastDisputes, setPastDisputes] = useState<PastDispute[]>([]);
  const [pastDisputesLoading, setPastDisputesLoading] = useState(false);
  const [expandedDisputeId, setExpandedDisputeId] = useState<number | null>(null);

  // Suggestions based on dispute type
  const getDescriptionSuggestions = (type: string): string[] => {
    switch (type) {
      case "fraud":
        return [
          "I did not authorize this transaction",
          "My card was stolen and used without permission",
          "I noticed unauthorized charges on my account",
          "This transaction was made after I reported my card lost",
          "I don't recognize this merchant or transaction"
        ];
      case "atm_failure":
        return [
          "ATM did not dispense cash but my account was debited",
          "ATM showed error but money was deducted",
          "Cash withdrawal failed but amount was charged",
          "ATM malfunctioned during transaction",
          "Partial cash dispensed but full amount debited"
        ];
      case "emi_issue":
        return [
          "EMI amount charged is incorrect",
          "Double EMI deduction in the same month",
          "EMI deducted after loan closure",
          "Wrong EMI amount as per loan agreement",
          "EMI not reflecting despite payment"
        ];
      case "incorrect_amount":
        return [
          "Charged amount is higher than the bill",
          "Wrong amount debited from my account",
          "Amount doesn't match the receipt",
          "Overcharged for the purchase",
          "Currency conversion rate is incorrect"
        ];
      case "merchant_dispute":
        return [
          "Goods not received as described",
          "Service not provided as promised",
          "Merchant refused to honor refund policy",
          "Product is defective or damaged",
          "Merchant charged wrong amount"
        ];
      case "duplicate":
        return [
          "Same transaction charged twice",
          "Duplicate charge for single purchase",
          "Multiple debits for one transaction",
          "Charged twice at the same merchant",
          "Duplicate EMI deduction"
        ];
      case "failed_transaction":
        return [
          "Transaction failed but amount was debited",
          "Payment declined but money deducted",
          "Transaction timeout but account charged",
          "Failed online payment but amount debited",
          "Transaction error but money taken"
        ];
      case "refund_not_received":
        return [
          "Refund not credited after return",
          "Cancelled order but refund pending",
          "Merchant promised refund but not received",
          "Refund initiated but not reflected in account",
          "Partial refund received instead of full amount"
        ];
      default:
        return [];
    }
  };

  const descriptionSuggestions = useMemo(() => getDescriptionSuggestions(disputeType), [disputeType]);

  // Reusable function to fetch customers
  const fetchCustomers = async () => {
    try {
      setCustomersLoading(true);
      setError(null);
      const response = await fetch(`${API_BASE_URL}/api/customers`);
      if (!response.ok) {
        const errorData: ApiErrorResponse = await response.json().catch(() => ({}));
        throw new Error(getErrorMessage(errorData, `Failed to fetch customers: ${response.statusText}`));
      }
      const data = await response.json();
      setCustomers(data.customers ?? []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load customers");
      console.error("Error fetching customers:", err);
    } finally {
      setCustomersLoading(false);
    }
  };

  // Reusable function to fetch transactions
  const fetchTransactions = async (customerId?: string) => {
    const targetCustomerId = customerId ?? selectedCustomerId;
    if (!targetCustomerId) {
      setTransactions([]);
      setSelectedTransactionId("");
      return;
    }
    try {
      setTransactionsLoading(true);
      setError(null);
      setSelectedTransactionId("");
      const response = await fetch(`${API_BASE_URL}/api/customers/${targetCustomerId}/transactions`);
      if (!response.ok) {
        const errorData: ApiErrorResponse = await response.json().catch(() => ({}));
        throw new Error(getErrorMessage(errorData, `Failed to fetch transactions: ${response.statusText}`));
      }
      const data = await response.json();
      setTransactions(data.transactions ?? []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load transactions");
      setTransactions([]);
      console.error("Error fetching transactions:", err);
    } finally {
      setTransactionsLoading(false);
    }
  };

  // Fetch past disputes for a customer
  const fetchPastDisputes = async (customerId: string) => {
    if (!customerId) {
      setPastDisputes([]);
      return;
    }

    setPastDisputesLoading(true);

    try {
      const response = await fetch(`${API_BASE_URL}/api/customers/${customerId}/disputes`);
      if (!response.ok) {
        throw new Error("Failed to fetch past disputes");
      }
      const data = await response.json();
      setPastDisputes(data.disputes || []);
    } catch (err) {
      console.error("Error fetching past disputes:", err);
      setPastDisputes([]);
    } finally {
      setPastDisputesLoading(false);
    }
  };

  useEffect(() => {
    fetchCustomers();
  }, []);

  useEffect(() => {
    fetchTransactions();
    if (selectedCustomerId) {
      fetchPastDisputes(selectedCustomerId);
    }
  }, [selectedCustomerId]);

  const selectedCustomer = useMemo(
    () => customers.find((c) => c.id === Number(selectedCustomerId)) ?? null,
    [customers, selectedCustomerId]
  );

  const selectedTransaction = useMemo(
    () => transactions.find((t) => t.id === Number(selectedTransactionId)) ?? null,
    [transactions, selectedTransactionId]
  );

  // Build comprehensive query string from all form inputs
  const buildComprehensiveQuery = (): string => {
    let query = `Dispute Type: ${disputeType}\n\n`;
    
    // Add base description if provided
    if (disputeReason.trim()) {
      query += `Description: ${disputeReason.trim()}\n\n`;
    }

    // Add type-specific fields
    switch (disputeType) {
      case "fraud":
        query += "Issue: Fraudulent/unauthorized transaction detected.\n";
        if (additionalDetails.trim()) {
          query += `Additional Details: ${additionalDetails.trim()}\n`;
        }
        break;
      
      case "atm_failure":
        query += "Issue: ATM did not dispense cash but account was debited.\n";
        if (atmLocation.trim()) {
          query += `ATM Location: ${atmLocation.trim()}\n`;
        }
        if (atmWithdrawalAmount.trim()) {
          query += `Withdrawal Amount: $${atmWithdrawalAmount.trim()}\n`;
        }
        if (additionalDetails.trim()) {
          query += `Additional Details: ${additionalDetails.trim()}\n`;
        }
        break;
      
      case "emi_issue":
        query += "Issue: EMI/Loan payment dispute.\n";
        if (loanAccountNumber.trim()) {
          query += `Loan Account Number: ${loanAccountNumber.trim()}\n`;
        }
        if (emiAmount.trim()) {
          query += `EMI Amount: $${emiAmount.trim()}\n`;
        }
        if (additionalDetails.trim()) {
          query += `Additional Details: ${additionalDetails.trim()}\n`;
        }
        break;
      
      case "incorrect_amount":
        query += "Issue: Incorrect amount charged.\n";
        if (expectedAmount.trim()) {
          query += `Expected Amount: $${expectedAmount.trim()}\n`;
        }
        if (chargedAmount.trim()) {
          query += `Charged Amount: $${chargedAmount.trim()}\n`;
        }
        if (merchantReceipt) {
          query += `Merchant Receipt: ${merchantReceipt.name} (attached)\n`;
        }
        if (additionalDetails.trim()) {
          query += `Additional Details: ${additionalDetails.trim()}\n`;
        }
        break;
      
      case "merchant_dispute":
        query += "Issue: Dispute with merchant regarding goods/services.\n";
        if (merchantReceipt) {
          query += `Merchant Receipt: ${merchantReceipt.name} (attached)\n`;
        }
        if (additionalDetails.trim()) {
          query += `Additional Details: ${additionalDetails.trim()}\n`;
        }
        break;
      
      case "duplicate":
        query += "Issue: Duplicate charge detected.\n";
        if (additionalDetails.trim()) {
          query += `Additional Details: ${additionalDetails.trim()}\n`;
        }
        break;
      
      case "failed_transaction":
        query += "Issue: Transaction failed but amount was debited.\n";
        if (additionalDetails.trim()) {
          query += `Additional Details: ${additionalDetails.trim()}\n`;
        }
        break;
      
      case "refund_not_received":
        query += "Issue: Refund not received for returned goods/cancelled service.\n";
        if (additionalDetails.trim()) {
          query += `Additional Details: ${additionalDetails.trim()}\n`;
        }
        break;
      
      default:
        if (additionalDetails.trim()) {
          query += `Details: ${additionalDetails.trim()}\n`;
        }
    }

    return query.trim();
  };

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedCustomerId || !selectedTransactionId || !disputeType) {
      setError("Please select a customer, choose a transaction, and select a dispute type.");
      return;
    }
    if (!disputeReason.trim()) {
      setError("Please provide a brief description of the issue.");
      return;
    }
    
    // Build comprehensive query from all form fields
    const comprehensiveQuery = buildComprehensiveQuery();
    
    try {
      setSubmitLoading(true);
      setError(null);
      setDecisionResult(null);
      setShowDecisionModal(false);
      setActiveStreamTicketId(null); // Reset to allow the feed to listen to the new dispute

      const response = await fetch(`${API_BASE_URL}/api/disputes/process`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          transaction_id: Number(selectedTransactionId),
          customer_id: Number(selectedCustomerId),
          customer_query: comprehensiveQuery,
        }),
      });

      if (!response.ok) {
        const errorData: ApiErrorResponse = await response.json().catch(() => ({}));
        throw new Error(getErrorMessage(errorData, `Failed to process dispute: ${response.statusText}`));
      }

      const data: ProcessDisputeResponse = await response.json();
      setActiveStreamTicketId(data.ticket_id);
      setDecisionResult(data);
      setShowDecisionModal(true);
      
      // Reset form (Keep customer selected so history stays visible)
      setSelectedTransactionId("");
      setDisputeType("");
      setDisputeReason("");
      setLoanAccountNumber("");
      setEmiAmount("");
      setAtmLocation("");
      setAtmWithdrawalAmount("");
      setMerchantReceipt(null);
      setExpectedAmount("");
      setChargedAmount("");
      setAdditionalDetails("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to submit dispute");
    } finally {
      setSubmitLoading(false);
    }
  }

  return (
    <>
      {showDecisionModal && decisionResult && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/60 px-4">
          <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl">
            <div className="mb-4 flex items-center gap-3">
              <div className="rounded-full bg-green-100 p-2 text-green-700">
                <CheckCircle2 className="h-6 w-6" />
              </div>
              <div>
                <p className="text-sm font-medium text-slate-500">AI Review Complete</p>
                <h3 className="text-xl font-semibold text-slate-900">Decision available</h3>
              </div>
            </div>

            <div className="space-y-4">
              <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                <p className="text-sm text-slate-600">Immediate outcome</p>
                <p className="mt-1 text-lg font-semibold text-slate-900">
                  {formatDecisionMessage(decisionResult.final_decision)}
                </p>
              </div>

              <div className="space-y-2 text-sm text-slate-600">
                <p>
                  <span className="font-medium text-slate-900">Reference ID:</span> #{decisionResult.ticket_id}
                </p>
                <p>
                  <span className="font-medium text-slate-900">AI category:</span> {formatDisputeCategory(decisionResult.dispute_category)}
                </p>
              </div>
              
              {decisionResult.decision_reasoning?.justification && (
                <div className="rounded-xl border border-blue-200 bg-blue-50 p-4">
                  <p className="text-sm font-semibold text-blue-900 mb-1">AI Reasoning</p>
                  <p className="text-sm text-blue-800 leading-relaxed">{decisionResult.decision_reasoning.justification}</p>
                </div>
              )}

              <Button
                type="button"
                className="w-full bg-blue-900 hover:bg-blue-800"
                onClick={() => {
                  setShowDecisionModal(false);
                  if (decisionResult) {
                    setExpandedDisputeId(decisionResult.ticket_id);
                    fetchPastDisputes(selectedCustomerId);
                    setTimeout(() => {
                      document.getElementById('dispute-history-card')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
                    }, 150);
                  }
                }}
              >
                Close & View History
              </Button>
            </div>
          </div>
        </div>
      )}

      <div className="min-h-screen bg-slate-100">
      <div className="border-b bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="rounded-full bg-blue-900 p-2 text-white">
              <Landmark className="h-5 w-5" />
            </div>
            <div>
              <p className="text-sm font-medium uppercase tracking-[0.2em] text-slate-500">Retail Banking</p>
              <h1 className="text-xl font-bold text-slate-900">Customer Service Portal</h1>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <Link href="/">
              <Button variant="outline">
                Log Out
              </Button>
            </Link>
          </div>
        </div>
      </div>

      <div className="mx-auto max-w-7xl px-6 py-8">
        <div className="grid gap-6 lg:grid-cols-[1.6fr_1fr]">
          <div className="space-y-6">
            <div className="rounded-2xl bg-gradient-to-r from-blue-950 via-blue-900 to-slate-800 p-8 text-white shadow-lg">
              <p className="text-sm uppercase tracking-[0.3em] text-blue-200">Dispute Resolution</p>
              <h2 className="mt-3 text-3xl font-semibold">Report an issue with a recent banking transaction</h2>
              <p className="mt-3 max-w-2xl text-sm text-blue-100">
                Use this secure form to select your customer profile, review recent transactions, and describe what went wrong in your own words.
              </p>
              <div className="mt-6 flex flex-wrap gap-3 text-sm">
                <div className="rounded-full border border-white/20 bg-white/10 px-4 py-2">Card payments</div>
                <div className="rounded-full border border-white/20 bg-white/10 px-4 py-2">ATM cash issues</div>
                <div className="rounded-full border border-white/20 bg-white/10 px-4 py-2">Unauthorized activity</div>
              </div>
            </div>

            <Card className="border-slate-200 shadow-sm">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-slate-900">
                  <Building2 className="h-5 w-5 text-blue-800" />
                  Raise a Dispute Ticket
                </CardTitle>
                <CardDescription>Complete the form below to create a new customer-facing dispute request.</CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleSubmit} className="space-y-6">
                  {error && (
                    <div className="flex items-start gap-3 rounded-lg border border-red-200 bg-red-50 p-4 text-red-700">
                      <AlertCircle className="mt-0.5 h-5 w-5 shrink-0" />
                      <p className="text-sm">{error}</p>
                    </div>
                  )}

                  <div className="grid gap-6 md:grid-cols-2">
                    <div className="space-y-2">
                      <label htmlFor="customer" className="text-sm font-medium text-slate-700">Select Customer</label>
                      <select
                        id="customer"
                        value={selectedCustomerId}
                        onChange={(e) => setSelectedCustomerId(e.target.value)}
                        className="w-full rounded-lg border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 shadow-sm outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
                        disabled={customersLoading}
                      >
                        <option value="">{customersLoading ? "Loading customers..." : "Choose a customer"}</option>
                        {customers.map((c) => (
                          <option key={c.id} value={c.id}>{c.name} · {c.account_tier}</option>
                        ))}
                      </select>
                    </div>

                    <div className="space-y-2">
                      <label htmlFor="transaction" className="text-sm font-medium text-slate-700">Select Transaction</label>
                      <select
                        id="transaction"
                        value={selectedTransactionId}
                        onChange={(e) => setSelectedTransactionId(e.target.value)}
                        className="w-full rounded-lg border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 shadow-sm outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
                        disabled={!selectedCustomerId || transactionsLoading}
                      >
                        <option value="">
                          {!selectedCustomerId ? "Select a customer first" : transactionsLoading ? "Loading transactions..." : transactions.length > 0 ? "Choose a transaction" : "No recent transactions found"}
                        </option>
                        {transactions.map((t) => (
                          <option key={t.id} value={t.id}>#{t.id} · {t.merchant_name} · ${t.amount.toFixed(2)}</option>
                        ))}
                      </select>
                    </div>
                  </div>

                  {transactions.length > 0 && (
                    <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                      <div className="mb-3 flex items-center justify-between">
                        <h3 className="text-sm font-semibold text-slate-800">Recent transactions</h3>
                        <p className="text-xs text-slate-500">Showing latest {transactions.length} records</p>
                      </div>
                      <div className="space-y-3">
                        {transactions.map((t) => {
                          const isSelected = t.id === Number(selectedTransactionId);
                          return (
                            <button
                              key={t.id}
                              type="button"
                              onClick={() => setSelectedTransactionId(String(t.id))}
                              className={`flex w-full items-center justify-between rounded-lg border px-4 py-3 text-left transition ${isSelected ? "border-blue-600 bg-blue-50 shadow-sm" : "border-slate-200 bg-white hover:border-slate-300"}`}
                            >
                              <div className="flex-1">
                                <div className="flex items-center gap-2 mb-1">
                                  <p className="text-sm font-semibold text-slate-900">{t.merchant_name}</p>
                                  <Badge
                                    variant="outline"
                                    className={
                                      t.transaction_type === 'credit'
                                        ? 'bg-green-50 text-green-700 border-green-200 text-xs'
                                        : 'bg-slate-50 text-slate-700 border-slate-200 text-xs'
                                    }
                                  >
                                    {(t.transaction_type || 'debit').toUpperCase()}
                                  </Badge>
                                </div>
                                <p className="text-xs text-slate-500">
                                  {new Date(t.transaction_date).toLocaleString()} · {t.status}{t.is_international ? " · International" : ""}
                                </p>
                              </div>
                              <p className="text-sm font-bold text-slate-900">${t.amount.toFixed(2)}</p>
                            </button>
                          );
                        })}
                      </div>
                    </div>
                  )}

                  <div className="space-y-2">
                    <Label htmlFor="disputeType" className="text-sm font-medium text-slate-700">Dispute Type *</Label>
                    <select
                      id="disputeType"
                      value={disputeType}
                      onChange={(e) => {
                        setDisputeType(e.target.value);
                        // Reset type-specific fields when changing dispute type
                        setLoanAccountNumber("");
                        setEmiAmount("");
                        setAtmLocation("");
                        setAtmWithdrawalAmount("");
                        setMerchantReceipt(null);
                        setExpectedAmount("");
                        setChargedAmount("");
                      }}
                      className="w-full rounded-lg border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 shadow-sm outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
                      disabled={!selectedTransactionId}
                    >
                      <option value="">Select dispute type...</option>
                      <option value="fraud">🚨 Fraudulent Transaction</option>
                      <option value="atm_failure">🏧 ATM Failure (Cash Not Dispensed)</option>
                      <option value="emi_issue">💳 EMI/Loan Issue</option>
                      <option value="incorrect_amount">💰 Incorrect Amount Charged</option>
                      <option value="merchant_dispute">🏪 Merchant Dispute</option>
                      <option value="duplicate">📋 Duplicate Charge</option>
                      <option value="failed_transaction">❌ Failed Transaction</option>
                      <option value="refund_not_received">↩️ Refund Not Received</option>
                    </select>
                  </div>

                  {/* Dynamic fields based on dispute type */}
                  {disputeType === "emi_issue" && (
                    <div className="space-y-4 rounded-lg border border-blue-200 bg-blue-50 p-4">
                      <h4 className="text-sm font-semibold text-slate-900">EMI/Loan Details</h4>
                      <div className="space-y-2">
                        <Label htmlFor="loanAccountNumber">Loan Account Number</Label>
                        <Input
                          id="loanAccountNumber"
                          type="text"
                          value={loanAccountNumber}
                          onChange={(e) => setLoanAccountNumber(e.target.value)}
                          placeholder="e.g., LOAN123456789"
                          className="bg-white"
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="emiAmount">EMI Amount</Label>
                        <Input
                          id="emiAmount"
                          type="number"
                          step="0.01"
                          value={emiAmount}
                          onChange={(e) => setEmiAmount(e.target.value)}
                          placeholder="e.g., 500.00"
                          className="bg-white"
                        />
                      </div>
                    </div>
                  )}

                  {disputeType === "atm_failure" && (
                    <div className="space-y-4 rounded-lg border border-blue-200 bg-blue-50 p-4">
                      <h4 className="text-sm font-semibold text-slate-900">ATM Transaction Details</h4>
                      <div className="space-y-2">
                        <Label htmlFor="atmLocation">ATM Location</Label>
                        <Input
                          id="atmLocation"
                          type="text"
                          value={atmLocation}
                          onChange={(e) => setAtmLocation(e.target.value)}
                          placeholder="e.g., Main Street Branch, Downtown"
                          className="bg-white"
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="atmWithdrawalAmount">Withdrawal Amount</Label>
                        <Input
                          id="atmWithdrawalAmount"
                          type="number"
                          step="0.01"
                          value={atmWithdrawalAmount}
                          onChange={(e) => setAtmWithdrawalAmount(e.target.value)}
                          placeholder="e.g., 200.00"
                          className="bg-white"
                        />
                      </div>
                    </div>
                  )}

                  {(disputeType === "merchant_dispute" || disputeType === "incorrect_amount") && (
                    <div className="space-y-4 rounded-lg border border-blue-200 bg-blue-50 p-4">
                      <h4 className="text-sm font-semibold text-slate-900">
                        {disputeType === "incorrect_amount" ? "Amount Details" : "Merchant Details"}
                      </h4>
                      
                      {disputeType === "incorrect_amount" && (
                        <>
                          <div className="space-y-2">
                            <Label htmlFor="expectedAmount">Expected Amount</Label>
                            <Input
                              id="expectedAmount"
                              type="number"
                              step="0.01"
                              value={expectedAmount}
                              onChange={(e) => setExpectedAmount(e.target.value)}
                              placeholder="e.g., 50.00"
                              className="bg-white"
                            />
                          </div>
                          <div className="space-y-2">
                            <Label htmlFor="chargedAmount">Charged Amount</Label>
                            <Input
                              id="chargedAmount"
                              type="number"
                              step="0.01"
                              value={chargedAmount}
                              onChange={(e) => setChargedAmount(e.target.value)}
                              placeholder="e.g., 75.00"
                              className="bg-white"
                            />
                          </div>
                        </>
                      )}
                      
                      <div className="space-y-2">
                        <Label htmlFor="merchantReceipt">Merchant Receipt (Optional)</Label>
                        <div className="flex items-center gap-2">
                          <label
                            htmlFor="merchantReceipt"
                            className="flex cursor-pointer items-center gap-2 rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm text-slate-700 transition hover:bg-slate-50"
                          >
                            <Upload className="h-4 w-4" />
                            {merchantReceipt ? "Change File" : "Upload Receipt"}
                          </label>
                          <input
                            id="merchantReceipt"
                            type="file"
                            accept="image/*,.pdf"
                            onChange={(e) => setMerchantReceipt(e.target.files?.[0] || null)}
                            className="hidden"
                          />
                          {merchantReceipt && (
                            <div className="flex items-center gap-2 rounded-lg bg-white px-3 py-2 text-sm">
                              <span className="text-slate-700">{merchantReceipt.name}</span>
                              <button
                                type="button"
                                onClick={() => setMerchantReceipt(null)}
                                className="text-red-600 hover:text-red-700"
                              >
                                <X className="h-4 w-4" />
                              </button>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  )}

                  {disputeType && (
                    <>
                      <div className="space-y-2">
                        <Label htmlFor="reason" className="text-sm font-medium text-slate-700">
                          Brief Description *
                        </Label>
                        <textarea
                          id="reason"
                          value={disputeReason}
                          onChange={(e) => setDisputeReason(e.target.value)}
                          placeholder="Provide a brief summary of the issue..."
                          className="min-h-[100px] w-full rounded-lg border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 shadow-sm outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
                          required
                        />
                        {descriptionSuggestions.length > 0 && !disputeReason.trim() && (
                          <div className="rounded-lg border border-blue-200 bg-blue-50 p-3">
                            <p className="mb-2 text-xs font-semibold text-slate-700">💡 Quick suggestions (click to use):</p>
                            <div className="flex flex-wrap gap-2">
                              {descriptionSuggestions.map((suggestion, index) => (
                                <button
                                  key={index}
                                  type="button"
                                  onClick={() => setDisputeReason(suggestion)}
                                  className="rounded-md border border-blue-300 bg-white px-3 py-1.5 text-xs text-slate-700 transition hover:bg-blue-100 hover:border-blue-400"
                                >
                                  {suggestion}
                                </button>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>

                      <div className="space-y-2">
                        <Label htmlFor="additionalDetails" className="text-sm font-medium text-slate-700">
                          Additional Details (Optional)
                        </Label>
                        <textarea
                          id="additionalDetails"
                          value={additionalDetails}
                          onChange={(e) => setAdditionalDetails(e.target.value)}
                          placeholder="Any other relevant information..."
                          className="min-h-[80px] w-full rounded-lg border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 shadow-sm outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
                        />
                      </div>
                    </>
                  )}

                  <Button type="submit" disabled={submitLoading || !selectedCustomerId || !selectedTransactionId || !disputeType || !disputeReason.trim()} className="w-full bg-blue-900 hover:bg-blue-800">
                    {submitLoading ? (
                      <>
                        <div className="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                        AI is reviewing your case...
                      </>
                    ) : (
                      <>
                        <Send className="mr-2 h-4 w-4" />
                        Submit Dispute
                      </>
                    )}
                  </Button>
                </form>
              </CardContent>
            </Card>
          </div>

          <div className="space-y-6">
            <LiveAiFeed
              activeTicketId={activeStreamTicketId}
              onProcessingCompleted={() => {
                console.log("[CustomerPortal] Refreshing customer and transaction data after dispute completion");
                fetchCustomers();
                if (selectedCustomerId) {
                  fetchTransactions(selectedCustomerId);
                  fetchPastDisputes(selectedCustomerId);
                }
              }}
            />

            {selectedCustomer && (
              <Card className="border-slate-200 shadow-sm">
                <CardHeader>
                  <CardTitle className="text-slate-900">Customer Profile</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <p className="text-xs font-medium text-slate-500">Name</p>
                    <p className="text-sm font-semibold text-slate-900">{selectedCustomer.name}</p>
                  </div>
                  <div>
                    <p className="text-xs font-medium text-slate-500">Account Tier</p>
                    <Badge variant="outline" className="mt-1">{selectedCustomer.account_tier}</Badge>
                  </div>
                  <div>
                    <p className="text-xs font-medium text-slate-500">Current Account Balance</p>
                    <p className="text-sm font-semibold text-green-600">${selectedCustomer.current_account_balance.toLocaleString()}</p>
                  </div>
                </CardContent>
              </Card>
            )}

            {selectedTransaction && (
              <Card className="border-slate-200 shadow-sm">
                <CardHeader>
                  <CardTitle className="text-slate-900">Transaction Details</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <p className="text-xs font-medium text-slate-500">Amount</p>
                    <p className="text-2xl font-bold text-red-600">${selectedTransaction.amount.toFixed(2)}</p>
                  </div>
                  <div>
                    <p className="text-xs font-medium text-slate-500">Merchant</p>
                    <p className="text-sm font-semibold text-slate-900">{selectedTransaction.merchant_name}</p>
                  </div>
                  <div>
                    <p className="text-xs font-medium text-slate-500">Date</p>
                    <p className="text-sm text-slate-900">{new Date(selectedTransaction.transaction_date).toLocaleString()}</p>
                  </div>
                  <div>
                    <p className="text-xs font-medium text-slate-500">Status</p>
                    <Badge variant="outline" className="mt-1">{selectedTransaction.status}</Badge>
                  </div>
                  {selectedTransaction.is_international && (
                    <Badge variant="secondary" className="bg-blue-100 text-blue-700">🌍 International Transaction</Badge>
                  )}
                </CardContent>
              </Card>
            )}

            {selectedCustomerId && (
              <Card id="dispute-history-card" className="border-slate-200 shadow-sm">
                <CardHeader>
                  <CardTitle className="text-slate-900">Dispute History</CardTitle>
                  <CardDescription>View your past disputes and AI activity</CardDescription>
                </CardHeader>
                <CardContent>
                  {pastDisputesLoading ? (
                    <div className="flex items-center justify-center py-8">
                      <div className="h-6 w-6 animate-spin rounded-full border-2 border-blue-900 border-t-transparent" />
                    </div>
                  ) : pastDisputes.length === 0 ? (
                    <p className="text-sm text-slate-500 py-4">No past disputes found.</p>
                  ) : (
                    <div className="space-y-3">
                      {pastDisputes.map((dispute) => (
                        <div key={dispute.ticket_id} className="border border-slate-200 rounded-lg overflow-hidden">
                          <button
                            onClick={() => setExpandedDisputeId(expandedDisputeId === dispute.ticket_id ? null : dispute.ticket_id)}
                            className="w-full px-4 py-3 bg-slate-50 hover:bg-slate-100 transition flex items-center justify-between"
                          >
                            <div className="flex items-center gap-3 text-left">
                              <div>
                                <p className="text-sm font-semibold text-slate-900">Ticket #{dispute.ticket_id}</p>
                                <p className="text-xs text-slate-500">
                                  {dispute.created_at ? new Date(dispute.created_at).toLocaleDateString() : 'N/A'}
                                </p>
                              </div>
                              <Badge variant="outline" className="text-xs">
                                {formatDisputeCategory(dispute.dispute_category)}
                              </Badge>
                              <Badge
                                className={
                                  dispute.final_decision === "auto_approved" || dispute.final_decision === "resolved_approved"
                                    ? "bg-green-100 text-green-800 hover:bg-green-100"
                                    : dispute.final_decision === "auto_rejected" || dispute.final_decision === "resolved_rejected"
                                    ? "bg-red-100 text-red-800 hover:bg-red-100"
                                    : "bg-yellow-100 text-yellow-800 hover:bg-yellow-100"
                                }
                              >
                                {dispute.final_decision === "auto_approved" || dispute.final_decision === "resolved_approved"
                                  ? "Approved"
                                  : dispute.final_decision === "auto_rejected" || dispute.final_decision === "resolved_rejected"
                                  ? "Rejected"
                                  : "Under Review"}
                              </Badge>
                            </div>
                            {expandedDisputeId === dispute.ticket_id ? (
                              <ChevronUp className="h-4 w-4 text-slate-500" />
                            ) : (
                              <ChevronDown className="h-4 w-4 text-slate-500" />
                            )}
                          </button>
                          
                          {expandedDisputeId === dispute.ticket_id && (
                            <div className="p-4 bg-slate-50 border-t border-slate-200">
                              <div className="mb-4">
                                <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">AI Reasoning</p>
                                <p className="text-sm text-slate-700 bg-white p-3 rounded border border-slate-200">
                                  {typeof dispute.decision_reasoning === 'object' ? dispute.decision_reasoning?.justification : dispute.decision_reasoning || "No reasoning provided."}
                                </p>
                              </div>
                              
                              <div>
                                <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Audit Trail</p>
                                <div className="bg-white p-3 rounded border border-slate-200 max-h-60 overflow-y-auto space-y-2">
                                  {dispute.audit_trail && dispute.audit_trail.map((log: any, idx: number) => {
                                    const isObj = typeof log === 'object' && log !== null;
                                    const key = isObj && log.id ? log.id : idx;
                                    const text = isObj ? log.description : log;
                                    const agent = isObj && log.agent_name ? `[${log.agent_name}] ` : '';
                                    return (
                                      <div key={key} className="text-xs text-slate-600 border-b border-slate-100 pb-2 last:border-0 last:pb-0">
                                        <span className="font-medium text-slate-800">{agent}</span>{text}
                                      </div>
                                    );
                                  })}
                                </div>
                              </div>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </div>
      </div>
    </>
  );
}

// Made with Bob
