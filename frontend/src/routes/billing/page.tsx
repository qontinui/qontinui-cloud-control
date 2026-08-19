"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { AlertCircle, ExternalLink, Loader2 } from "lucide-react";
import { billingService } from "@/services/service-factory";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  SubscriptionBadge,
  type SubscriptionBadgeSource,
} from "../../components/subscription-badge";
import type { Subscription, TierLimits } from "../../services/billing-service";

/**
 * `/billing` — the account-side billing landing page.
 *
 * This route existed only as a nav target until now: `navItems` advertised
 * `/billing`, but the only billing routes were `/billing/success` and
 * `/billing/canceled`, the two Stripe redirect targets. The link 404'd in
 * every deployment. Registering a real landing page is the fix rather than
 * repointing the nav item at `/pricing`, which is a marketing surface — a
 * signed-in user asking about billing wants what they are on and how to
 * change it, not the public tier table.
 *
 * What it shows: the current subscription and its plan limits, a route into
 * the Stripe customer portal, and a link to `/pricing` for a plan change.
 *
 * Errors are reported, never papered over. `routes/pricing.tsx` reads
 * `subscription?.tier || "free"` to decide button states, which is fine there
 * (the worst case is an over-offered upgrade); here the tier IS the content,
 * so a failed fetch renders an error card rather than a confident "Free".
 */
export default function BillingPage() {
  const [subscription, setSubscription] = useState<Subscription | null>(null);
  const [limits, setLimits] = useState<TierLimits | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [limitsError, setLimitsError] = useState(false);
  const [portalPending, setPortalPending] = useState(false);
  const [portalError, setPortalError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setLoadError(null);
    setLimitsError(false);
    try {
      // Settled, not `all`: the limits endpoint failing should not blank out
      // the subscription the user actually came here to read. Each half
      // reports its own outcome — a silent `null` would be indistinguishable
      // from "this plan has no limits", which is the papering-over this page
      // says it does not do.
      const [subResult, limitsResult] = await Promise.allSettled([
        billingService.getSubscription(),
        billingService.getTierLimits(),
      ]);
      if (subResult.status === "fulfilled") {
        setSubscription(subResult.value);
      } else {
        console.error("Failed to load subscription:", subResult.reason);
        setLoadError("Could not load your subscription.");
      }
      if (limitsResult.status === "fulfilled") {
        setLimits(limitsResult.value);
      } else {
        console.error("Failed to load plan limits:", limitsResult.reason);
        setLimits(null);
        setLimitsError(true);
      }
    } finally {
      setLoading(false);
    }
  }, []);

  // The badge renders in this page's header, so it reads the subscription this
  // component already owns instead of fetching its own. Uncontrolled it would
  // issue a second identical request, and on the error path it could show a
  // confident "Pro" directly above a card saying the subscription could not be
  // loaded.
  const badgeSource: SubscriptionBadgeSource = loading
    ? { status: "loading" }
    : loadError
      ? { status: "error" }
      : { status: "ready", subscription };

  useEffect(() => {
    void load();
  }, [load]);

  const openPortal = async () => {
    setPortalPending(true);
    setPortalError(null);
    try {
      await billingService.redirectToBillingPortal();
    } catch (error) {
      console.error("Failed to open billing portal:", error);
      setPortalError(
        "Could not open the billing portal. Please try again in a moment."
      );
      setPortalPending(false);
    }
    // On success the browser navigates away, so `portalPending` is left true
    // deliberately — clearing it would flash the button back to enabled
    // during the redirect.
  };

  return (
    <div className="container mx-auto max-w-3xl px-4 py-10 space-y-6">
      <header className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold">Billing</h1>
          <p className="text-sm text-muted-foreground">
            Your plan, its limits, and how to change it.
          </p>
        </div>
        <SubscriptionBadge source={badgeSource} />
      </header>

      <Card>
        <CardHeader>
          <CardTitle>Current plan</CardTitle>
          <CardDescription>
            Managed through Stripe. Changes take effect immediately.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {loading ? (
            <div
              className="flex items-center gap-2 text-sm text-muted-foreground"
              aria-busy="true"
            >
              <Loader2 className="h-4 w-4 animate-spin" />
              Loading your subscription&hellip;
            </div>
          ) : loadError ? (
            <div className="space-y-3">
              <p className="flex items-start gap-2 text-sm text-destructive">
                <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
                {loadError}
              </p>
              <Button variant="outline" size="sm" onClick={() => void load()}>
                Try again
              </Button>
            </div>
          ) : (
            <dl className="grid grid-cols-1 gap-3 text-sm sm:grid-cols-2">
              <div>
                <dt className="text-muted-foreground">Status</dt>
                <dd className="font-medium">
                  {subscription?.status || "unknown"}
                </dd>
              </div>
              <div>
                <dt className="text-muted-foreground">Renews</dt>
                <dd className="font-medium">
                  {subscription?.current_period_end
                    ? new Date(
                        subscription.current_period_end
                      ).toLocaleDateString()
                    : "—"}
                  {subscription?.cancel_at_period_end
                    ? " (cancels at period end)"
                    : ""}
                </dd>
              </div>
              {limitsError && (
                <div className="sm:col-span-2">
                  <p className="flex items-start gap-2 text-muted-foreground">
                    <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
                    Plan limits are unavailable right now. Your subscription
                    above is unaffected.
                  </p>
                </div>
              )}
              {limits && (
                <>
                  <div>
                    <dt className="text-muted-foreground">Configurations</dt>
                    <dd className="font-medium">
                      {limits.max_configs.toLocaleString()}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-muted-foreground">Images</dt>
                    <dd className="font-medium">
                      {limits.max_images.toLocaleString()}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-muted-foreground">Storage</dt>
                    <dd className="font-medium">
                      {limits.max_storage_mb.toLocaleString()} MB
                    </dd>
                  </div>
                </>
              )}
            </dl>
          )}
        </CardContent>
      </Card>

      <div className="flex flex-wrap items-center gap-3">
        <Button onClick={() => void openPortal()} disabled={portalPending}>
          {portalPending ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Opening&hellip;
            </>
          ) : (
            <>
              Manage billing
              <ExternalLink className="ml-2 h-4 w-4" />
            </>
          )}
        </Button>
        <Button variant="outline" asChild>
          <Link href="/pricing">Compare plans</Link>
        </Button>
      </div>
      {portalError && (
        <p className="flex items-start gap-2 text-sm text-destructive">
          <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
          {portalError}
        </p>
      )}
    </div>
  );
}
