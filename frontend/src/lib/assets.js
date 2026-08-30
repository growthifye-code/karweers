// Real + AI-processed portraits of Sudarshan Karweer
const B = "https://customer-assets-lqy194kg.emergentagent.net/job_energy-strategy-hub/artifacts";
const P = "https://static.prod-images.emergentagent.com/jobs/69d54eb7-07e1-4ffd-ad08-8725f9f9829e/images";

// Processed (zoomed, background removed, lime rim-light) — preferred for portraits
export const SK_PORTRAITS = {
  hero: `${P}/e7dd3d48e9a3021442cbca7b6c8a7271f2b5b1a557539cb78d832df66ec15f1d.jpeg`,
  advisory: `${P}/bd94f2abf7366bbbe2e23723fa5725b3fb652f107d8d234a36a161ba893e1ce0.jpeg`,
  coaching: `${P}/69527640e2347ebe65186632fedd966713737be8a6139a15317412085acd99a5.jpeg`,
};

// Original photos (used sparingly, non-portrait contexts / about page)
export const SK_PHOTOS = {
  heroPortrait: SK_PORTRAITS.hero,
  aboutWide: `${B}/dst68mam_DSC05686.webp`,
  walking: `${B}/l6ah83fp_DSC05555.webp`,
  armsCrossed: SK_PORTRAITS.advisory,
  seated: `${B}/w5bxm4fe_DSC05702.webp`,
};

export const CONTACT = {
  email: "sudarshan@karweers.com",
  phone: "+91 72089 98944",
  phoneRaw: "+917208998944",
  whatsapp: "917208998944",
};
