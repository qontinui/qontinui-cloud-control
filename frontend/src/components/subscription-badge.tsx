"use client";

import { useState, useEffect } from "react";
import { Crown, Loader2, Sparkles, Zap } from "lucide-react";
import { billingService } from "@/services/service-factory";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { Subscription } from "../services/billing-service";

type Tier = Subscription["tier"];

const TIER_ICONS: Record<Tier, React.ReactNode> = {
  free: <Sparkles className="h-3.5 w-3.5" />,
  hobby: <Zap className="h-3.5 w-3.5" />,
  pro: <Crown className="h-3.5 w-3.5" />,
};

const TIER_LABELS: Record<Tier, string> = {
  free: "Free",
  hobby: "Hobby",
  pro: "Pro",
};

/**
 * Neutral styling: the `free` tier's normal look, and also the look a paid
 * tier falls back to when its billing status is not healthy — muted rather
 * than the tier's confident accent colour.
 */
const NEUTRAL_STYLE = "bg-muted text-muted-foreground border-border";

const TIER_STYLES: Record<Tier, string> = {
  free: NEUTRAL_STYLE,
  hobby: "bg-blue-500/10 text-blue-500 border-blue-500/30",
  pro: "bg-amber-500/10 text-amber-500 border-amber-500/30",
};

/**
 * Subscription statuses under which a paid tier is genuinely being paid for.
 * `Subscription["status"]` is a free-form `string` (it is Stripe-derived and
 * the set grows), so the comparison is case-insensitive and everything not
 * listed here counts as not-healthy rather than assuming a closed union.
 */
const HEALTHY_STATUSES = new Set(["active", "trialing"]);

function isHealthyStatus(status: string | undefined): boolean {
  return HEALTHY_STATUSES.has((status ?? "").trim().toLowerCase());
}

/**
 * Renders the signed-in user's real subscription tier.
 *
 * Three visually distinct states:
 *  - loading: a spinner placeholder that cannot be mistaken for a tier
 *  - error / no subscription: nothing at all — this badge asserts what the
 *    user pays for, so it must never guess (deliberately NOT the
 *    `?.tier || "free"` fallback that `routes/pricing.tsx` uses for its
 *    button states)
 *  - loaded: the real tier, styled and labelled per tier
 *
 * The loaded state also accounts for `subscription.status`: a `past_due` /
 * `unpaid` / `incomplete` Pro is still a Pro (hiding it would be its own
 * misstatement), but it must not be rendered in the confident tier accent as
 * though nothing were wrong. Such a badge renders muted and carries a `title`
 * naming the actual status, so the discrepancy is inspectable rather than
 * invisible. `cancel_at_period_end` is surfaced in that same `title` but does
 * NOT mute the badge: the subscription is valid until period end, so the tier
 * label is accurate. The `free` tier has no meaningful billing status and is
 * always rendered normally.
 *
 * **Self-fetching by default, controllable by a caller that already has the
 * data.** The component slot it is registered into declares empty props, so
 * with no props it fetches its own subscription — that is the sidebar path and
 * it is unchanged. A caller that has already loaded the subscription passes
 * `source` instead, which suppresses the fetch.
 *
 * That option exists because `routes/billing/page.tsx` renders this badge in a
 * header directly above a card built from its own `getSubscription()` call:
 * uncontrolled, that is two identical requests per page load, and on the error
 * path the card can say "Could not load your subscription" while the badge's
 * independent fetch succeeded and reads "Pro" three inches away. One owner of
 * the fetch removes both.
 *
 * `source` is a discriminated union rather than a nullable subscription so
 * "the caller is still loading" and "the caller's load failed" cannot be
 * confused with "the caller passed nothing, fetch it yourself".
 */
export type SubscriptionBadgeSource =
  | { status: "loading" }
  | { status: "error" }
  | { status: "ready"; subscription: Subscription | null };

export function SubscriptionBadge({
  source,
}: {
  source?: SubscriptionBadgeSource;
} = {}) {
  const controlled = source !== undefined;
  const [fetched, setFetched] = useState<Subscription | null>(null);
  const [fetching, setFetching] = useState(!controlled);

  useEffect(() => {
    if (controlled) return;
    let cancelled = false;
    (async () => {
      try {
        const sub = await billingService.getSubscription();
        if (!cancelled) setFetched(sub);
      } catch (error) {
        console.error("Failed to load subscription:", error);
      } finally {
        if (!cancelled) setFetching(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [controlled]);

  const loadingSub = controlled ? source.status === "loading" : fetching;
  const subscription = controlled
    ? source.status === "ready"
      ? source.subscription
      : null
    : fetched;

  if (loadingSub) {
    return (
      <Badge
        variant="outline"
        aria-busy="true"
        aria-label="Loading subscription tier"
        className={cn(
          "flex items-center gap-1.5 px-3 py-1",
          "bg-transparent text-muted-foreground border-dashed border-border"
        )}
      >
        <Loader2 className="h-3.5 w-3.5 animate-spin" />
        <span className="font-medium">&hellip;</span>
      </Badge>
    );
  }

  // Unknown or unavailable tier: say nothing rather than assert a wrong one.
  // An absent subscription is the ordinary error / no-data path and stays
  // silent; a *present* tier we do not recognise means billing shipped a tier
  // this badge has not learned yet, and the badge vanishing for the
  // highest-paying accounts would otherwise look identical to an OSS deploy.
  // `Object.hasOwn` rather than `in` so an inherited key ("constructor",
  // "toString") cannot pass the guard and index into an undefined label.
  if (!subscription?.tier) {
    return null;
  }
  const tier = subscription.tier;
  if (!Object.hasOwn(TIER_LABELS, tier)) {
    console.warn("SubscriptionBadge: unrecognised subscription tier", tier);
    return null;
  }

  // `free` has nothing to be past-due on, so its status is never a discrepancy.
  const statusIsRelevant = tier !== "free";
  const degraded = statusIsRelevant && !isHealthyStatus(subscription.status);
  const cancelling = statusIsRelevant && subscription.cancel_at_period_end;

  const title =
    degraded || cancelling
      ? `Subscription status: ${subscription.status || "unknown"}` +
        (cancelling ? " — cancels at period end" : "")
      : undefined;

  return (
    <Badge
      variant="outline"
      title={title}
      className={cn(
        "flex items-center gap-1.5 px-3 py-1",
        degraded ? NEUTRAL_STYLE : TIER_STYLES[tier]
      )}
    >
      {TIER_ICONS[tier]}
      <span className="font-medium">{TIER_LABELS[tier]}</span>
    </Badge>
  );
}
