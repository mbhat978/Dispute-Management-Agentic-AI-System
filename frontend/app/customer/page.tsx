"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { AlertCircle, Brain, Building2, CheckCircle2, Landmark, Radio, Send, WifiOff } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

interface Customer {
  id: number;
  name: string;
  account_tier: string;
  average_monthly_balance: number;
}

interface Transaction {
  id: number;
  customer_id: number;
  amount: number;
  merchant_name: string;
  transaction_date: string;
  status: string;
  is_international: boolean;
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
}

function formatStatus(status: string): string {
  return status
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
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

function LiveAiFeed({ activeTicketId }: { activeTicketId: number | null }) {
  const [events, setEvents] = useState<LiveFeedEvent[]>([]);
  const [connectionStatus, setConnectionStatus] = useState<"idle" | "connecting" | "connected" | "disconnected">("idle");

  useEffect(() => {
    if (!activeTicketId) {
      setConnectionStatus("idle");
      setEvents([]);
      return;
    }

    setConnectionStatus("connecting");
    setEvents([]);

    const eventSource = new EventSource(`${API_BASE_URL}/api/disputes/stream`);

    const appendEvent = (eventType: string, rawData: string) => {
      try {
        const parsed = JSON.parse(rawData) as {
          timestamp?: string;
          message?: string;
          ticket_id?: number | null;
          node?: string | null;
          final_decision?: string | null;
          dispute_category?: string | null;
          state?: LiveFeedState;
        };

        if (parsed.ticket_id != null && parsed.ticket_id !== activeTicketId) {
          return;
        }

        setEvents((current) => {
          const nextEvent: LiveFeedEvent = {
            id: `${eventType}-${parsed.timestamp ?? Date.now()}-${current.length}`,
            timestamp: parsed.timestamp ?? new Date().toISOString(),
            eventType,
            message: parsed.message ?? "AI workflow update received",
            ticket_id: parsed.ticket_id,
            node: parsed.node,
            final_decision: parsed.final_decision ?? parsed.state?.final_decision ?? null,
            dispute_category: parsed.dispute_category ?? parsed.state?.dispute_category ?? null,
            state: parsed.state,
          };

          return [nextEvent, ...current].slice(0, 30);
        });
      } catch (streamError) {
        console.error("Failed to parse live feed event:", streamError, rawData);
      }
    };

    const registerEventType = (eventType: string) => {
      eventSource.addEventListener(eventType, (event) => {
        setConnectionStatus("connected");
        appendEvent(eventType, (event as MessageEvent).data);
      });
    };

    registerEventType("connection");
    registerEventType("processing_started");
    registerEventType("agent_update");
    registerEventType("processing_completed");
    registerEventType("processing_failed");
    registerEventType("heartbeat");

    eventSource.onopen = () => {
      setConnectionStatus("connected");
    };

    eventSource.onerror = () => {
      setConnectionStatus("disconnected");
    };

    return () => {
      eventSource.close();
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
          <div className="space-y-3 max-h-[420px] overflow-y-auto pr-2">
            {events.map((event) => (
              <div key={event.id} className="rounded-lg border border-slate-200 bg-slate-50 p-4">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <Badge className={getEventBadgeClass(event.eventType)}>
                      {formatEventLabel(event.eventType)}
                    </Badge>
                    {event.node && (
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

                <p className="mt-3 text-sm leading-relaxed text-slate-700">{event.message}</p>

                {(event.dispute_category || event.final_decision || event.state) && (
                  <div className="mt-3 grid gap-2 md:grid-cols-2">
                    {(event.dispute_category || event.state?.dispute_category) && (
                      <div className="rounded-md bg-white p-3 text-xs text-slate-700">
                        <span className="font-semibold">Category:</span>{" "}
                        {event.dispute_category ?? event.state?.dispute_category}
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
            ))}
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

  useEffect(() => {
    async function fetchCustomers() {
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
    }
    fetchCustomers();
  }, []);

  useEffect(() => {
    async function fetchTransactions() {
      if (!selectedCustomerId) {
        setTransactions([]);
        setSelectedTransactionId("");
        return;
      }
      try {
        setTransactionsLoading(true);
        setError(null);
        setSelectedTransactionId("");
        const response = await fetch(`${API_BASE_URL}/api/customers/${selectedCustomerId}/transactions`);
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
    }
    fetchTransactions();
  }, [selectedCustomerId]);

  const selectedCustomer = useMemo(
    () => customers.find((c) => c.id === Number(selectedCustomerId)) ?? null,
    [customers, selectedCustomerId]
  );

  const selectedTransaction = useMemo(
    () => transactions.find((t) => t.id === Number(selectedTransactionId)) ?? null,
    [transactions, selectedTransactionId]
  );

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedCustomerId || !selectedTransactionId || !disputeReason.trim()) {
      setError("Please select a customer, choose a transaction, and describe the issue.");
      return;
    }
    try {
      setSubmitLoading(true);
      setError(null);
      setDecisionResult(null);
      setShowDecisionModal(false);
      setActiveStreamTicketId(null);

      const response = await fetch(`${API_BASE_URL}/api/disputes/process`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          transaction_id: Number(selectedTransactionId),
          customer_id: Number(selectedCustomerId),
          customer_query: disputeReason.trim(),
        }),
      });

      if (!response.ok) {
        const errorData: ApiErrorResponse = await response.json().catch(() => ({}));
        throw new Error(getErrorMessage(errorData, `Failed to process dispute: ${response.statusText}`));
      }

      const data: ProcessDisputeResponse = await response.json();
      setDecisionResult(data);
      setActiveStreamTicketId(data.ticket_id);
      setShowDecisionModal(true);
      setSelectedCustomerId("");
      setSelectedTransactionId("");
      setTransactions([]);
      setDisputeReason("");
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
                  <span className="font-medium text-slate-900">AI category:</span> {decisionResult.dispute_category}
                </p>
              </div>

              <Button
                type="button"
                className="w-full bg-blue-900 hover:bg-blue-800"
                onClick={() => setShowDecisionModal(false)}
              >
                Close
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
                              <div>
                                <p className="text-sm font-semibold text-slate-900">{t.merchant_name}</p>
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
                    <label htmlFor="reason" className="text-sm font-medium text-slate-700">Dispute Reason</label>
                    <textarea
                      id="reason"
                      value={disputeReason}
                      onChange={(e) => setDisputeReason(e.target.value)}
                      placeholder="Describe exactly what went wrong in natural language, for example: 'I didn't make this purchase' or 'The ATM didn't give me cash'."
                      className="min-h-[160px] w-full rounded-lg border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 shadow-sm outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
                    />
                  </div>

                  <Button type="submit" disabled={submitLoading || !selectedCustomerId || !selectedTransactionId || !disputeReason.trim()} className="w-full bg-blue-900 hover:bg-blue-800">
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
            <LiveAiFeed activeTicketId={activeStreamTicketId} />
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
                    <p className="text-xs font-medium text-slate-500">Average Monthly Balance</p>
                    <p className="text-sm font-semibold text-green-600">${selectedCustomer.average_monthly_balance.toLocaleString()}</p>
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
          </div>
        </div>
      </div>
      </div>
    </>
  );
}

// Made with Bob
