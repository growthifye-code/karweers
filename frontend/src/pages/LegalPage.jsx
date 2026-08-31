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
      ["Data we collect", "Contact details you submit (name, email, phone, company), consultation booking details including your selected time slot, consultation enquiry content, and newsletter email. For registered clients we also assign a unique client ID and store your account profile (including profile photo and email if you sign in with Google). We do not take card details or process any payments on this site."],
      ["Activity tracking & personalisation", "When you are signed in as a client and have given consent, we record your on-site activity — pages viewed, services explored, learning videos watched and topics you filter by — and associate it with your account. We use this solely to personalise your experience: to recommend relevant curated videos, surface relevant blogs and insights, and (where enabled) send you a weekly personalised watchlist. We do not use it for third-party advertising and we never sell it. You can withdraw consent at any time via the cookie banner or your dashboard, and you can view or delete this data from your dashboard."],
      ["How we use it", "To respond to enquiries, schedule and confirm consultations, send booking confirmations and calendar invites, personalise your client experience, and (with consent) send our newsletter and weekly learning digest."],
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
    intro: "By accessing this website or requesting a consultation, you agree to these Terms & Conditions.",
    sections: [
      ["Services", "We provide strategic advisory and business coaching. Content on this site (news, blogs, analysis) is for information only and does not constitute financial, legal or investment advice."],
      ["Bookings & confirmation", "Consultations are requested by submitting your details and selecting an available time slot. Bookings are not confirmed automatically — every session is personally reviewed and confirmed by Sudarshan's team, after which you receive a confirmation and a calendar invite. Package prices shown on the site are indicative only; there is no charge to request or confirm a booking, and any fee for a paid engagement (if applicable) will be communicated and agreed in writing before the session."],
      ["Scheduling & rescheduling", "You choose an available slot when you request a booking. Once confirmed, rescheduling is permitted with at least 24 hours' notice, subject to availability; we may also propose an alternative slot, which you are free to accept or decline."],
      ["No-shows", "Please give at least 24 hours' notice if you cannot attend, so the slot can be offered to someone else. Repeated no-shows without notice may limit future priority booking."],
      ["Intellectual property", "All content, frameworks and materials remain the intellectual property of Sudarshan Karweer and may not be reproduced without written permission."],
      ["Limitation of liability", "To the maximum extent permitted by law, our liability arising from the services is limited to the value of the specific engagement."],
      ["Governing law", "These terms are governed by the laws of India, with jurisdiction of the courts of Maharashtra, without prejudice to mandatory consumer protections in your jurisdiction."],
      ["Contact", "Questions? Email " + CONTACT.email + "."],
    ],
  },
  refund: {
    title: "Booking & Cancellation Policy",
    updated: "June 2026",
    intro: "Consultations are requested free of charge and confirmed personally by our team. This policy governs cancellations and rescheduling.",
    sections: [
      ["Cancellation by you", "You can cancel any time before your session at no cost — just let us know so we can free the slot for someone else."],
      ["Rescheduling", "You may reschedule with at least 24 hours' notice, subject to availability. We may also propose a new slot, which you're free to accept or decline."],
      ["No-shows", "Sessions missed without at least 24 hours' notice may limit future priority booking. Please give advance notice wherever possible."],
      ["Cancellation or rescheduling by us", "If we need to cancel or move your session, we'll offer you the next available slot or an alternative time of your choosing."],
      ["Fees", "There is no charge to request or confirm a booking on this site, and we do not process payments here. Should any paid engagement be agreed separately, its terms — including any refunds — will be set out and agreed in writing beforehand."],
      ["How to request", "Email " + CONTACT.email + " with your booking details to cancel or reschedule."],
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
