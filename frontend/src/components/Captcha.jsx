import { forwardRef } from "react";
import HCaptcha from "@hcaptcha/react-hcaptcha";

// Real hCaptcha sitekey (from env). Falls back to hCaptcha's always-pass TEST key
// only if no sitekey is configured.
const TEST_SITEKEY = "10000000-ffff-ffff-ffff-000000000001";
const SITEKEY = process.env.REACT_APP_HCAPTCHA_SITEKEY || TEST_SITEKEY;

const Captcha = forwardRef(function Captcha({ onVerify, onExpire }, ref) {
  return (
    <div data-testid="hcaptcha" className="my-2">
      <HCaptcha
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
