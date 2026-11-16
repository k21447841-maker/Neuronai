#!/usr/bin/env bash
FILE="src/pages/AuthPage.tsx"
cat << 'TSX' > "$FILE"
import { useState } from "react";
import { useNavigate } from "react-router-dom";

export function AuthPage() {
  const [isLogin, setIsLogin] = useState(true);
  const navigate = useNavigate();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    navigate("/");
  };

  return (
    <div className="min-h-screen bg-[#0a0a0f] flex items-center justify-center p-4">
      <div className="w-full max-w-md bg-white/5 backdrop-blur-xl border border-white/10 rounded-2xl p-8 shadow-2xl">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-white mb-2">NEUROFLOW AI</h1>
          <p className="text-gray-400">Your AI YouTube Automation Studio</p>
        </div>

        <div className="flex gap-4 mb-6">
          <button onClick={() => setIsLogin(true)} className={`flex-1 pb-2 text-sm font-medium transition-colors ${isLogin ? "text-purple-400 border-b-2 border-purple-400" : "text-gray-500 hover:text-gray-300"}`}>Login</button>
          <button onClick={() => setIsLogin(false)} className={`flex-1 pb-2 text-sm font-medium transition-colors ${!isLogin ? "text-purple-400 border-b-2 border-purple-400" : "text-gray-500 hover:text-gray-300"}`}>Sign Up</button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">Email</label>
            <input type="email" required className="w-full px-4 py-2 bg-black/50 border border-white/10 rounded-lg focus:ring-2 focus:ring-purple-500 text-white outline-none transition-all" placeholder="you@example.com" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">Password</label>
            <input type="password" required className="w-full px-4 py-2 bg-black/50 border border-white/10 rounded-lg focus:ring-2 focus:ring-purple-500 text-white outline-none transition-all" placeholder="••••••••" />
          </div>
          <button type="submit" className="w-full py-3 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-500 hover:to-pink-500 text-white font-semibold rounded-lg shadow-lg shadow-purple-500/30 transition-all transform hover:scale-[1.02]">
            {isLogin ? "Sign In" : "Create Account"}
          </button>
        </form>
      </div>
    </div>
  );
}
TSX
echo "AuthPage updated!"
