import { forwardRef } from "react";
import HCaptcha from "@hcaptcha/react-hcaptcha";

const SITEKEY = process.env.REACT_APP_HCAPTCHA_SITEKEY || "10000000-ffff-ffff-ffff-000000000001";

const Captcha = forwardRef(function Captcha({ onVerify, onExpire }, ref) {
  return (
    <div data-testid="hcaptcha" className="my-2">
      <HCaptcha
        ref={ref}
        sitekey={SITEKEY}
        theme="dark"
        onVerify={onVerify}
        onExpire={() => onExpire && onExpire()}
      />
    </div>
  );
});

export default Captcha;
