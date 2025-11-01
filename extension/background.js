// background.js
const SERVER = "http://127.0.0.1:8081";
const TIMEOUT_MS = 30000; // 30 seconds for AI model loading

// Helper: POST JSON with timeout
async function postJSON(url, body) {
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), TIMEOUT_MS);
  try {
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      signal: controller.signal,
    });
    clearTimeout(id);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (e) {
    clearTimeout(id);
    throw e;
  }
}

// generate suggestions: ask local server and return 3 variants
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === "generate_suggestions") {
    const { email_text, tone = "professional", length = "medium" } = message;
    
    console.log('🚀 Generating suggestions for:', email_text.substring(0, 50) + '...');
    
    postJSON(`${SERVER}/generate`, { email_text, tone, length })
      .then((j) => {
        console.log('✅ Server response:', j);
        
        const base = j && j.reply ? j.reply.trim() : null;
        if (base) {
          const short = base.split(".").slice(0, 1).join(".") + ".";
          const long = base + " Please let me know if you'd like more details.";
          
          console.log('🤖 AI suggestions generated successfully');
          sendResponse({
            suggestions: [base, short, long],
            from_model: !!j.from_model,
            meta: j.meta || {},
          });
          
          // Auto-cleanup after every 10th generation
          if (Math.random() < 0.1) {
            fetch(`${SERVER}/cleanup_storage`, { method: "POST" }).catch(() => {});
          }
        } else {
          console.warn('❌ No reply in server response');
          sendResponse({ suggestions: null });
        }
      })
      .catch((err) => {
        console.error("❌ Local server error:", err);
        console.error("Error details:", err.message, err.name);
        sendResponse({ suggestions: null });
      });
    return true;
  }

  // Enhanced learning from user interactions
  if (message.action === "learn_interaction") {
    const data = {
      interaction_type: message.interaction_type,
      suggestion: message.suggestion,
      suggestion_index: message.suggestion_index,
      original_email: message.original_email,
      context: message.context,
      feedback: message.feedback
    };
    
    // Send comprehensive learning data to server
    fetch(`${SERVER}/learn_interaction`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    })
      .then((r) => r.json())
      .then((j) => sendResponse({ ok: true, learned: j }))
      .catch((e) => {
        console.warn("learning failed", e);
        sendResponse({ ok: false });
      });
    return true;
  }

  // Legacy remember function (keep for compatibility)
  if (message.action === "remember_inserted") {
    const text = message.text || "";
    if (!text) {
      sendResponse({ ok: false, error: "no text" });
      return true;
    }
    fetch(`${SERVER}/remember`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    })
      .then((r) => r.json())
      .then((j) => sendResponse({ ok: true }))
      .catch((e) => {
        console.warn("remember failed", e);
        sendResponse({ ok: false });
      });
    return true;
  }

  // Model unloading for memory optimization
  if (message.action === "unload_model") {
    fetch(`${SERVER}/unload_model`, { method: "POST" })
      .then((r) => r.json())
      .then((j) => {
        console.log("🤖 AI model unloaded for memory optimization");
        sendResponse({ ok: true, unloaded: true });
      })
      .catch((e) => {
        console.warn("Model unload failed:", e);
        sendResponse({ ok: false, error: String(e) });
      });
    return true;
  }

  // Memory status check
  if (message.action === "memory_status") {
    fetch(`${SERVER}/memory_status`)
      .then((r) => r.json())
      .then((j) => sendResponse({ ok: true, status: j }))
      .catch((e) => sendResponse({ ok: false, error: String(e) }));
    return true;
  }

  // Storage cleanup
  if (message.action === "cleanup_storage") {
    fetch(`${SERVER}/cleanup_storage`, { method: "POST" })
      .then((r) => r.json())
      .then((j) => {
        console.log("🧹 Storage cleanup completed");
        sendResponse({ ok: true, cleaned: j });
      })
      .catch((e) => sendResponse({ ok: false, error: String(e) }));
    return true;
  }



  // Server control - Start server (legacy)
  if (message.action === "start_server") {
    console.log("🚀 Attempting to start AI server...");
    
    // Try to start the server using different methods
    startServerProcess()
      .then(() => {
        console.log("✅ Server started successfully");
        sendResponse({ success: true, message: "Server started" });
      })
      .catch((error) => {
        console.error("❌ Failed to start server:", error);
        sendResponse({ success: false, error: error.message });
      });
    return true;
  }

  // Server control - Stop server
  if (message.action === "stop_server") {
    console.log("🛑 Attempting to stop AI server...");
    
    fetch(`${SERVER}/shutdown`, { method: "POST" })
      .then(() => {
        console.log("✅ Server stopped successfully");
        sendResponse({ success: true, message: "Server stopped" });
      })
      .catch((error) => {
        console.error("❌ Failed to stop server:", error);
        sendResponse({ success: false, error: error.message });
      });
    return true;
  }

  // single reply generation (fallback)
  if (message.action === "generate_reply") {
    const { email_text, tone = "professional", length = "medium" } = message;
    postJSON(`${SERVER}/generate`, { email_text, tone, length })
      .then((j) =>
        sendResponse({ ok: true, reply: j.reply, from_model: !!j.from_model })
      )
      .catch((err) =>
        sendResponse({ ok: false, reply: null, error: String(err) })
      );
    return true;
  }
});



// Server startup function (manual fallback)
async function startServerProcess() {
  try {
    // Method 1: Try to execute the batch file directly
    const response = await chrome.runtime.sendNativeMessage(
      'com.svarx.ai.server',
      { action: 'start' }
    );
    
    if (response && response.success) {
      return Promise.resolve();
    }
  } catch (error) {
    console.log("Native messaging not available, trying alternative methods");
  }

  // Method 2: Try to open the server directory for manual start
  try {
    await chrome.tabs.create({
      url: 'file://' + chrome.runtime.getURL('../ai-engine/start-server.bat'),
      active: false
    });
    
    // Give user instructions
    chrome.notifications.create({
      type: 'basic',
      iconUrl: 'icons/icon-48.png',
      title: 'svarx.ai Server',
      message: 'Please run start-server.bat in the ai-engine folder to start the AI server.'
    });
    
    return Promise.resolve();
  } catch (error) {
    console.error("Could not open server directory:", error);
  }

  // Method 3: Show instructions to user
  chrome.tabs.create({
    url: chrome.runtime.getURL('server-instructions.html')
  });
  
  return Promise.resolve();
}

// Keyboard shortcut handling
chrome.commands.onCommand.addListener((command) => {
  if (command === "open_suggester") {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      if (!tabs || !tabs[0]) return;
      chrome.tabs.sendMessage(tabs[0].id, {
        action: "open_suggester_shortcut",
      });
    });
  }
});
