import * as backboardService from "../services/backboardService.js";
const profileRoutes = async (fastify) => {
    fastify.get("/:userId", async (request) => {
        const { userId } = request.params;
        const profile = await backboardService.getProfile(userId);
        const dwellEventCount = backboardService.getDwellCount(userId);
        const response = {
            user_id: userId,
            profile,
            dwell_event_count: dwellEventCount,
        };
        return response;
    });
    fastify.delete("/:userId", async (request) => {
        const { userId } = request.params;
        backboardService.clearProfile(userId);
        return { deleted: true, user_id: userId };
    });
};
export default profileRoutes;
