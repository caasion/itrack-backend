import { settings } from "../config/settings.js";
import * as backboardService from "../services/backboardService.js";
const healthRoutes = async (fastify) => {
    fastify.get("/", async () => {
        const response = {
            status: "ok",
            sourcing_mode: settings.PRODUCT_SOURCING_MODE,
            timestamp: new Date().toISOString(),
        };
        const anonDebugDwellCount = backboardService.getDwellCount("anon-debug");
        if (anonDebugDwellCount > 0) {
            response.dwell_count = anonDebugDwellCount;
        }
        return response;
    });
};
export default healthRoutes;
