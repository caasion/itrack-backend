import Fastify from "fastify";
import cors from "@fastify/cors";

import { settings } from "./config/settings.js";
import healthRoutes from "./routes/health.js";
import dwellRoutes from "./routes/dwell.js";
import profileRoutes from "./routes/profile.js";

const app = Fastify({
  logger: settings.DEBUG
    ? {
        transport: {
          target: "pino-pretty",
          options: {
            colorize: true,
            translateTime: "HH:MM:ss",
            ignore: "pid,hostname",
            messageFormat: "{msg}",
          },
        },
      }
    : true,
});

await app.register(cors, { origin: "*" });
await app.register(healthRoutes, { prefix: "/health" });
await app.register(dwellRoutes, { prefix: "/dwell" });
await app.register(profileRoutes, { prefix: "/profile" });

try {
  await app.listen({
    host: settings.HOST,
    port: settings.PORT,
  });

  app.log.info(`iTrack backend running - sourcing: ${settings.PRODUCT_SOURCING_MODE}`);
} catch (error) {
  app.log.error(error, "Failed to start server");
  process.exit(1);
}
