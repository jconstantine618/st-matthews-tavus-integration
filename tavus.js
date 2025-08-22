// api/tavus.js
import fetch from "node-fetch";

export default async function handler(req, res) {
  try {
    // Your Tavus API Key (store as environment variable!)
    const API_KEY = process.env.TAVUS_API_KEY;

    // Call Tavus API to create a new conversation
    const response = await fetch("https://api.tavus.io/v2/conversations", {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${API_KEY}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        // Replace with your replica/persona IDs
        replica_id: "your_replica_id",
        persona_id: "your_persona_id",
      }),
    });

    const data = await response.json();

    if (!data.conversation_url) {
      throw new Error("No conversation_url returned");
    }

    res.status(200).json({ url: data.conversation_url });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: "Failed to create Tavus session" });
  }
}
