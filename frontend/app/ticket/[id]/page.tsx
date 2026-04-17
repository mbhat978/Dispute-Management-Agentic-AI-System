"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { ArrowLeft, CheckCircle2, XCircle, Clock, User, CreditCard, AlertCircle, Brain, Eye, Wrench, Scale } from "lucide-react";

interface Customer {
  id: number;
  name: string;
  account_tier: string;
  average_monthly_balance: number;
}

interface Transaction {
  id: number;
  amount: number;
  merchant_name: string;
  transaction_date: string;
  status: string;
  is_international: boolean;
}

interface AuditLog {
  id: number;
  agent_name: string;
  action_type: string;
  description: string;
  timestamp: string;
}

interface Dispute {
  id: number;
  dispute_reason: string;
  status: string;
  resolution_notes: string | null;
  created_at: string;
  updated_at: string;
}

interface TicketData {
  dispute: Dispute;
  customer: Customer;
  transaction: Transaction;
  audit_logs: AuditLog[];
}

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

function getStatusBadge(status: string) {
  switch (status) {
    case "auto_approved":
      return {
        variant: "default" as const,
        className: "bg-green-500 hover:bg-green-600",
        icon: <CheckCircle2 className="h-4 w-4 mr-1" />
      };
    case "auto_rejected":
      return {
        variant: "destructive" as const,
        className: "",
        icon: <XCircle className="h-4 w-4 mr-1" />
      };
    case "human_review_required":
      return {
        variant: "secondary" as const,
        className: "bg-yellow-500 hover:bg-yellow-600 text-black",
        icon: <AlertCircle className="h-4 w-4 mr-1" />
      };
    case "pending_review":
      return {
        variant: "secondary" as const,
        className: "bg-orange-500 hover:bg-orange-600 text-white",
        icon: <AlertCircle className="h-4 w-4 mr-1" />
      };
    default:
      return {
        variant: "outline" as const,
        className: "",
        icon: <Clock className="h-4 w-4 mr-1" />
      };
  }
}

function formatStatus(status: string): string {
  return status.split("_").map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(" ");
}

function getActionTypeStyle(actionType: string) {
  switch (actionType) {
    case "thought":
      return { 
        bgColor: "bg-blue-50 dark:bg-blue-950/50", 
        textColor: "text-blue-900 dark:text-blue-100", 
        borderColor: "border-blue-300 dark:border-blue-700", 
        icon: <Brain className="h-5 w-5" />, 
        label: "Thought",
        description: "AI Reasoning"
      };
    case "tool_call":
      return { 
        bgColor: "bg-purple-50 dark:bg-purple-950/50", 
        textColor: "text-purple-900 dark:text-purple-100", 
        borderColor: "border-purple-300 dark:border-purple-700", 
        icon: <Wrench className="h-5 w-5" />, 
        label: "Tool Call",
        description: "Action Taken"
      };
    case "observation":
      return { 
        bgColor: "bg-green-50 dark:bg-green-950/50", 
        textColor: "text-green-900 dark:text-green-100", 
        borderColor: "border-green-300 dark:border-green-700", 
        icon: <Eye className="h-5 w-5" />, 
        label: "Observation",
        description: "Data Retrieved"
      };
    case "decision":
      return { 
        bgColor: "bg-orange-50 dark:bg-orange-950/50", 
        textColor: "text-orange-900 dark:text-orange-100", 
        borderColor: "border-orange-300 dark:border-orange-700", 
        icon: <Scale className="h-5 w-5" />, 
        label: "Decision",
        description: "Final Verdict"
      };
    default:
      return { 
        bgColor: "bg-gray-50 dark:bg-gray-950/50", 
        textColor: "text-gray-900 dark:text-gray-100", 
        borderColor: "border-gray-300 dark:border-gray-700", 
        icon: <Clock className="h-5 w-5" />, 
        label: actionType,
        description: "Event"
      };
  }
}

