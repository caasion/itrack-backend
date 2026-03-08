import { DwellEventSchema } from "../models/schemas.js";
import * as backboardService from "../services/backboardService.js";
import * as cloudinaryService from "../services/cloudinaryService.js";
import * as geminiService from "../services/geminiService.js";
import * as sourcingService from "../services/sourcingService.js";
const dwellRoutes = async (fastify) => {
    fastify.post("/", async (request, reply) => {
        const event = DwellEventSchema.parse(request.body);
        fastify.log.info(`[Pipeline] Received dwell: user=${event.user_id} duration=${event.dwell_duration_ms}`);
        fastify.log.info("[Pipeline] Fetching current profile for Cat2 input");
        const currentProfile = await backboardService.getProfile(event.user_id);
        fastify.log.info("[Pipeline] Running Cat1, Cat2, and Gemini concurrently");
        const cat1Task = sourcingService.sourceCat1(event.screenshot_b64);
        const cat2Task = sourcingService.sourceCat2(currentProfile).catch((error) => {
            fastify.log.warn({ error }, "[Pipeline] Cat2 sourcing failed, using empty picks");
            return [];
        });
        const geminiTask = geminiService
            .identifyAndUpdate(event.screenshot_b64, event.user_id, event.page_url, event.page_title)
            .catch((error) => {
            fastify.log.warn({ error }, "[Pipeline] Gemini identify/update failed");
        });
        let cat1Product;
        let cat2Picks;
        try {
            [cat1Product, cat2Picks] = await Promise.all([cat1Task, cat2Task, geminiTask]).then(([cat1, cat2, _gemini]) => [cat1, cat2]);
        }
        catch (error) {
            fastify.log.error({ error }, "[Pipeline] Cat1 sourcing failed");
            return reply.code(502).send({ message: "Cat1 sourcing failed" });
        }
        fastify.log.info("[Pipeline] Transforming product images in parallel");
        const allProducts = [cat1Product, ...cat2Picks];
        const urls = await Promise.all(allProducts.map((product) => cloudinaryService.transformProductImage(product.image_url)));
        allProducts.forEach((product, index) => {
            product.image_url = urls[index];
        });
        fastify.log.info("[Pipeline] Re-fetching profile after Gemini update");
        const updatedProfile = await backboardService.getProfile(event.user_id);
        return {
            current_product: cat1Product,
            taste_picks: cat2Picks,
            profile_snapshot: {
                ...updatedProfile,
                dwell_count: backboardService.getDwellCount(event.user_id),
            },
        };
    });
};
export default dwellRoutes;
