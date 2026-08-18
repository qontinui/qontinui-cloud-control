"use client";

import React, { useState, useEffect } from "react";
import { X, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { FeedbackForm } from "@/components/feedback-form";

export function BetaBanner() {
  const [isVisible, setIsVisible] = useState(true);
  const [isHydrated, setIsHydrated] = useState(false);
  const [feedbackOpen, setFeedbackOpen] = useState(false);

  useEffect(() => {
    setIsHydrated(true);
    const dismissed = localStorage.getItem("beta-banner-dismissed") === "true";
    setIsVisible(!dismissed);
  }, []);

  const handleDismiss = () => {
    setIsVisible(false);
    if (typeof window !== "undefined") {
      localStorage.setItem("beta-banner-dismissed", "true");
    }
  };

  // Don't render anything until hydration is complete to avoid mismatch
  if (!isHydrated) {
    return null;
  }

  if (!isVisible) {
    return null;
  }

  return (
    <>
      <div className="bg-gradient-to-r from-blue-500 to-purple-600 text-white">
        <div className="px-4 py-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Sparkles className="h-4 w-4 flex-shrink-0" />
              <div className="flex flex-col sm:flex-row sm:items-center sm:gap-2">
                <span className="font-semibold text-sm">Beta!</span>
                <span className="text-xs opacity-90">
                  We&apos;re actively developing new features. Your feedback
                  helps us improve.
                </span>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="ghost"
                size="sm"
                className="text-white hover:bg-white/20 text-xs h-7"
                onClick={() => setFeedbackOpen(true)}
              >
                Give Feedback
              </Button>
              <Button
                variant="ghost"
                size="icon"
                className="text-white hover:bg-white/20 h-7 w-7"
                onClick={handleDismiss}
                aria-label="Dismiss beta banner"
              >
                <X className="h-3 w-3" />
              </Button>
            </div>
          </div>
        </div>
      </div>
      <FeedbackForm open={feedbackOpen} onOpenChange={setFeedbackOpen} />
    </>
  );
}
