const HEYGEN_API_KEY = process.env.HEYGEN_API_KEY;

// TEMP: HeyGen's `streaming.create_token` was sunset at the end of March
// 2026 (migrated to LiveAvatar at api.liveavatar.com). Until we migrate,
// return a placeholder token so the chat UI doesn't 500. The avatar
// itself will fail to start; the chat text flow is unaffected.
const HEYGEN_DISABLED = !HEYGEN_API_KEY || HEYGEN_API_KEY.startsWith("placeholder");

export async function POST() {
  if (HEYGEN_DISABLED) {
    return new Response("placeholder-token", { status: 200 });
  }

  try {
    const res = await fetch(
      "https://api.heygen.com/v1/streaming.create_token",
      {
        method: "POST",
        headers: {
          "x-api-key": HEYGEN_API_KEY as string,
          "Content-Type": "application/json",
        },
      },
    );

    const data = await res.json().catch(() => ({}));
    const token = data?.data?.token;

    if (!res.ok || !token) {
      const detail = data?.error?.message || data?.message || "no token in response";
      console.error("HeyGen token error:", res.status, detail);
      return new Response("placeholder-token", { status: 200 });
    }

    return new Response(token, { status: 200 });
  } catch (error) {
    console.error("Error retrieving access token:", error);
    return new Response("placeholder-token", { status: 200 });
  }
}
