// FigRecipe chat adapter — posts chat messages to scitex-app's chat endpoint.
// Extracted from main.tsx to keep the bootstrap orchestrator under the line
// limit; main.tsx imports `figrecipeChatAdapter` and wires it into ChatMode.

import type { ChatAdapter } from "@scitex/ui/src/scitex_ui/static/scitex_ui/ts/shell/chat";

export const FIGRECIPE_SYSTEM =
  "You are a helpful AI assistant in the FigRecipe figure editor. " +
  "Help with YAML recipes, matplotlib plots, and figure composition.";

export const figrecipeChatAdapter: ChatAdapter = {
  async streamChat(message, _context, images) {
    return fetch("api/chat/stream", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        prompt: message,
        history: [],
        system_prompt: FIGRECIPE_SYSTEM,
        ...(images?.length
          ? {
              images: images.map((b64) => `data:image/png;base64,${b64}`),
            }
          : {}),
      }),
    });
  },
};
