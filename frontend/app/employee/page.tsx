"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Brain, Radio, WifiOff } from "lucide-react";

// Define the Dispute type based on our API response
interface Dispute {
  id: number;
  customer_name: string;
  customer_id: number;
  dispute_reason: string;
  status: string;
  amount: number;
  created_at: string | null;
}

// Define the Analytics type for executive metrics
interface Analytics {
  total_disputes: number;
  auto_resolution_rate: number;
  human_intervention_required: number;
  total_fraud_prevented: number;
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


// Function to get badge variant and color based on status
function getStatusBadge(status: string) {
  switch (status) {
    case "auto_approved":
      return { variant: "default" as const, className: "bg-green-500 hover:bg-green-600" };
    case "auto_rejected":
      return { variant: "destructive" as const, className: "" };
    case "human_review_required":
      return { variant: "secondary" as const, className: "bg-yellow-500 hover:bg-yellow-600 text-black" };
    case "pending":
      return { variant: "outline" as const, className: "" };
    default:
      return { variant: "outline" as const, className: "" };
  }
}

// Function to format status text
function formatStatus(status: string): string {
  return status
    .split("_")
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

export default function DashboardPage() {
  const [disputes, setDisputes] = useState<Dispute[]>([]);
  const [analytics, setAnalytics] = useState<Analytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [agentLogs, setAgentLogs] = useState<string[]>([]);
  const [streamConnected, setStreamConnected] = useState(false);

  // Fetch disputes and analytics data
  useEffect(() => {
    async function fetchData() {
      try {
        // Fetch both disputes and analytics in parallel
        const [disputesResponse, analyticsResponse] = await Promise.all([
          fetch("http://localhost:8000/api/disputes"),
          fetch("http://localhost:8000/api/analytics")
        ]);
        
        if (!disputesResponse.ok) {
          const errorData: ApiErrorResponse = await disputesResponse.json().catch(() => ({}));
          throw new Error(getErrorMessage(errorData, `Failed to fetch disputes: ${disputesResponse.statusText}`));
        }
        
        if (!analyticsResponse.ok) {
          const errorData: ApiErrorResponse = await analyticsResponse.json().catch(() => ({}));
          throw new Error(getErrorMessage(errorData, `Failed to fetch analytics: ${analyticsResponse.statusText}`));
        }
        
        const disputesData = await disputesResponse.json();
        const analyticsData = await analyticsResponse.json();
        
        setDisputes(disputesData.disputes || []);
        setAnalytics(analyticsData);
      } catch (err) {
        setError(err instanceof Error ? err.message : "An error occurred");
        console.error("Error fetching data:", err);
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, []);

  // Connect to the real-time agent log stream
  useEffect(() => {
    const eventSource = new EventSource("http://localhost:8000/api/disputes/stream");
    
    eventSource.onopen = () => {
      console.log("[Employee Dashboard] SSE connection opened");
      setStreamConnected(true);
    };
    
    // Register event handlers for different event types
    const handleAgentUpdate = (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data);
        const timestamp = new Date().toLocaleTimeString();
        
        // Format agent activity log
        let logMessage = "";
        if (data.agent_name) {
          logMessage = `[${timestamp}] 🤖 ${data.agent_name}: ${data.message}`;
          if (data.activity_summary) {
            logMessage += ` | ${data.activity_summary}`;
          }
        } else {
          logMessage = `[${timestamp}] ${data.message || 'Agent activity update'}`;
        }
        
        setAgentLogs((prevLogs) => [...prevLogs, logMessage].slice(-50)); // Keep last 50 logs
      } catch (err) {
        console.error("[Employee Dashboard] Error parsing agent_update:", err);
      }
    };
    
    const handleProcessingStarted = (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data);
        const timestamp = new Date().toLocaleTimeString();
        const logMessage = `[${timestamp}] 🚀 Started processing dispute #${data.ticket_id} - ${data.customer_query}`;
        setAgentLogs((prevLogs) => [...prevLogs, logMessage].slice(-50));
      } catch (err) {
        console.error("[Employee Dashboard] Error parsing processing_started:", err);
      }
    };
    
    const handleProcessingCompleted = (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data);
        const timestamp = new Date().toLocaleTimeString();
        const logMessage = `[${timestamp}] ✅ Completed dispute #${data.ticket_id} - Decision: ${data.final_decision?.toUpperCase()}`;
        setAgentLogs((prevLogs) => [...prevLogs, logMessage].slice(-50));
      } catch (err) {
        console.error("[Employee Dashboard] Error parsing processing_completed:", err);
      }
    };
    
    const handleProcessingFailed = (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data);
        const timestamp = new Date().toLocaleTimeString();
        const logMessage = `[${timestamp}] ❌ Failed processing dispute #${data.ticket_id} - ${data.error}`;
        setAgentLogs((prevLogs) => [...prevLogs, logMessage].slice(-50));
      } catch (err) {
        console.error("[Employee Dashboard] Error parsing processing_failed:", err);
      }
    };
    
    // Register specific event listeners (heartbeat is intentionally not registered)
    eventSource.addEventListener("agent_update", handleAgentUpdate);
    eventSource.addEventListener("processing_started", handleProcessingStarted);
    eventSource.addEventListener("processing_completed", handleProcessingCompleted);
    eventSource.addEventListener("processing_failed", handleProcessingFailed);
    
    eventSource.onerror = (err) => {
      console.error("[Employee Dashboard] SSE error:", err);
      setStreamConnected(false);
    };
    
    // Cleanup function to close the connection when component unmounts
    return () => {
      console.log("[Employee Dashboard] Closing SSE connection");
      eventSource.close();
    };
  }, []);

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Dispute Dashboard</h1>
          <p className="text-muted-foreground mt-2">
            View and manage all banking dispute tickets
          </p>
        </div>
        <Link href="/">
          <Button variant="outline">
            Log Out
          </Button>
        </Link>
      </div>

      {/* Executive Metrics Dashboard */}
      {analytics && (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {/* Card 1: Total Disputes */}
          <Card className="border-l-4 border-l-blue-500">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Total Disputes
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">{analytics.total_disputes}</div>
              <p className="text-xs text-muted-foreground mt-1">
                All-time dispute tickets
              </p>
            </CardContent>
          </Card>

          {/* Card 2: Auto-Resolution Rate */}
          <Card className="border-l-4 border-l-green-500">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Auto-Resolution Rate
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-green-600">
                {(analytics.auto_resolution_rate ?? 0).toFixed(1)}%
              </div>
              <div className="mt-2">
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-green-600 h-2 rounded-full transition-all duration-500"
                    style={{ width: `${analytics.auto_resolution_rate ?? 0}%` }}
                  />
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  High efficiency indicator
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Card 3: Human Intervention Required */}
          <Card className="border-l-4 border-l-yellow-500">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Human Intervention Required
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-yellow-600">
                {analytics.human_intervention_required}
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                Tickets pending review
              </p>
            </CardContent>
          </Card>

          {/* Card 4: Total Fraud Prevented */}
          <Card className="border-l-4 border-l-purple-500">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Total Fraud Prevented
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-purple-600">
                ${(analytics.total_fraud_prevented ?? 0).toLocaleString('en-US', {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2
                })}
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                Fraudulent claims blocked
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Main Content Card */}
      <Card>
        <CardHeader>
          <CardTitle>All Disputes</CardTitle>
          <CardDescription>
            A comprehensive list of all dispute tickets with their current status
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading && (
            <div className="flex justify-center items-center py-8">
              <p className="text-muted-foreground">Loading disputes...</p>
            </div>
          )}

          {error && (
            <div className="flex justify-center items-center py-8">
              <p className="text-red-500">Error: {error}</p>
            </div>
          )}

          {!loading && !error && disputes.length === 0 && (
            <div className="flex justify-center items-center py-8">
              <p className="text-muted-foreground">No disputes found</p>
            </div>
          )}

          {!loading && !error && disputes.length > 0 && (
            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-[100px]">Ticket ID</TableHead>
                    <TableHead>Customer Name</TableHead>
                    <TableHead>Dispute Reason</TableHead>
                    <TableHead>Amount</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead className="text-right">Action</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {disputes.map((dispute) => {
                    const statusBadge = getStatusBadge(dispute.status);
                    return (
                      <TableRow key={dispute.id}>
                        <TableCell className="font-medium">#{dispute.id}</TableCell>
                        <TableCell>{dispute.customer_name}</TableCell>
                        <TableCell className="max-w-md truncate">
                          {dispute.dispute_reason}
                        </TableCell>
                        <TableCell>${dispute.amount.toFixed(2)}</TableCell>
                        <TableCell>
                          <Badge 
                            variant={statusBadge.variant}
                            className={statusBadge.className}
                          >
                            {formatStatus(dispute.status)}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-right">
                          <Link href={`/ticket/${dispute.id}`}>
                            <Button variant="outline" size="sm">
                              View Details
                            </Button>
                          </Link>
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Real-Time AI Agent Logs */}
      <Card className="border-2 border-blue-500/20">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Brain className="h-5 w-5 text-blue-500" />
              <CardTitle>AI Agent Activity Stream</CardTitle>
            </div>
            <div className="flex items-center gap-2">
              {streamConnected ? (
                <>
                  <Radio className="h-4 w-4 text-green-500 animate-pulse" />
                  <span className="text-xs text-green-500 font-medium">Live</span>
                </>
              ) : (
                <>
                  <WifiOff className="h-4 w-4 text-red-500" />
                  <span className="text-xs text-red-500 font-medium">Disconnected</span>
                </>
              )}
            </div>
          </div>
          <CardDescription>
            Watch AI agents think and process disputes in real-time
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="bg-black rounded-lg p-4 h-96 overflow-y-auto font-mono text-sm">
            {agentLogs.length === 0 ? (
              <div className="flex items-center justify-center h-full text-green-400">
                <p>Waiting for agent activity...</p>
              </div>
            ) : (
              <div className="space-y-1">
                {agentLogs.map((log, index) => (
                  <div key={index} className="text-green-400">
                    <span className="text-gray-500">[{new Date().toLocaleTimeString()}]</span>{" "}
                    {log}
                  </div>
                ))}
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Summary Stats */}
      {!loading && !error && disputes.length > 0 && (
        <div className="grid gap-4 md:grid-cols-4">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium">Total Disputes</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{disputes.length}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium">Auto Approved</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-green-600">
                {disputes.filter(d => d.status === "auto_approved").length}
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium">Auto Rejected</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-red-600">
                {disputes.filter(d => d.status === "auto_rejected").length}
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium">Needs Review</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-yellow-600">
                {disputes.filter(d => d.status === "human_review_required").length}
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}