import { useParams, Navigate } from "react-router-dom";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import Seo from "@/components/Seo";
import { CONTACT } from "@/lib/assets";

export const DOCS = {
  privacy: {
    title: "Privacy Policy & GDPR",
    updated: "June 2026",
    intro: "This Privacy Policy explains how Sudarshan Karweer (\"we\", \"us\") collects, uses, stores and protects your personal data, in line with the EU General Data Protection Regulation (GDPR), the UK GDPR and India's Digital Personal Data Protection Act.",
    sections: [
      ["Data we collect", "Contact details you submit (name, email, phone, company), consultation booking details including your selected time slot, consultation enquiry content, and newsletter email. For registered clients we also assign a unique client ID and store your account profile (including profile photo and email if you sign in with Google). When you pay for a consultation, payment is processed by our payment gateway, Razorpay. We do NOT collect or store your full card, UPI or bank details on this site — these are handled directly and securely by Razorpay. We store only the payment reference data returned to us (Razorpay order ID, payment ID, amount, GST, currency, status and, where applicable, refund ID)."],
      ["Activity tracking & personalisation", "When you are signed in as a client and have given consent, we record your on-site activity — pages viewed, services explored, learning videos watched and topics you filter by — and associate it with your account. We use this solely to personalise your experience: to recommend relevant curated videos, surface relevant blogs and insights, and (where enabled) send you a weekly personalised watchlist. We do not use it for third-party advertising and we never sell it. You can withdraw consent at any time via the cookie banner or your dashboard, and you can view or delete this data from your dashboard."],
      ["How we use it", "To respond to enquiries, take and verify consultation payments, schedule and confirm consultations, issue payment receipts and refunds, send booking confirmations and calendar invites, personalise your client experience, and (with consent) send our newsletter and weekly learning digest."],
      ["Payments (Razorpay)", "Paid consultations are processed by Razorpay Software Pvt. Ltd., a PCI-DSS compliant payment gateway. When you check out, your payment information is transmitted directly to Razorpay under their Terms and Privacy Policy (razorpay.com). We receive only a confirmation and payment reference. Razorpay may set its own cookies on the checkout window to process the transaction and prevent fraud."],
      ["Legal basis (GDPR)", "We rely on consent (newsletter, analytics/personalisation cookies, activity tracking, weekly digest), contract performance (consultations you book and pay for, and processing any refund) and legitimate interest (responding to enquiries, securing our services, fraud prevention)."],
      ["Your rights", "You have the right to access, rectify, erase, restrict, port and object to processing of your data, and to withdraw consent at any time. Signed-in clients can download a full copy of their data or permanently delete their account and associated activity directly from the dashboard. You may also email " + CONTACT.email + " and we will respond within 30 days."],
      ["Data retention", "We retain enquiry, booking and activity data only as long as necessary for the purpose collected or as required by law, after which it is securely deleted. Deleting your account removes your profile, activity history, tickets and enquiries."],
      ["Security", "Data is transmitted over TLS/HTTPS, protected by bot mitigation (Google reCAPTCHA), rate limiting, hardened security headers (HSTS, X-Frame-Options, X-Content-Type-Options), least-privilege access and encrypted storage. Sessions expire automatically after 30 minutes of inactivity."],
      ["Cookies & consent", "We use essential cookies for authentication and preferences, and our payment gateway (Razorpay) sets cookies on its secure checkout to process payments and prevent fraud. Personalisation/analytics tracking runs only after you accept it in our consent banner; you can decline or change your choice at any time without losing access to the site."],
      ["Contact", "Data controller: Sudarshan Karweer. Email: " + CONTACT.email + "."],
    ],
  },
  terms: {
    title: "Terms & Conditions",
    updated: "June 2026",
    intro: "By accessing this website or requesting a consultation, you agree to these Terms & Conditions.",
    sections: [
      ["Services", "We provide strategic advisory and business coaching. Content on this site (news, blogs, analysis) is for information only and does not constitute financial, legal or investment advice."],
      ["Bookings, fees & payment", "Consultations are booked by selecting an available time slot and paying the applicable fee online via our payment gateway, Razorpay. Fees are: Discovery Call (30 min) \u20b912,000; 1:1 Strategy Session (60 min) \u20b950,000; Deep-Dive Advisory (90 min) \u20b91,20,000. All fees are in Indian Rupees (INR) and are inclusive of 18% GST. A slot is reserved on successful payment and then personally reviewed and confirmed by Sudarshan's team, after which you receive a confirmation and calendar invite. If a paid session cannot be accommodated or is declined, your payment is refunded in full (see our Booking & Cancellation Policy)."],
      ["Scheduling & rescheduling", "You choose an available slot when you request a booking. Once confirmed, rescheduling is permitted with at least 24 hours' notice, subject to availability; we may also propose an alternative slot, which you are free to accept or decline."],
      ["No-shows", "Please give at least 24 hours' notice if you cannot attend, so the slot can be offered to someone else. Repeated no-shows without notice may limit future priority booking."],
      ["Intellectual property", "All content, frameworks and materials remain the intellectual property of Sudarshan Karweer and may not be reproduced without written permission."],
      ["Limitation of liability", "To the maximum extent permitted by law, our liability arising from the services is limited to the value of the specific engagement."],
      ["Governing law", "These terms are governed by the laws of India, with jurisdiction of the courts of Maharashtra, without prejudice to mandatory consumer protections in your jurisdiction."],
      ["Contact", "Questions? Email " + CONTACT.email + "."],
    ],
  },
  refund: {
    title: "Booking, Payment & Refund Policy",
    updated: "June 2026",
    intro: "Consultations are booked and paid for online via Razorpay, then confirmed personally by our team. This policy governs payments, cancellations, rescheduling and refunds.",
    sections: [
      ["Fees & GST", "Consultation fees are: Discovery Call \u20b912,000, 1:1 Strategy Session \u20b950,000 and Deep-Dive Advisory \u20b91,20,000 — all in INR and inclusive of 18% GST. Payment is taken securely via Razorpay at the time of booking."],
      ["Refund if not confirmed", "Your slot is reserved on payment and then confirmed by our team. If we cannot accommodate or confirm your session, or if you do not wish to proceed with the offered slot, we refund your payment in full. Refunds are issued through Razorpay to your original payment method/account and typically appear within 5–7 business days."],
      ["Cancellation by you", "You may cancel before your session; if you cancel a paid booking that has not yet taken place, we refund it in full to your original payment method (online cancellations are not available within 24 hours of a confirmed session — contact us and we'll help)."],
      ["Rescheduling", "You may reschedule with at least 24 hours' notice, subject to availability, at no extra charge. We may also propose a new slot, which you're free to accept (no charge) or decline (full refund)."],
      ["No-shows", "Sessions missed without at least 24 hours' notice are non-refundable and may limit future priority booking. Please give advance notice wherever possible."],
      ["Cancellation or rescheduling by us", "If we need to cancel or move your session and cannot offer a suitable alternative, you receive a full refund to your original payment method."],
      ["How to request", "Use the cancel/reschedule link in your booking email, or email " + CONTACT.email + " with your booking details."],
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
