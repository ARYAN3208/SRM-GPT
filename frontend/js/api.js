
const Api = {

  async checkHealth() {
    try {
      const res = await fetch(`${CONFIG.API_BASE_URL}/api/health`);
      return res.ok;
    } catch {
      return false;
    }
  },

  
  async sendMessage(message, sessionId, modelName) {
    const res = await fetch(`${CONFIG.API_BASE_URL}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message,
        session_id: sessionId,
        model_name: modelName
      })
    });

    if (!res.ok) {
      const errBody = await res.json().catch(() => ({}));
      throw new Error(errBody.detail || `Request failed with status ${res.status}`);
    }

    return res.json();
  }

};