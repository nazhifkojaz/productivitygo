/**
 * LoadingFallback Component
 *
 * A consistent loading state used across lazy-loaded routes.
 * Uses the NeoBrutalist design system for visual consistency.
 */
import React from 'react';

interface LoadingFallbackProps {
  message?: string;
}

export default function LoadingFallback({ message = 'LOADING...' }: LoadingFallbackProps) {
  return (
    <div className="h-screen flex items-center justify-center bg-neo-bg">
      <div className="text-center">
        <div className="font-black text-2xl md:text-3xl text-neo-black">
          {message}
        </div>
        {/* Optional: Add a pulsing indicator */}
        <div className="mt-4 flex justify-center gap-2">
          <div className="w-3 h-3 bg-neo-red animate-pulse" />
          <div className="w-3 h-3 bg-neo-green animate-pulse delay-75" />
          <div className="w-3 h-3 bg-neo-blue animate-pulse delay-150" />
        </div>
      </div>
    </div>
  );
}
