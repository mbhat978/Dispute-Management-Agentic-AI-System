"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Landmark, UserCircle, Briefcase } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export default function HomePage() {
  const router = useRouter();
  const [loginType, setLoginType] = useState<"retail" | "employee">("retail");
  const [loginId, setLoginId] = useState("");
  const [loginPassword, setPassword] = useState("");
  const [loginError, setLoginError] = useState("");

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (loginType === "retail") {
      if (loginId === "4" || loginId === "5") {
        localStorage.setItem("banking_session", loginId);
        router.push("/customer");
      } else {
        setLoginError("Invalid Account ID or Password. Please try again.");
      }
    } else {
      // Employee login simulation
      if (loginId.toLowerCase() === "admin" || loginId.startsWith("E")) {
        localStorage.setItem("employee_session", loginId);
        router.push("/employee");
      } else {
        setLoginError("Invalid Employee ID. Use 'admin' for demo access.");
      }
    }
  };

  return (
    <div className="flex min-h-screen bg-white">
      {/* Left Marketing Side */}
      <div className="hidden lg:flex w-1/2 bg-slate-950 flex-col justify-between p-12 relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-blue-900/20 to-purple-900/20 z-0" />
        <div className="relative z-10 flex items-center gap-4">
          {/* Glowing Icon Container - Scaled Up */}
          <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-blue-500 to-indigo-600 shadow-xl shadow-indigo-500/30 border border-white/10">
            <Landmark className="h-8 w-8 text-white" />
          </div>
          
          {/* Stacked Gradient Typography - Scaled Up */}
          <div className="flex flex-col">
            <span className="bg-gradient-to-r from-white via-blue-50 to-slate-300 bg-clip-text text-3xl font-extrabold tracking-tight text-transparent">
              Agentic Dispute
            </span>
            <span className="text-xs font-bold uppercase tracking-[0.25em] text-indigo-300 mt-[-2px]">
              Resolution Center
            </span>
          </div>
        </div>
        <div className="relative z-10 max-w-lg">
          <h1 className="text-5xl font-light text-white leading-tight tracking-tighter mb-6">
            The future of <br/><span className="font-semibold">secure banking.</span>
          </h1>
          <p className="text-slate-400 text-lg">
            Access your digital wallet, monitor real-time transactions, and resolve disputes instantly with our next-generation AI support.
          </p>
        </div>
        <div className="relative z-10 text-slate-500 text-sm">
          © 2026 Retail Banking Corp. All rights reserved.
        </div>
      </div>
      
      {/* Right Login Side */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-8 bg-zinc-50 relative">
        <div className="w-full max-w-md">
          
          {/* Dynamic Toggle */}
          <div className="flex bg-zinc-200/60 p-1 rounded-2xl mb-8">
            <button
              onClick={() => { setLoginType("retail"); setLoginError(""); setLoginId(""); setPassword(""); }}
              className={`flex-1 flex items-center justify-center gap-2 py-3 rounded-xl text-sm font-semibold transition-all duration-200 ${loginType === "retail" ? "bg-white text-slate-900 shadow-sm" : "text-slate-500 hover:text-slate-700"}`}
            >
              <UserCircle className="w-4 h-4" /> Retail Customer
            </button>
            <button
              onClick={() => { setLoginType("employee"); setLoginError(""); setLoginId(""); setPassword(""); }}
              className={`flex-1 flex items-center justify-center gap-2 py-3 rounded-xl text-sm font-semibold transition-all duration-200 ${loginType === "employee" ? "bg-white text-slate-900 shadow-sm" : "text-slate-500 hover:text-slate-700"}`}
            >
              <Briefcase className="w-4 h-4" /> Employee Access
            </button>
          </div>

          <div className="text-center lg:text-left mb-8">
            <h2 className="text-3xl font-semibold text-slate-900 tracking-tight">
              {loginType === "retail" ? "Welcome back" : "Agent Portal"}
            </h2>
            <p className="text-slate-500 mt-2">
              {loginType === "retail" ? "Enter your Account ID to securely access your digital wallet." : "Enter your Employee ID to access the dispute dashboard."}
            </p>
          </div>
          
          <form onSubmit={handleLogin} className="space-y-6 bg-white p-8 rounded-3xl shadow-[0_8px_30px_rgb(0,0,0,0.04)] border border-slate-100">
            {loginError && (
              <div className="p-3 bg-red-50 text-red-600 text-sm rounded-xl border border-red-100">
                {loginError}
              </div>
            )}
            <div className="space-y-2">
              <Label htmlFor="accountId">{loginType === "retail" ? "Account ID" : "Employee ID"}</Label>
              <Input 
                id="accountId" 
                value={loginId}
                onChange={(e) => setLoginId(e.target.value)}
                placeholder={loginType === "retail" ? "e.g., 4" : "e.g., admin"} 
                className="bg-zinc-50 border-none py-6 rounded-xl focus-visible:ring-blue-500"
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Secure Password / PIN</Label>
              <Input 
                id="password" 
                type="password"
                value={loginPassword}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••" 
                className="bg-zinc-50 border-none py-6 rounded-xl focus-visible:ring-blue-500"
                required
              />
            </div>
            <Button type="submit" className="w-full py-6 rounded-xl bg-slate-900 hover:bg-slate-800 text-white font-medium text-base transition-all">
              Secure Login
            </Button>
            
            <div className="text-center mt-4">
              <p className="text-xs text-slate-400">
                {loginType === "retail" 
                  ? <>Demo Access: Use ID <strong>4</strong> or <strong>5</strong> with any password.</>
                  : <>Demo Access: Use ID <strong>admin</strong> with any password.</>
                }
              </p>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}

// Made with Bob
