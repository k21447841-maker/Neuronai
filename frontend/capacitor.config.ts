import type { CapacitorConfig } from "@capacitor/cli";

const config: CapacitorConfig = {
  appId: "com.neuroflow.ai",
  appName: "NEUROFLOW AI",
  webDir: "dist",
  server: {
    androidScheme: "https"
  },
  plugins: {
    CapacitorHttp: {
      enabled: true
    }
  }
};

export default config;