export default function TicketDetailPage() {
  const params = useParams();
  const router = useRouter();
  const ticketId = params.id as string;
  const [ticketData, setTicketData] = useState<TicketData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);
  const [processing, setProcessing] = useState(false);
  const [humanNotes, setHumanNotes] = useState("");
  const [showNotesDialog, setShowNotesDialog] = useState(false);
  const [pendingAction, setPendingAction] = useState<"approve" | "reject" | null>(null);
  const [overrideProcessing, setOverrideProcessing] = useState(false);

  useEffect(() => {
    async function fetchTicketDetails() {
      try {
        const response = await fetch(`http://localhost:8000/api/disputes/${ticketId}`);
        if (!response.ok) {
          const errorData: ApiErrorResponse = await response.json().catch(() => ({}));
          throw new Error(getErrorMessage(errorData, `Failed to fetch ticket details: ${response.statusText}`));
        }
        const data = await response.json();
        setTicketData(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "An error occurred");
        console.error("Error fetching ticket details:", err);
      } finally {
        setLoading(false);
      }
    }
    fetchTicketDetails();
  }, [ticketId]);

  const handleApprove = () => {
    setPendingAction("approve");
    setShowNotesDialog(true);
  };

  const handleReject = () => {
    setPendingAction("reject");
    setShowNotesDialog(true);
  };

  const handleCancelResolution = () => {
    setShowNotesDialog(false);
    setPendingAction(null);
    setHumanNotes("");
    setActionError(null);
  };

  const handleConfirmResolution = async () => {
    if (!humanNotes.trim()) {
      setActionError("Please provide notes for your decision.");
      return;
    }

    const action = pendingAction;
    if (!action) return;

    const resolutionStatus = action === "approve" ? "resolved_approved" : "resolved_rejected";
    
    setProcessing(true);
    setActionError(null);
    setActionSuccess(null);
    try {
      const response = await fetch(`http://localhost:8000/api/disputes/${ticketId}/resolve`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          resolution_status: resolutionStatus,
          human_notes: humanNotes.trim()
        }),
      });
      
      if (!response.ok) {
        const errorData: ApiErrorResponse = await response.json().catch(() => ({}));
        throw new Error(getErrorMessage(errorData, `Failed to ${action} ticket: ${response.statusText}`));
      }
      
      const result = await response.json();
      setActionSuccess(result.message ?? `Ticket ${action}ed successfully.`);
      
      // Reset state and refresh
      setShowNotesDialog(false);
      setPendingAction(null);
      setHumanNotes("");
      
      // Refresh the page to show updated status
      window.location.reload();
    } catch (err) {
      console.error(`Error ${action}ing ticket:`, err);
      setActionError(err instanceof Error ? err.message : `Failed to ${action} ticket`);
    } finally {
      setProcessing(false);
    }
  };

  const handleHumanOverride = async (decision: string) => {
    setOverrideProcessing(true);
    setActionError(null);
    setActionSuccess(null);
    
    try {
      const response = await fetch(`http://localhost:8000/api/disputes/${ticketId}/resume`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          override_decision: decision
        }),
      });
      
      if (!response.ok) {
        const errorData: ApiErrorResponse = await response.json().catch(() => ({}));
        throw new Error(getErrorMessage(errorData, `Failed to ${decision} dispute: ${response.statusText}`));
      }
      
      const result = await response.json();
      setActionSuccess(result.message ?? `Dispute ${decision}d successfully. Processing will resume.`);
      
      // Refresh the page after a short delay to show the updated status
      setTimeout(() => {
        window.location.reload();
      }, 1500);
    } catch (err) {
      console.error(`Error ${decision}ing dispute:`, err);
      setActionError(err instanceof Error ? err.message : `Failed to ${decision} dispute`);
    } finally {
      setOverrideProcessing(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <div className="text-center space-y-4">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
          <p className="text-muted-foreground">Loading ticket details...</p>
        </div>
      </div>
    );
  }

  if (error || !ticketData) {
    return (
      <div className="flex flex-col justify-center items-center min-h-screen space-y-4">
        <AlertCircle className="h-16 w-16 text-red-500" />
        <p className="text-red-500 text-lg font-semibold">Error: {error || "Ticket not found"}</p>
        <Link href="/employee">
          <Button variant="outline">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Dashboard
          </Button>
        </Link>
      </div>
    );
  }

  const { dispute, customer, transaction, audit_logs } = ticketData;
  const statusBadge = getStatusBadge(dispute.status);

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Link href="/employee">
            <Button variant="ghost" size="sm">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Dashboard
            </Button>
          </Link>
          <Separator orientation="vertical" className="h-8" />
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Dispute Ticket #{dispute.id}</h1>
            <p className="text-muted-foreground mt-1">
              Created on {new Date(dispute.created_at).toLocaleString()}
            </p>
          </div>
        </div>
        <Badge variant={statusBadge.variant} className={`${statusBadge.className} text-lg px-4 py-2`}>
          {statusBadge.icon}
          {formatStatus(dispute.status)}
        </Badge>
      </div>

      {/* Split Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Column - Context */}
        <div className="space-y-6">
          {/* Customer Details */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <User className="h-5 w-5 mr-2" />
                Customer Details
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Name</p>
                <p className="text-lg font-semibold">{customer.name}</p>
              </div>
              <div>
                <p className="text-sm font-medium text-muted-foreground">Customer ID</p>
                <p className="text-lg font-mono">{customer.id}</p>
              </div>
              <div>
                <p className="text-sm font-medium text-muted-foreground">Account Tier</p>
                <Badge variant="outline" className="mt-1">{customer.account_tier}</Badge>
              </div>
              <div>
                <p className="text-sm font-medium text-muted-foreground">Average Monthly Balance</p>
                <p className="text-lg font-semibold text-green-600">
                  ${customer.average_monthly_balance.toLocaleString()}
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Transaction Details */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <CreditCard className="h-5 w-5 mr-2" />
                Transaction Details
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Amount</p>
                <p className="text-3xl font-bold text-red-600">${transaction.amount.toFixed(2)}</p>
              </div>
              <div>
                <p className="text-sm font-medium text-muted-foreground">Merchant</p>
                <p className="text-lg font-semibold">{transaction.merchant_name}</p>
              </div>
              <div>
                <p className="text-sm font-medium text-muted-foreground">Transaction Date</p>
                <p className="text-lg">{new Date(transaction.transaction_date).toLocaleString()}</p>
              </div>
              <div>
                <p className="text-sm font-medium text-muted-foreground">Transaction ID</p>
                <p className="text-lg font-mono">{transaction.id}</p>
              </div>
              <div>
                <p className="text-sm font-medium text-muted-foreground">Status</p>
                <Badge variant="outline" className="mt-1">{transaction.status}</Badge>
              </div>
              {transaction.is_international && (
                <div>
                  <Badge variant="secondary" className="bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300">
                    🌍 International Transaction
                  </Badge>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Dispute Reason */}
          <Card>
            <CardHeader>
              <CardTitle>Dispute Reason</CardTitle>
              <CardDescription>Customer's reported issue</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm leading-relaxed bg-muted p-4 rounded-md">
                {dispute.dispute_reason}
              </p>
            </CardContent>
          </Card>

          {/* Final AI Decision */}
          <Card className="border-2 border-primary/20">
            <CardHeader>
              <CardTitle className="flex items-center">
                <Scale className="h-5 w-5 mr-2" />
                Final AI Decision
              </CardTitle>
              <CardDescription>AI system's recommendation based on analysis</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <p className="text-sm font-medium text-muted-foreground mb-2">Decision</p>
                <Badge variant={statusBadge.variant} className={`${statusBadge.className} text-base px-3 py-1`}>
                  {statusBadge.icon}
                  {formatStatus(dispute.status)}
                </Badge>
              </div>
              {dispute.resolution_notes && (
                <div>
                  <p className="text-sm font-medium text-muted-foreground mb-2">Resolution Notes</p>
                  <p className="text-sm leading-relaxed p-3 bg-muted rounded-md">
                    {dispute.resolution_notes}
                  </p>
                </div>
              )}
              <div>
                <p className="text-sm font-medium text-muted-foreground mb-2">Last Updated</p>
                <p className="text-sm">{new Date(dispute.updated_at).toLocaleString()}</p>
              </div>
            </CardContent>
          </Card>

          {/* Human Review Actions */}
          {dispute.status === "human_review_required" && (
            <Card className="border-yellow-500 border-2 bg-yellow-50 dark:bg-yellow-950/20">
              <CardHeader>
                <CardTitle className="text-yellow-700 dark:text-yellow-300 flex items-center">
                  <AlertCircle className="h-5 w-5 mr-2" />
                  Human Review Required
                </CardTitle>
                <CardDescription className="text-yellow-600 dark:text-yellow-400">
                  This case requires human intervention. Please review the complete audit trail on the right and make a final decision.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {actionError && (
                  <div className="flex items-start gap-3 rounded-lg border border-red-200 bg-red-50 p-4 text-red-700">
                    <AlertCircle className="mt-0.5 h-5 w-5 shrink-0" />
                    <p className="text-sm">{actionError}</p>
                  </div>
                )}
                {actionSuccess && (
                  <div className="flex items-start gap-3 rounded-lg border border-green-200 bg-green-50 p-4 text-green-700">
                    <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0" />
                    <p className="text-sm">{actionSuccess}</p>
                  </div>
                )}
                {!showNotesDialog ? (
                  <div className="flex gap-3">
                    <Button
                      onClick={handleApprove}
                      disabled={processing}
                      className="flex-1 bg-green-600 hover:bg-green-700"
                    >
                      <CheckCircle2 className="h-4 w-4 mr-2" />
                      Approve Dispute
                    </Button>
                    <Button
                      onClick={handleReject}
                      disabled={processing}
                      variant="destructive"
                      className="flex-1"
                    >
                      <XCircle className="h-4 w-4 mr-2" />
                      Reject Dispute
                    </Button>
                  </div>
                ) : (
                  <div className="space-y-4">
                    <div>
                      <label className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 block">
                        {pendingAction === "approve" ? "Approval" : "Rejection"} Notes
                        <span className="text-red-500 ml-1">*</span>
                      </label>
                      <textarea
                        value={humanNotes}
                        onChange={(e) => setHumanNotes(e.target.value)}
                        placeholder={`Provide detailed notes explaining your decision to ${pendingAction} this dispute. Include any additional context or reasoning that supports your decision.`}
                        className="w-full min-h-[120px] p-3 border rounded-md focus:ring-2 focus:ring-primary focus:border-transparent resize-y bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100"
                        disabled={processing}
                      />
                      <p className="text-xs text-muted-foreground mt-1">
                        These notes will be added to the audit trail for compliance and governance.
                      </p>
                    </div>
                    <div className="flex gap-3">
                      <Button
                        onClick={handleConfirmResolution}
                        disabled={processing || !humanNotes.trim()}
                        className={`flex-1 ${pendingAction === "approve" ? "bg-green-600 hover:bg-green-700" : ""}`}
                        variant={pendingAction === "reject" ? "destructive" : "default"}
                      >
                        {processing ? (
                          <>
                            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                            Processing...
                          </>
                        ) : (
                          <>
                            {pendingAction === "approve" ? (
                              <CheckCircle2 className="h-4 w-4 mr-2" />
                            ) : (
                              <XCircle className="h-4 w-4 mr-2" />
                            )}
                            Confirm {pendingAction === "approve" ? "Approval" : "Rejection"}
                          </>
                        )}
                      </Button>
                      <Button
                        onClick={handleCancelResolution}
                        disabled={processing}
                        variant="outline"
                        className="flex-1"
                      >
                        Cancel
                      </Button>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* Human Intervention for Paused Tickets */}
          {dispute.status === "pending_review" && (
            <Card className="border-orange-500 border-2 bg-orange-50 dark:bg-orange-950/20">
              <CardHeader>
                <CardTitle className="text-orange-700 dark:text-orange-300 flex items-center">
                  <AlertCircle className="h-5 w-5 mr-2" />
                  Human Intervention Required
                </CardTitle>
                <CardDescription className="text-orange-600 dark:text-orange-400">
                  This dispute has been paused by the AI system and requires your decision to proceed.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {actionError && (
                  <div className="flex items-start gap-3 rounded-lg border border-red-200 bg-red-50 p-4 text-red-700">
                    <AlertCircle className="mt-0.5 h-5 w-5 shrink-0" />
                    <p className="text-sm">{actionError}</p>
                  </div>
                )}
                {actionSuccess && (
                  <div className="flex items-start gap-3 rounded-lg border border-green-200 bg-green-50 p-4 text-green-700">
                    <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0" />
                    <p className="text-sm">{actionSuccess}</p>
                  </div>
                )}
                <div className="bg-white dark:bg-gray-900 p-4 rounded-md border">
                  <p className="text-sm text-gray-700 dark:text-gray-300 mb-4">
                    The AI system has paused processing and is awaiting your decision. Choose to approve or reject this dispute to allow the system to continue processing with your override decision.
                  </p>
                  <div className="flex gap-3">
                    <Button
                      onClick={() => handleHumanOverride("approve")}
                      disabled={overrideProcessing}
                      className="flex-1 bg-green-600 hover:bg-green-700"
                    >
                      {overrideProcessing ? (
                        <>
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                          Processing...
                        </>
                      ) : (
                        <>
                          <CheckCircle2 className="h-4 w-4 mr-2" />
                          Approve Dispute
                        </>
                      )}
                    </Button>
                    <Button
                      onClick={() => handleHumanOverride("reject")}
                      disabled={overrideProcessing}
                      variant="destructive"
                      className="flex-1"
                    >
                      {overrideProcessing ? (
                        <>
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                          Processing...
                        </>
                      ) : (
                        <>
                          <XCircle className="h-4 w-4 mr-2" />
                          Reject Dispute
                        </>
                      )}
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Right Column - AI Audit Trail */}
        <div className="space-y-6">
          <Card className="sticky top-6">
            <CardHeader className="bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-950/30 dark:to-purple-950/30">
              <CardTitle className="text-xl">🤖 AI Audit Trail</CardTitle>
              <CardDescription>
                Complete reasoning and decision-making process for AI governance and explainability
              </CardDescription>
            </CardHeader>
            <CardContent className="pt-6">
              {audit_logs.length === 0 ? (
                <div className="text-center py-12">
                  <AlertCircle className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                  <p className="text-muted-foreground">No audit logs available for this ticket.</p>
                  <p className="text-sm text-muted-foreground mt-2">
                    Process the dispute to generate the AI audit trail.
                  </p>
                </div>
              ) : (
                <div className="space-y-4 max-h-[800px] overflow-y-auto pr-2">
                  {audit_logs.map((log, index) => {
                    const style = getActionTypeStyle(log.action_type);
                    return (
                      <div key={log.id} className="relative">
                        {/* Timeline connector */}
                        {index < audit_logs.length - 1 && (
                          <div className="absolute left-6 top-full w-0.5 h-4 bg-gradient-to-b from-gray-300 to-transparent dark:from-gray-700" />
                        )}
                        
                        {/* Audit log entry */}
                        <div className={`p-4 rounded-lg border-l-4 ${style.borderColor} ${style.bgColor} transition-all hover:shadow-md`}>
                          <div className="flex items-start justify-between mb-3">
                            <div className="flex items-center space-x-3">
                              <div className={`p-2 rounded-full ${style.bgColor} ${style.borderColor} border`}>
                                {style.icon}
                              </div>
                              <div>
                                <div className="flex items-center space-x-2">
                                  <Badge variant="outline" className={`${style.textColor} text-xs font-semibold`}>
                                    {style.label}
                                  </Badge>
                                  <span className="text-xs text-muted-foreground">
                                    {style.description}
                                  </span>
                                </div>
                                <p className="text-xs text-muted-foreground mt-1 font-medium">
                                  {log.agent_name}
                                </p>
                              </div>
                            </div>
                            <span className="text-xs text-muted-foreground whitespace-nowrap">
                              {new Date(log.timestamp).toLocaleTimeString()}
                            </span>
                          </div>
                          
                          <Separator className="my-3" />
                          
                          <div className={`text-sm ${style.textColor} leading-relaxed`}>
                            <p className="whitespace-pre-wrap font-mono text-xs bg-white/50 dark:bg-black/20 p-3 rounded">
                              {log.description}
                            </p>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

// Made with Bob
