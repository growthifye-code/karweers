import { useParams, Navigate } from "react-router-dom";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import Seo from "@/components/Seo";
import { CONTACT } from "@/lib/assets";

const DOCS = {
  privacy: {
    title: "Privacy Policy & GDPR",
    updated: "June 2026",
    intro: "This Privacy Policy explains how Sudarshan Karweer (\"we\", \"us\") collects, uses, stores and protects your personal data, in line with the EU General Data Protection Regulation (GDPR), the UK GDPR and India's Digital Personal Data Protection Act.",
    sections: [
      ["Data we collect", "Contact details you submit (name, email, phone, company), consultation enquiry content, newsletter email, and payment metadata processed by our payment provider. We do not store your card details — these are handled entirely by Stripe. For registered clients we also assign a unique client ID and store your account profile (including profile photo and email if you sign in with Google)."],
      ["Activity tracking & personalisation", "When you are signed in as a client and have given consent, we record your on-site activity — pages viewed, services explored, learning videos watched and topics you filter by — and associate it with your account. We use this solely to personalise your experience: to recommend relevant curated videos, surface relevant blogs and insights, and (where enabled) send you a weekly personalised watchlist. We do not use it for third-party advertising and we never sell it. You can withdraw consent at any time via the cookie banner or your dashboard, and you can view or delete this data from your dashboard."],
      ["How we use it", "To respond to enquiries, deliver and schedule consultations, process payments, send booking confirmations, personalise your client experience, and (with consent) send our newsletter and weekly learning digest."],
      ["Legal basis (GDPR)", "We rely on consent (newsletter, analytics/personalisation cookies, activity tracking, weekly digest), contract performance (consultations you book) and legitimate interest (responding to enquiries, securing our services)."],
      ["Your rights", "You have the right to access, rectify, erase, restrict, port and object to processing of your data, and to withdraw consent at any time. Signed-in clients can download a full copy of their data or permanently delete their account and associated activity directly from the dashboard. You may also email " + CONTACT.email + " and we will respond within 30 days."],
      ["Data retention", "We retain enquiry, booking and activity data only as long as necessary for the purpose collected or as required by law, after which it is securely deleted. Deleting your account removes your profile, activity history, tickets and enquiries."],
      ["Security", "Data is transmitted over TLS/HTTPS, protected by bot mitigation (hCaptcha), rate limiting, hardened security headers (HSTS, X-Frame-Options, X-Content-Type-Options), least-privilege access and encrypted storage. Sessions expire automatically after 30 minutes of inactivity."],
      ["Cookies & consent", "We use essential cookies for authentication and preferences. Personalisation/analytics tracking runs only after you accept it in our consent banner; you can decline or change your choice at any time without losing access to the site."],
      ["Contact", "Data controller: Sudarshan Karweer. Email: " + CONTACT.email + "."],
    ],
  },
  terms: {
    title: "Terms & Conditions",
    updated: "June 2026",
    intro: "By accessing this website or booking a consultation, you agree to these Terms & Conditions.",
    sections: [
      ["Services", "We provide strategic advisory and business coaching. Content on this site (news, blogs, analysis) is for information only and does not constitute financial, legal or investment advice."],
      ["Bookings & payment terms", "Consultations are booked and paid in advance via our payment provider (Stripe). Prices are shown per package and are charged in the stated currency. Payment confirms your booking; a session slot and calendar invite follow. Applicable taxes may be added at checkout."],
      ["Scheduling & rescheduling", "After payment you may select an available slot. Rescheduling is permitted with at least 24 hours' notice, subject to availability."],
      ["No-shows", "Sessions missed without at least 24 hours' notice are treated as delivered and are non-refundable."],
      ["Intellectual property", "All content, frameworks and materials remain the intellectual property of Sudarshan Karweer and may not be reproduced without written permission."],
      ["Limitation of liability", "To the maximum extent permitted by law, our liability arising from the services is limited to the fees paid for the specific engagement."],
      ["Governing law", "These terms are governed by the laws of India, with jurisdiction of the courts of Maharashtra, without prejudice to mandatory consumer protections in your jurisdiction."],
      ["Contact", "Questions? Email " + CONTACT.email + "."],
    ],
  },
  refund: {
    title: "Refund & Cancellation Policy",
    updated: "June 2026",
    intro: "We want you to book with confidence. This policy governs refunds and cancellations for paid consultations.",
    sections: [
      ["Cancellation by you", "Cancel at least 48 hours before your scheduled session for a full refund. Cancellations within 48 hours are eligible for a 50% refund or a free reschedule."],
      ["Rescheduling", "You may reschedule once at no cost with at least 24 hours' notice, subject to availability."],
      ["No-shows", "Missed sessions without notice are non-refundable."],
      ["Cancellation by us", "If we must cancel or reschedule, you will be offered a new slot or a full refund at your choice."],
      ["Refund processing", "Approved refunds are issued to the original payment method via Stripe within 5–10 business days. Payment-processor fees may be non-refundable where applicable."],
      ["How to request", "Email " + CONTACT.email + " with your booking details to request a refund or reschedule."],
    ],
  },
};

export default function LegalPage({ doc }) {
  const { docParam } = useParams();
  const key = doc || docParam;
  const content = DOCS[key];
  if (!content) return <Navigate to="/" replace />;

  return (
    <div className="min-h-screen bg-background text-left text-foreground">
      <Seo title={`${content.title} — Sudarshan Karweer`} description={content.intro.slice(0, 150)} />
      <Navbar />
      <div className="mx-auto max-w-3xl px-6 pt-40 lg:pt-48" data-testid={`legal-${key}`}>
        <h1 className="font-display text-4xl font-black tracking-tight sm:text-5xl">{content.title}</h1>
        <p className="mt-3 text-sm text-muted-foreground">Last updated: {content.updated}</p>
        <p className="mt-6 leading-relaxed text-muted-foreground">{content.intro}</p>
        <div className="mt-10 space-y-8">
          {content.sections.map(([h, b]) => (
            <div key={h}>
              <h2 className="font-display text-xl font-bold">{h}</h2>
              <p className="mt-2 leading-relaxed text-muted-foreground">{b}</p>
            </div>
          ))}
        </div>
      </div>
      <div className="py-20" />
      <Footer />
    </div>
  );
}
