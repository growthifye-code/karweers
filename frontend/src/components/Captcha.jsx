import { forwardRef } from "react";
import HCaptcha from "@hcaptcha/react-hcaptcha";
import { getHcaptchaSitekey } from "@/config";

// hCaptcha's official always-pass TEST sitekey (works on ANY hostname, never challenges).
const TEST_SITEKEY = "10000000-ffff-ffff-ffff-000000000001";

// The real sitekey is hostname-locked to production in the hCaptcha dashboard, so it
// cannot complete a challenge on the ephemeral preview domain. Select by EXACT hostname:
// real key only on production; the always-pass test key everywhere else (preview/localhost).
// The backend already auto-passes captcha on preview hosts, so the test token is accepted
// on preview and full siteverify runs only on production. The production sitekey is served
// by the backend (/api/public-config → getHcaptchaSitekey) so it can be rotated via .env.
const PRODUCTION_HOSTNAMES = new Set(["sudarshankarweer.com", "www.sudarshankarweer.com"]);

function pickSitekey() {
  // Diagnostic override: force the real sitekey everywhere (used to validate a real key
  // pair on the preview domain before deploying). Requires the preview host to be added to
  // the hCaptcha site's allowed hostnames.
  if (process.env.REACT_APP_CAPTCHA_FORCE_REAL === "1") {
    return getHcaptchaSitekey() || TEST_SITEKEY;
  }
  const host = (typeof window !== "undefined" ? window.location.hostname : "").toLowerCase();
  if (PRODUCTION_HOSTNAMES.has(host)) {
    return getHcaptchaSitekey() || TEST_SITEKEY;
  }
  return TEST_SITEKEY;
}

const SITEKEY = pickSitekey();

const Captcha = forwardRef(function Captcha({ onVerify, onExpire }, ref) {
  return (
    <div data-testid="hcaptcha" className="my-2">
      <HCaptcha
        key={SITEKEY}
        ref={ref}
        sitekey={SITEKEY}
        theme="dark"
        reCaptchaCompat={false}
        onVerify={onVerify}
        onExpire={() => onExpire && onExpire()}
        onError={(e) => { console.error("hCaptcha error", e); }}
      />
    </div>
  );
});

export default Captcha;
