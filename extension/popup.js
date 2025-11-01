const SERVER_HEALTH = "http://127.0.0.1:8081/health";
const DEFAULT_PREFS = {
  tone: "professional",
  length: "medium",
  personalize: true,
};

function savePrefs() {
  const tone = document.getElementById("tone").value;
  const length = document.getElementById("length").value;
  const personalize = document.getElementById("personalize").checked;
  chrome.storage.sync.set({ tone, length, personalize });
  
  // Auto-optimize storage when saving
  fetch("http://127.0.0.1:8081/cleanup_storage", { method: "POST" }).catch(() => {});
}

// Load saved preferences
chrome.storage.sync.get(DEFAULT_PREFS, (prefs) => {
  document.getElementById("tone").value = prefs.tone || DEFAULT_PREFS.tone;
  document.getElementById("length").value = prefs.length || DEFAULT_PREFS.length;
  document.getElementById("personalize").checked = prefs.personalize !== false;
});

// Auto-save when any setting changes
document.getElementById("tone").addEventListener("change", savePrefs);
document.getElementById("length").addEventListener("change", savePrefs);
document.getElementById("personalize").addEventListener("change", savePrefs);

// Enhanced status check with memory monitoring
async function checkStatus() {
  const status = document.getElementById("status");
  
  try {
    // Check basic health
    const healthRes = await fetch(SERVER_HEALTH);
    const health = await healthRes.json();
    
    // Get memory status
    const memoryRes = await fetch("http://127.0.0.1:8081/memory_status");
    const memory = await memoryRes.json();
    
    if (health.ok && health.has_model) {
      status.className = "status success";
      
      if (memory.model_loaded) {
        const unloadTime = Math.round(memory.will_unload_in);
        status.textContent = `Active (${memory.memory_mb}MB) - Auto-unload in ${unloadTime}s`;
      } else {
        status.textContent = `Ready (${memory.memory_mb}MB) - Model will load on-demand`;
      }
    } else {
      status.className = "status error";
      status.textContent = "Service unavailable";
    }
  } catch (e) {
    status.className = "status error";
    status.textContent = "Offline";
  }
}





// Server control functionality
let serverProcess = null;
let isServerRunning = false;

let isCheckingStatus = false;

async function checkServerStatus() {
  if (isCheckingStatus) return; // Prevent multiple simultaneous checks
  isCheckingStatus = true;
  
  const toggle = document.getElementById("serverToggle");
  const status = document.getElementById("serverStatus");
  
  console.log("Checking server status...");
  
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 3000);
    
    const response = await fetch(SERVER_HEALTH, { 
      signal: controller.signal,
      cache: 'no-cache'
    });
    
    clearTimeout(timeoutId);
    
    if (response.ok) {
      const health = await response.json();
      
      if (health.ok) {
        // Server is running
        console.log("Server is running");
        const wasRunning = isServerRunning;
        isServerRunning = true;
        
        // Only update UI if state actually changed
        if (!wasRunning) {
          toggle.classList.add("active");
          status.textContent = "✅ Server running - AI suggestions enabled";
          status.style.color = "#10b981";
        }
        isCheckingStatus = false;
        return;
      }
    }
    
    throw new Error("Server not healthy");
    
  } catch (error) {
    // Server is not running
    console.log("Server is offline:", error.message);
    const wasRunning = isServerRunning;
    isServerRunning = false;
    
    // Only update UI if state actually changed
    if (wasRunning) {
      toggle.classList.remove("active");
      status.textContent = "❌ Server offline - Using basic suggestions";
      status.style.color = "#dc2626";
    }
  }
  
  isCheckingStatus = false;
}

async function startServer() {
  const status = document.getElementById("serverStatus");
  
  status.textContent = "🔄 Please run svarx-ai-server.exe";
  status.style.color = "#2563eb";
  
  // Monitor for server to come online
  monitorServerStartup();
}

function monitorServerStartup() {
  const status = document.getElementById("serverStatus");
  const toggle = document.getElementById("serverToggle");
  
  let attempts = 0;
  const checkInterval = setInterval(async () => {
    attempts++;
    
    try {
      const response = await fetch(SERVER_HEALTH, { 
        signal: AbortSignal.timeout(2000),
        cache: 'no-cache'
      });
      const health = await response.json();
      
      if (health.ok) {
        clearInterval(checkInterval);
        isServerRunning = true;
        toggle.classList.add("active");
        status.textContent = "✅ Server running - AI suggestions enabled";
        status.style.color = "#10b981";
        return;
      }
    } catch (e) {
      // Server still not running
    }
    
    // Update status with countdown
    const remaining = Math.max(0, 30 - attempts);
    if (remaining > 0) {
      status.textContent = `🔄 Looking for server... (${remaining}s)`;
    } else {
      status.textContent = "❌ Server not found. Run svarx-ai-server.exe";
      status.style.color = "#dc2626";
    }
    
    if (attempts >= 30) { // Stop checking after 30 seconds
      clearInterval(checkInterval);
    }
  }, 1000);
}



async function stopServer() {
  const status = document.getElementById("serverStatus");
  const toggle = document.getElementById("serverToggle");
  
  try {
    status.textContent = "🔄 Stopping server...";
    status.style.color = "#2563eb";
    
    // Try multiple shutdown methods
    try {
      // Method 1: Try shutdown endpoint
      await fetch("http://127.0.0.1:8081/shutdown", { 
        method: "POST",
        signal: AbortSignal.timeout(3000)
      });
    } catch (e) {
      console.log("Shutdown endpoint failed, trying alternative methods");
      
      // Method 2: Try a different endpoint that might exist
      try {
        await fetch("http://127.0.0.1:8081/stop", { 
          method: "POST",
          signal: AbortSignal.timeout(3000)
        });
      } catch (e2) {
        console.log("Alternative shutdown failed, server might be stopped");
      }
    }
    
    // Update state immediately
    isServerRunning = false;
    toggle.classList.remove("active");
    status.textContent = "❌ Server offline - Using basic suggestions";
    status.style.color = "#dc2626";
    
    // Verify server is actually stopped after a moment
    setTimeout(() => {
      checkServerStatus();
    }, 2000);
    
  } catch (error) {
    console.log("Server stop error:", error);
    // Assume it worked and update UI
    isServerRunning = false;
    toggle.classList.remove("active");
    status.textContent = "❌ Server offline - Using basic suggestions";
    status.style.color = "#dc2626";
  }
}

// Manual toggle function
function toggleServer() {
  const toggle = document.getElementById("serverToggle");
  const status = document.getElementById("serverStatus");
  
  console.log("Manual toggle, current state:", isServerRunning);
  
  if (isServerRunning) {
    console.log("User wants to stop server");
    stopServer();
  } else {
    console.log("User wants to start server");
    startServer();
  }
}

// Event listener for server toggle switch
document.getElementById("serverToggle").addEventListener("click", (e) => {
  e.preventDefault();
  e.stopPropagation();
  toggleServer();
});

// Check status on load and refresh every 5 seconds
checkStatus();
checkServerStatus();
setInterval(() => {
  checkStatus();
  checkServerStatus();
}, 5000);