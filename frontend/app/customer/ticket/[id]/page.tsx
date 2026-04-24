"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { ArrowLeft, CheckCircle2, XCircle, Clock, CreditCard, AlertCircle, Receipt } from "lucide-react";

interface Transaction {
  id: number;
  amount: number;
  merchant_name: string;
  transaction_date: string;
  status: string;
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
  transaction: Transaction;
  audit_logs: AuditLog[];
}

function getStatusBadge(status: string) {
  if (status === "auto_approved" || status === "resolved_approved") {
    return {
      className: "bg-green-500 hover:bg-green-600 text-white",
      icon: <CheckCircle2 className="h-4 w-4 mr-1" />
    };
  } else if (status === "auto_rejected" || status === "resolved_rejected") {
    return {
      className: "bg-red-500 hover:bg-red-600 text-white",
      icon: <XCircle className="h-4 w-4 mr-1" />
    };
  } else {
    return {
      className: "bg-yellow-500 hover:bg-yellow-600 text-black",
      icon: <Clock className="h-4 w-4 mr-1" />
    };
  }
}

function formatStatus(status: string): string {
  return status.split("_").map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(" ");
}

export default function CustomerTicketPage() {
  const params = useParams();
  const ticketId = params.id as string;
  const [ticketData, setTicketData] = useState<TicketData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchTicketDetails() {
      try {
        const response = await fetch(`http://localhost:8000/api/disputes/${ticketId}`);
        if (!response.ok) {
          throw new Error(`Failed to fetch ticket details: ${response.statusText}`);
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

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-screen bg-slate-50">
        <div className="text-center space-y-4">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="text-slate-600">Loading ticket details...</p>
        </div>
      </div>
    );
  }

  if (error || !ticketData) {
    return (
      <div className="flex flex-col justify-center items-center min-h-screen bg-slate-50 space-y-4">
        <AlertCircle className="h-16 w-16 text-red-500" />
        <p className="text-red-500 text-lg font-semibold">Error: {error || "Ticket not found"}</p>
        <Link href="/customer">
          <Button variant="outline">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Portal
          </Button>
        </Link>
      </div>
    );
  }

  const { dispute, transaction, audit_logs } = ticketData;
  const statusBadge = getStatusBadge(dispute.status);

  // Parse resolution notes if it's a JSON string
  let resolutionContent = dispute.resolution_notes;
  if (dispute.resolution_notes) {
    try {
      const parsed = JSON.parse(dispute.resolution_notes);
      if (parsed.justification) {
        resolutionContent = parsed.justification;
      }
    } catch {
      // If parsing fails, use as-is
      resolutionContent = dispute.resolution_notes;
    }
  }

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <div className="bg-white border-b border-slate-200 sticky top-0 z-10 shadow-sm">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <Link href="/customer">
                <Button variant="ghost" size="sm" className="hover:bg-slate-100">
                  <ArrowLeft className="h-4 w-4 mr-2" />
                  Back to Portal
                </Button>
              </Link>
              <Separator orientation="vertical" className="h-8" />
              <div>
                <h1 className="text-2xl font-bold text-slate-900">Ticket #{dispute.id}</h1>
                <p className="text-sm text-slate-500">
                  Submitted on {new Date(dispute.created_at).toLocaleDateString()}
                </p>
              </div>
            </div>
            <Badge className={`${statusBadge.className} text-base px-4 py-2`}>
              {statusBadge.icon}
              {formatStatus(dispute.status)}
            </Badge>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="container mx-auto px-6 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column - Main Details */}
          <div className="lg:col-span-2 space-y-6">
            {/* Transaction Details Card */}
            <Card className="shadow-md">
              <CardHeader className="bg-gradient-to-r from-blue-50 to-indigo-50">
                <CardTitle className="flex items-center text-slate-900">
                  <CreditCard className="h-5 w-5 mr-2 text-blue-600" />
                  Transaction Details
                </CardTitle>
                <CardDescription>Information about the disputed transaction</CardDescription>
              </CardHeader>
              <CardContent className="pt-6 space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm font-medium text-slate-500">Merchant</p>
                    <p className="text-lg font-semibold text-slate-900">{transaction.merchant_name}</p>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-slate-500">Amount</p>
                    <p className="text-2xl font-bold text-red-600">${transaction.amount.toFixed(2)}</p>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-slate-500">Transaction Date</p>
                    <p className="text-base text-slate-900">
                      {new Date(transaction.transaction_date).toLocaleDateString()}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-slate-500">Transaction ID</p>
                    <p className="text-base font-mono text-slate-900">{transaction.id}</p>
                  </div>
                </div>
                <Separator />
                <div>
                  <p className="text-sm font-medium text-slate-500 mb-2">Your Dispute Reason</p>
                  <p className="text-sm text-slate-700 bg-slate-50 p-4 rounded-lg border border-slate-200 leading-relaxed">
                    {dispute.dispute_reason}
                  </p>
                </div>
              </CardContent>
            </Card>

            {/* Decision & Reasoning Card */}
            {resolutionContent && (
              <Card className="shadow-md border-2 border-blue-200">
                <CardHeader className="bg-gradient-to-r from-green-50 to-emerald-50">
                  <CardTitle className="flex items-center text-slate-900">
                    <CheckCircle2 className="h-5 w-5 mr-2 text-green-600" />
                    Decision & Reasoning
                  </CardTitle>
                  <CardDescription>AI system's analysis and decision</CardDescription>
                </CardHeader>
                <CardContent className="pt-6">
                  <div className="bg-white p-4 rounded-lg border border-slate-200">
                    <p className="text-sm text-slate-700 leading-relaxed whitespace-pre-wrap">
                      {resolutionContent}
                    </p>
                  </div>
                  <div className="mt-4 pt-4 border-t border-slate-200">
                    <p className="text-xs text-slate-500">
                      Last updated: {new Date(dispute.updated_at).toLocaleString()}
                    </p>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>

          {/* Right Column - Activity Log */}
          <div className="lg:col-span-1">
            <Card className="shadow-md sticky top-24">
              <CardHeader className="bg-gradient-to-r from-purple-50 to-pink-50">
                <CardTitle className="flex items-center text-slate-900">
                  <Receipt className="h-5 w-5 mr-2 text-purple-600" />
                  Activity Log
                </CardTitle>
                <CardDescription>Step-by-step processing history</CardDescription>
              </CardHeader>
              <CardContent className="pt-6">
                {audit_logs.length === 0 ? (
                  <div className="text-center py-8">
                    <AlertCircle className="h-10 w-10 text-slate-300 mx-auto mb-3" />
                    <p className="text-sm text-slate-500">No activity logs available yet.</p>
                  </div>
                ) : (
                  <div className="space-y-4 max-h-[600px] overflow-y-auto pr-2">
                    {audit_logs.map((log, index) => (
                      <div key={log.id} className="relative">
                        {/* Timeline connector */}
                        {index < audit_logs.length - 1 && (
                          <div className="absolute left-4 top-10 w-0.5 h-full bg-slate-200" />
                        )}
                        
                        {/* Log entry */}
                        <div className="flex gap-3">
                          <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 font-semibold text-xs z-10">
                            {index + 1}
                          </div>
                          <div className="flex-1 pb-4">
                            <div className="bg-slate-50 rounded-lg p-3 border border-slate-200">
                              <div className="flex items-center justify-between mb-2">
                                <Badge variant="outline" className="text-xs">
                                  {log.action_type}
                                </Badge>
                                <span className="text-xs text-slate-500">
                                  {new Date(log.timestamp).toLocaleTimeString()}
                                </span>
                              </div>
                              <p className="text-xs font-medium text-slate-600 mb-1">
                                {log.agent_name}
                              </p>
                              <p className="text-xs text-slate-700 leading-relaxed">
                                {log.description}
                              </p>
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}

// Made with Bob
