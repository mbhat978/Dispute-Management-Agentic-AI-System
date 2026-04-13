"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

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
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchDisputes() {
      try {
        const response = await fetch("http://localhost:8000/api/disputes");
        
        if (!response.ok) {
          throw new Error(`Failed to fetch disputes: ${response.statusText}`);
        }
        
        const data = await response.json();
        setDisputes(data.disputes || []);
      } catch (err) {
        setError(err instanceof Error ? err.message : "An error occurred");
        console.error("Error fetching disputes:", err);
      } finally {
        setLoading(false);
      }
    }

    fetchDisputes();
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