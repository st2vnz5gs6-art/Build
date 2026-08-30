import Link from "next/link";

export const metadata = { title: "Privacy policy — Coupon" };

export default function PrivacyPage() {
  return (
    <div className="mx-auto max-w-lg px-4 pb-16 pt-8 safe-top safe-bottom">
      <Link href="/" className="text-sm text-ink-400">
        ← Back
      </Link>
      <h1 className="mb-1 mt-4 font-display text-3xl uppercase tracking-wide text-ink-100">Privacy policy</h1>
      <p className="mb-8 text-xs text-ink-500">Last updated {new Date().toISOString().slice(0, 10)}</p>

      <div className="space-y-6 text-sm leading-relaxed text-ink-300">
        <section>
          <h2 className="mb-1.5 text-base font-semibold text-ink-100">What Coupon is</h2>
          <p>
            Coupon is a private, group-based app for tracking football coupons in units, for fun. No real money
            changes hands anywhere in the product — there are no wallets, stakes, deposits or payouts. Coupon is
            not a gambling product and is not licensed as one.
          </p>
        </section>

        <section>
          <h2 className="mb-1.5 text-base font-semibold text-ink-100">What we collect</h2>
          <p>There are no user accounts. To use Coupon, you enter a group code and pick a display name. That gives us:</p>
          <ul className="mt-2 list-disc space-y-1 pl-5">
            <li>The display name you choose (this can be anything — it doesn&apos;t have to be your real name).</li>
            <li>The coupons, comments and copy (&quot;pile-on&quot;) actions you post, which are visible to your group.</li>
            <li>A random identifier stored in your browser&apos;s local storage that links your device to your display name within a group.</li>
            <li>Standard technical logs from our hosting provider (IP address, request timing) kept only for security and abuse prevention.</li>
          </ul>
        </section>

        <section>
          <h2 className="mb-1.5 text-base font-semibold text-ink-100">What we don&apos;t collect</h2>
          <p>No email address, no phone number, no payment details, no real-money transaction data — we don&apos;t ask for any of it.</p>
        </section>

        <section>
          <h2 className="mb-1.5 text-base font-semibold text-ink-100">Where it&apos;s stored</h2>
          <p>
            Coupon data is stored with Supabase (Postgres hosting) and this app is hosted on Vercel. Both may
            process data outside the UK/EEA under standard contractual safeguards. Your member identifier lives
            only in your browser&apos;s local storage — clearing your browser data or switching devices means
            starting again as a &quot;new&quot; member.
          </p>
        </section>

        <section>
          <h2 className="mb-1.5 text-base font-semibold text-ink-100">Who can see what</h2>
          <p>
            Everything you post is visible to everyone else in that group, indefinitely (coupons can&apos;t be
            edited or deleted once posted — that&apos;s the point). Nothing is public or searchable outside a
            group unless you deliberately share a coupon or join link.
          </p>
        </section>

        <section>
          <h2 className="mb-1.5 text-base font-semibold text-ink-100">Your rights (UK GDPR)</h2>
          <p>
            You can ask us what data we hold linked to your display name, ask us to correct it, or ask us to
            delete it, by contacting whoever runs your group&apos;s Coupon deployment. Because there&apos;s no
            account system, we can only act on requests we can reasonably verify belong to a given member.
          </p>
        </section>

        <section>
          <h2 className="mb-1.5 text-base font-semibold text-ink-100">Age restriction</h2>
          <p>Coupon deals with football betting content and requires you to confirm you&apos;re 18 or over before use.</p>
        </section>

        <section>
          <h2 className="mb-1.5 text-base font-semibold text-ink-100">Changes</h2>
          <p>We&apos;ll update this page if what we collect or how we use it changes.</p>
        </section>
      </div>
    </div>
  );
}
