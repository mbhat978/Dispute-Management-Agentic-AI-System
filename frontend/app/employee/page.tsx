"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Briefcase, ShieldCheck, Activity, AlertCircle, CheckCircle2, Search } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

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
    case "resolved_approved":
      return { variant: "outline" as const, className: "bg-green-50 text-green-700 border-green-200 font-semibold" };
    case "auto_rejected":
    case "resolved_rejected":
      return { variant: "outline" as const, className: "bg-red-50 text-red-700 border-red-200 font-semibold" };
    case "human_review_required":
    case "pending_review":
      return { variant: "outline" as const, className: "bg-amber-50 text-amber-700 border-amber-200 font-semibold animate-pulse" };
    default:
      return { variant: "outline" as const, className: "bg-slate-50 text-slate-700 border-slate-200 font-semibold" };
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
  const router = useRouter();
  const [disputes, setDisputes] = useState<Dispute[]>([]);
  const [analytics, setAnalytics] = useState<Analytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [activeTab, setActiveTab] = useState<"all" | "review" | "resolved">("all");

  const filteredDisputes = useMemo(() => {
    return disputes.filter((d) => {
      const matchesSearch =
        d.customer_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        d.id.toString().includes(searchTerm);
      
      if (!matchesSearch) return false;
      
      if (activeTab === "review") return d.status === "human_review_required" || d.status === "pending_review" || d.status === "pending";
      if (activeTab === "resolved") return d.status !== "human_review_required" && d.status !== "pending_review" && d.status !== "pending" && d.status !== "under_investigation";
      return true;
    });
  }, [disputes, searchTerm, activeTab]);

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


  return (
    <div className="min-h-screen bg-zinc-50 pb-12">
      {/* Premium Header */}
      <div className="border-b bg-white shadow-sm">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="rounded-xl bg-slate-900 p-2 text-white shadow-md">
              <Briefcase className="h-5 w-5" />
            </div>
            <div>
              <p className="text-xs font-bold uppercase tracking-[0.2em] text-slate-500">Internal Operations</p>
              <h1 className="text-xl font-bold text-slate-900">Agent Command Center</h1>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <Button
              variant="outline"
              className="rounded-full px-6 bg-white hover:bg-slate-50 border-slate-200 text-slate-700 font-medium transition-all"
              onClick={() => {
                localStorage.removeItem("employee_session");
                router.push("/");
              }}
            >
              Sign Out
            </Button>
          </div>
        </div>
      </div>

      <div className="mx-auto max-w-7xl px-6 pt-8 space-y-8">

      {/* Executive Metrics Dashboard */}
      {analytics && (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
          <Card className="border-0 shadow-sm rounded-3xl bg-white overflow-hidden relative">
            <div className="absolute top-0 left-0 w-full h-1 bg-blue-500" />
            <CardContent className="p-6">
              <div className="flex justify-between items-start mb-4">
                <p className="text-sm font-semibold text-slate-500 uppercase tracking-wider">Total Disputes</p>
                <Activity className="h-5 w-5 text-blue-500" />
              </div>
              <div className="text-4xl font-light tracking-tighter text-slate-900">{analytics.total_disputes}</div>
              <p className="text-sm text-slate-500 mt-2">All-time tickets processed</p>
            </CardContent>
          </Card>

          <Card className="border-0 shadow-sm rounded-3xl bg-white overflow-hidden relative">
            <div className="absolute top-0 left-0 w-full h-1 bg-emerald-500" />
            <CardContent className="p-6">
              <div className="flex justify-between items-start mb-4">
                <p className="text-sm font-semibold text-slate-500 uppercase tracking-wider">Auto-Resolution</p>
                <CheckCircle2 className="h-5 w-5 text-emerald-500" />
              </div>
              <div className="text-4xl font-light tracking-tighter text-emerald-600">{(analytics.auto_resolution_rate ?? 0).toFixed(1)}%</div>
              <div className="mt-3 w-full bg-slate-100 rounded-full h-1.5">
                <div className="bg-emerald-500 h-1.5 rounded-full" style={{ width: `${analytics.auto_resolution_rate ?? 0}%` }} />
              </div>
            </CardContent>
          </Card>

          <Card className="border-0 shadow-sm rounded-3xl bg-white overflow-hidden relative">
            <div className="absolute top-0 left-0 w-full h-1 bg-amber-500" />
            <CardContent className="p-6">
              <div className="flex justify-between items-start mb-4">
                <p className="text-sm font-semibold text-slate-500 uppercase tracking-wider">Needs Review</p>
                <AlertCircle className="h-5 w-5 text-amber-500" />
              </div>
              <div className="text-4xl font-light tracking-tighter text-amber-600">{analytics.human_intervention_required}</div>
              <p className="text-sm text-amber-700/70 mt-2 font-medium">Awaiting agent action</p>
            </CardContent>
          </Card>

          <Card className="border-0 shadow-sm rounded-3xl bg-white overflow-hidden relative">
            <div className="absolute top-0 left-0 w-full h-1 bg-purple-500" />
            <CardContent className="p-6">
              <div className="flex justify-between items-start mb-4">
                <p className="text-sm font-semibold text-slate-500 uppercase tracking-wider">Fraud Prevented</p>
                <ShieldCheck className="h-5 w-5 text-purple-500" />
              </div>
              <div className="text-4xl font-light tracking-tighter text-purple-600">
                ${(analytics.total_fraud_prevented ?? 0).toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}
              </div>
              <p className="text-sm text-slate-500 mt-2">Saved by AI detection</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Main Content Card */}
      <Card className="border-0 shadow-[0_8px_30px_rgb(0,0,0,0.04)] rounded-3xl bg-white overflow-hidden">
        <CardHeader className="border-b border-slate-100 pb-4">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <CardTitle className="text-xl text-slate-900">Ticket Inbox</CardTitle>
              <CardDescription>Manage and resolve customer disputes</CardDescription>
            </div>
            
            {/* Search & Tabs Toolbar */}
            <div className="flex flex-col sm:flex-row items-center gap-3">
              <div className="relative w-full sm:w-64">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                <Input
                  placeholder="Search by name or ID..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-9 bg-slate-50 border-slate-200 rounded-xl focus-visible:ring-blue-500 w-full"
                />
              </div>
              <div className="flex bg-slate-100 p-1 rounded-xl w-full sm:w-auto">
                <button
                  onClick={() => setActiveTab("all")}
                  className={`px-4 py-2 text-sm font-medium rounded-lg transition-all flex-1 sm:flex-none ${activeTab === "all" ? "bg-white text-slate-900 shadow-sm" : "text-slate-500 hover:text-slate-700"}`}
                >
                  All
                </button>
                <button
                  onClick={() => setActiveTab("review")}
                  className={`px-4 py-2 text-sm font-medium rounded-lg transition-all flex-1 sm:flex-none flex items-center justify-center gap-2 ${activeTab === "review" ? "bg-white text-slate-900 shadow-sm" : "text-slate-500 hover:text-slate-700"}`}
                >
                  Action Required
                  {disputes.filter(d => d.status === "human_review_required" || d.status === "pending_review").length > 0 && (
                    <span className="bg-red-500 text-white text-[10px] px-1.5 py-0.5 rounded-full">
                      {disputes.filter(d => d.status === "human_review_required" || d.status === "pending_review").length}
                    </span>
                  )}
                </button>
                <button
                  onClick={() => setActiveTab("resolved")}
                  className={`px-4 py-2 text-sm font-medium rounded-lg transition-all flex-1 sm:flex-none ${activeTab === "resolved" ? "bg-white text-slate-900 shadow-sm" : "text-slate-500 hover:text-slate-700"}`}
                >
                  Resolved
                </button>
              </div>
            </div>
          </div>
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

          {!loading && !error && filteredDisputes.length === 0 && (
            <div className="flex flex-col justify-center items-center py-16 text-center">
              <div className="h-16 w-16 bg-slate-50 rounded-full flex items-center justify-center mb-4">
                <Search className="h-8 w-8 text-slate-300" />
              </div>
              <h3 className="text-lg font-semibold text-slate-900">No tickets found</h3>
              <p className="text-slate-500 max-w-sm mt-1">
                {disputes.length === 0
                  ? "There are currently no disputes in the system."
                  : "We couldn't find any tickets matching your current search or filter."}
              </p>
              {disputes.length > 0 && (
                <Button
                  variant="link"
                  onClick={() => { setSearchTerm(""); setActiveTab("all"); }}
                  className="mt-2 text-blue-600"
                >
                  Clear all filters
                </Button>
              )}
            </div>
          )}

          {!loading && !error && filteredDisputes.length > 0 && (
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
                  {filteredDisputes.map((dispute) => {
                    const statusBadge = getStatusBadge(dispute.status);
                    return (
                      <TableRow
                        key={dispute.id}
                        onClick={() => router.push(`/ticket/${dispute.id}`)}
                        className="cursor-pointer hover:bg-slate-50 transition-colors group"
                      >
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
                            <Button variant="ghost" size="sm" className="hover:bg-blue-50 hover:text-blue-700 font-semibold transition-colors">
                              Review Ticket →
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
      </div>
    </div>
  );
}