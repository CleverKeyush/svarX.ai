// svarx.ai - Universal AI Assistant - Error-Free Version
(function() {
  'use strict';
  
  console.log('🚀 svarx.ai starting on:', window.location.hostname);
  
  // Configuration
  var CONFIG = {
    buttonClass: 'svarx-ai-btn',
    panelClass: 'svarx-suggestion-panel',
    createdAttr: 'data-svarx-created',
    idleTimeout: 60000 // 1 minute in milliseconds
  };
  
  // Memory management variables
  var isActive = true;
  var lastActivity = Date.now();
  var scanInterval = null;
  var observer = null;
  var idleTimer = null;
  
  // Textbox selectors for all platforms
  var SELECTORS = [
    'div[role="textbox"][contenteditable="true"]',
    'div[contenteditable="true"]',
    '[contenteditable="true"]',
    'textarea',
    '.msg-form__contenteditable',
    '.ql-editor',
    'div[data-qa="message_input"]'
  ];
  
  // Professional color scheme
  var COLORS = {
    buttonBg: '#ffffff',
    buttonBorder: '#1a73e8',
    buttonText: '#1a73e8',
    panelBg: '#ffffff',
    panelBorder: '#e1e5e9',
    panelShadow: '0 8px 32px rgba(0, 0, 0, 0.12)',
    headerBg: '#f8fafc',
    headerBorder: '#e1e5e9',
    headerText: '#1e293b',
    suggestionBg: '#ffffff',
    suggestionHover: '#f1f5f9',
    suggestionText: '#334155',
    suggestionBorder: '#f1f5f9',
    copyButtonBg: '#ffffff',
    copyButtonBorder: '#d1d5db',
    copyButtonText: '#374151',
    copyButtonHover: '#f3f4f6',
    accent: '#1a73e8',
    success: '#10b981',
    textSecondary: '#64748b'
  };
  
  // Create button
  function createButton() {
    var button = document.createElement('button');
    button.className = CONFIG.buttonClass;
    button.title = 'svarx.ai';
    button.textContent = 'AI';
    
    button.style.cssText = 
      'position: absolute !important;' +
      'top: 8px !important;' +
      'right: 8px !important;' +
      'width: 32px !important;' +
      'height: 32px !important;' +
      'border-radius: 50% !important;' +
      'border: 2px solid ' + COLORS.buttonBorder + ' !important;' +
      'background: ' + COLORS.buttonBg + ' !important;' +
      'color: ' + COLORS.buttonText + ' !important;' +
      'cursor: pointer !important;' +
      'z-index: 999999 !important;' +
      'display: flex !important;' +
      'align-items: center !important;' +
      'justify-content: center !important;' +
      'font-size: 12px !important;' +
      'font-weight: bold !important;';
    
    return button;
  }
  
  // Create professional panel
  function createPanel() {
    var panel = document.createElement('div');
    panel.className = CONFIG.panelClass;
    
    panel.style.cssText = 
      'position: absolute !important;' +
      'top: 42px !important;' +
      'left: 0 !important;' +
      'right: 0 !important;' +
      'background: ' + COLORS.panelBg + ' !important;' +
      'border: 1px solid ' + COLORS.panelBorder + ' !important;' +
      'border-radius: 12px !important;' +
      'box-shadow: ' + COLORS.panelShadow + ' !important;' +
      'z-index: 999998 !important;' +
      'display: none !important;' +
      'max-height: 400px !important;' +
      'overflow: hidden !important;' +
      'min-width: 380px !important;' +
      'max-width: 500px !important;' +
      'font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif !important;' +
      'backdrop-filter: blur(10px) !important;' +
      'animation: slideIn 0.2s ease-out !important;';
    
    return panel;
  }
  
  // Insert text
  function insertText(textbox, text) {
    console.log('📝 Inserting text:', text);
    
    try {
      // Always copy to clipboard first (most reliable)
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(function() {
          showNotification('✅ Copied! Press Ctrl+V to paste');
        }).catch(function() {
          fallbackCopy(text);
        });
      } else {
        fallbackCopy(text);
      }
      
      // Also try direct insertion
      textbox.focus();
      
      if (textbox.contentEditable === 'true') {
        textbox.textContent = text;
        textbox.dispatchEvent(new Event('input', { bubbles: true }));
      } else if (textbox.tagName === 'TEXTAREA') {
        textbox.value = text;
        textbox.dispatchEvent(new Event('input', { bubbles: true }));
      }
      
    } catch (error) {
      console.log('Insert error:', error);
      fallbackCopy(text);
    }
  }
  
  // Fallback copy method (modern approach)
  function fallbackCopy(text) {
    try {
      // Try modern clipboard API first
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(function() {
          showNotification('✅ Copied! Press Ctrl+V to paste');
        }).catch(function() {
          // If clipboard fails, show alert
          alert('svarx.ai suggestion:\n\n' + text);
        });
      } else {
        // Show alert as final fallback
        alert('svarx.ai suggestion:\n\n' + text);
      }
    } catch (e) {
      alert('svarx.ai suggestion:\n\n' + text);
    }
  }
  
  // Show notification
  function showNotification(message) {
    var notification = document.createElement('div');
    notification.style.cssText = 
      'position: fixed !important;' +
      'top: 20px !important;' +
      'right: 20px !important;' +
      'background: #4CAF50 !important;' +
      'color: white !important;' +
      'padding: 10px 15px !important;' +
      'border-radius: 5px !important;' +
      'z-index: 9999999 !important;' +
      'font-size: 14px !important;';
    
    notification.textContent = message;
    document.body.appendChild(notification);
    
    setTimeout(function() {
      if (notification.parentNode) {
        notification.parentNode.removeChild(notification);
      }
    }, 3000);
  }
  
  // Get suggestions
  function getSuggestions(callback) {
    if (typeof chrome !== 'undefined' && chrome.runtime && chrome.runtime.sendMessage) {
      chrome.runtime.sendMessage({
        action: 'generate_suggestions',
        email_text: 'Hello',
        tone: 'professional',
        length: 'medium'
      }, function(response) {
        if (chrome.runtime.lastError) {
          console.log('Runtime error:', chrome.runtime.lastError);
          callback(getFallbackSuggestions());
          return;
        }
        
        if (response && response.suggestions && response.suggestions.length > 0) {
          callback(response.suggestions);
        } else {
          callback(getFallbackSuggestions());
        }
      });
    } else {
      callback(getFallbackSuggestions());
    }
  }
  
  // Fallback suggestions
  function getFallbackSuggestions() {
    return [
      "Thank you for your message. I'll get back to you shortly.",
      "I appreciate you reaching out. Let me respond soon.",
      "Thanks for the update. I'll take care of this."
    ];
  }
  
  // Copy text to clipboard only
  function copyToClipboard(text) {
    try {
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(function() {
          showNotification('📋 Copied to clipboard!');
        }).catch(function() {
          fallbackCopy(text);
        });
      } else {
        fallbackCopy(text);
      }
    } catch (error) {
      fallbackCopy(text);
    }
  }
  
  // Setup suggestion events (separate function to avoid closure issues)
  function setupSuggestionEvents(container, textElement, btnElement, suggestion, textbox, panel) {
    // Professional hover effects for suggestion container
    container.addEventListener('mouseenter', function() {
      container.style.backgroundColor = COLORS.suggestionHover;
      container.style.transform = 'translateY(-1px)';
      container.style.boxShadow = '0 2px 8px rgba(0, 0, 0, 0.08)';
    });
    
    container.addEventListener('mouseleave', function() {
      container.style.backgroundColor = COLORS.suggestionBg;
      container.style.transform = 'translateY(0)';
      container.style.boxShadow = 'none';
    });
    
    // Click to insert text
    textElement.addEventListener('click', function(e) {
      e.stopPropagation();
      trackActivity();
      insertText(textbox, suggestion);
      panel.style.display = 'none';
    });
    
    // Modern copy button hover effects
    btnElement.addEventListener('mouseenter', function() {
      btnElement.style.backgroundColor = COLORS.copyButtonHover;
      btnElement.style.borderColor = COLORS.accent;
      btnElement.style.color = COLORS.accent;
      btnElement.style.transform = 'translateY(-1px)';
      btnElement.style.boxShadow = '0 2px 8px rgba(26, 115, 232, 0.15)';
    });
    
    btnElement.addEventListener('mouseleave', function() {
      btnElement.style.backgroundColor = COLORS.copyButtonBg;
      btnElement.style.borderColor = COLORS.copyButtonBorder;
      btnElement.style.color = COLORS.copyButtonText;
      btnElement.style.transform = 'translateY(0)';
      btnElement.style.boxShadow = '0 1px 2px rgba(0, 0, 0, 0.05)';
    });
    
    // Enhanced copy button click with animation
    btnElement.addEventListener('click', function(e) {
      e.stopPropagation();
      trackActivity();
      copyToClipboard(suggestion);
      
      // Professional visual feedback
      var originalText = btnElement.textContent;
      btnElement.textContent = '✓ Copied';
      btnElement.style.backgroundColor = COLORS.success;
      btnElement.style.borderColor = COLORS.success;
      btnElement.style.color = '#ffffff';
      btnElement.style.transform = 'scale(0.95)';
      
      setTimeout(function() {
        btnElement.style.transform = 'scale(1)';
      }, 100);
      
      setTimeout(function() {
        btnElement.textContent = originalText;
        btnElement.style.backgroundColor = COLORS.copyButtonBg;
        btnElement.style.borderColor = COLORS.copyButtonBorder;
        btnElement.style.color = COLORS.copyButtonText;
        btnElement.style.transform = 'translateY(0)';
      }, 1500);
    });
  }

  // Show suggestions
  function showSuggestions(panel, suggestions, textbox) {
    console.log('🎯 showSuggestions called with', suggestions.length, 'suggestions');
    panel.innerHTML = '';
    
    // Professional header with branding
    var header = document.createElement('div');
    header.style.cssText = 
      'display: flex !important;' +
      'align-items: center !important;' +
      'justify-content: space-between !important;' +
      'padding: 16px 20px !important;' +
      'background: ' + COLORS.headerBg + ' !important;' +
      'border-bottom: 1px solid ' + COLORS.headerBorder + ' !important;' +
      'border-radius: 12px 12px 0 0 !important;';
    
    var headerLeft = document.createElement('div');
    headerLeft.style.cssText = 
      'display: flex !important;' +
      'align-items: center !important;' +
      'gap: 8px !important;';
    
    var brandIcon = document.createElement('div');
    brandIcon.style.cssText = 
      'width: 20px !important;' +
      'height: 20px !important;' +
      'background: linear-gradient(135deg, ' + COLORS.accent + ', #4285f4) !important;' +
      'border-radius: 4px !important;' +
      'display: flex !important;' +
      'align-items: center !important;' +
      'justify-content: center !important;' +
      'color: white !important;' +
      'font-size: 10px !important;' +
      'font-weight: bold !important;';
    brandIcon.textContent = 'AI';
    
    var headerText = document.createElement('span');
    headerText.style.cssText = 
      'font-weight: 600 !important;' +
      'font-size: 15px !important;' +
      'color: ' + COLORS.headerText + ' !important;' +
      'letter-spacing: -0.01em !important;';
    headerText.textContent = 'svarx.ai Suggestions';
    
    var closeButton = document.createElement('button');
    closeButton.style.cssText = 
      'background: none !important;' +
      'border: none !important;' +
      'color: ' + COLORS.textSecondary + ' !important;' +
      'cursor: pointer !important;' +
      'font-size: 18px !important;' +
      'padding: 4px !important;' +
      'width: 28px !important;' +
      'height: 28px !important;' +
      'display: flex !important;' +
      'align-items: center !important;' +
      'justify-content: center !important;' +
      'border-radius: 6px !important;' +
      'transition: all 0.15s ease !important;';
    
    closeButton.innerHTML = '×';
    closeButton.title = 'Close suggestions';
    
    // Close button hover effect
    closeButton.addEventListener('mouseenter', function() {
      closeButton.style.backgroundColor = COLORS.suggestionHover;
      closeButton.style.color = COLORS.headerText;
    });
    
    closeButton.addEventListener('mouseleave', function() {
      closeButton.style.backgroundColor = 'transparent';
      closeButton.style.color = COLORS.textSecondary;
    });
    
    headerLeft.appendChild(brandIcon);
    headerLeft.appendChild(headerText);
    header.appendChild(headerLeft);
    header.appendChild(closeButton);
    
    closeButton.addEventListener('click', function(e) {
      e.stopPropagation();
      trackActivity();
      panel.style.display = 'none';
    });
    
    panel.appendChild(header);
    
    // Create scrollable content area
    var contentArea = document.createElement('div');
    contentArea.style.cssText = 
      'max-height: 320px !important;' +
      'overflow-y: auto !important;' +
      'overflow-x: hidden !important;';
    
    panel.appendChild(contentArea);
    
    // Add suggestions
    for (var i = 0; i < suggestions.length; i++) {
      var suggestion = suggestions[i];
      
      // Create professional suggestion container
      var suggestionContainer = document.createElement('div');
      suggestionContainer.style.cssText = 
        'display: flex !important;' +
        'align-items: flex-start !important;' +
        'gap: 12px !important;' +
        'padding: 16px 20px !important;' +
        'border-bottom: 1px solid ' + COLORS.suggestionBorder + ' !important;' +
        'background: ' + COLORS.suggestionBg + ' !important;' +
        'transition: all 0.15s ease !important;' +
        'position: relative !important;';
      
      // Add suggestion number indicator
      var suggestionNumber = document.createElement('div');
      suggestionNumber.style.cssText = 
        'width: 20px !important;' +
        'height: 20px !important;' +
        'border-radius: 50% !important;' +
        'background: ' + COLORS.headerBg + ' !important;' +
        'border: 1px solid ' + COLORS.panelBorder + ' !important;' +
        'display: flex !important;' +
        'align-items: center !important;' +
        'justify-content: center !important;' +
        'font-size: 11px !important;' +
        'font-weight: 600 !important;' +
        'color: ' + COLORS.textSecondary + ' !important;' +
        'flex-shrink: 0 !important;' +
        'margin-top: 2px !important;';
      suggestionNumber.textContent = (i + 1).toString();
      
      // Create suggestion text area
      var suggestionText = document.createElement('div');
      suggestionText.style.cssText = 
        'flex: 1 !important;' +
        'cursor: pointer !important;' +
        'color: ' + COLORS.suggestionText + ' !important;' +
        'font-size: 14px !important;' +
        'line-height: 1.5 !important;' +
        'font-weight: 400 !important;' +
        'letter-spacing: -0.01em !important;' +
        'margin-right: 8px !important;';
      
      suggestionText.textContent = suggestion;
      
      // Create modern copy button
      var copyButton = document.createElement('button');
      copyButton.style.cssText = 
        'padding: 8px 16px !important;' +
        'border: 1px solid ' + COLORS.copyButtonBorder + ' !important;' +
        'background: ' + COLORS.copyButtonBg + ' !important;' +
        'color: ' + COLORS.copyButtonText + ' !important;' +
        'border-radius: 8px !important;' +
        'cursor: pointer !important;' +
        'font-size: 13px !important;' +
        'font-weight: 500 !important;' +
        'min-width: 60px !important;' +
        'height: 36px !important;' +
        'display: flex !important;' +
        'align-items: center !important;' +
        'justify-content: center !important;' +
        'transition: all 0.15s ease !important;' +
        'box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05) !important;' +
        'flex-shrink: 0 !important;';
      
      copyButton.textContent = 'Copy';
      copyButton.title = 'Copy to clipboard';
      
      console.log('📋 Copy button created for suggestion:', suggestion.substring(0, 30) + '...');
      
      // Setup event handlers with proper closure
      setupSuggestionEvents(suggestionContainer, suggestionText, copyButton, suggestion, textbox, panel);
      
      // Assemble the professional suggestion item
      suggestionContainer.appendChild(suggestionNumber);
      suggestionContainer.appendChild(suggestionText);
      suggestionContainer.appendChild(copyButton);
      contentArea.appendChild(suggestionContainer);
      
      console.log('✅ Added suggestion container with copy button');
    }
    
    panel.style.display = 'block';
  }
  
  // Setup textbox
  function setupTextbox(textbox) {
    if (textbox.getAttribute(CONFIG.createdAttr)) return;
    
    textbox.setAttribute(CONFIG.createdAttr, 'true');
    
    if (window.getComputedStyle(textbox).position === 'static') {
      textbox.style.position = 'relative';
    }
    
    var button = createButton();
    var panel = createPanel();
    
    try {
      textbox.appendChild(button);
      textbox.appendChild(panel);
    } catch (e) {
      console.log('Append failed, trying alternative');
      return;
    }
    
    button.addEventListener('click', function(e) {
      e.preventDefault();
      e.stopPropagation();
      
      trackActivity(); // Track user interaction
      
      // Toggle panel visibility
      if (panel.style.display === 'block') {
        panel.style.display = 'none';
        return;
      }
      
      button.textContent = '...';
      
      getSuggestions(function(suggestions) {
        showSuggestions(panel, suggestions, textbox);
        button.textContent = 'AI';
      });
    });
    
    // Close panel when clicking outside
    document.addEventListener('click', function(e) {
      if (!panel.contains(e.target) && !button.contains(e.target)) {
        panel.style.display = 'none';
      }
      trackActivity(); // Track any click activity
    });
  }
  
  // Activity tracking
  function trackActivity() {
    lastActivity = Date.now();
    if (!isActive) {
      console.log('🔄 svarx.ai reactivating from idle state');
      reactivate();
    }
    resetIdleTimer();
  }
  
  // Reset idle timer
  function resetIdleTimer() {
    if (idleTimer) {
      clearTimeout(idleTimer);
    }
    idleTimer = setTimeout(function() {
      if (isActive && Date.now() - lastActivity >= CONFIG.idleTimeout) {
        enterIdleMode();
      }
    }, CONFIG.idleTimeout);
  }
  
  // Enter idle mode to save memory
  function enterIdleMode() {
    if (!isActive) return;
    
    console.log('💤 svarx.ai entering idle mode to save memory');
    isActive = false;
    
    // Clear intervals and observers
    if (scanInterval) {
      clearInterval(scanInterval);
      scanInterval = null;
    }
    
    if (observer) {
      observer.disconnect();
      observer = null;
    }
    
    // Hide all panels
    var panels = document.querySelectorAll('.' + CONFIG.panelClass);
    for (var i = 0; i < panels.length; i++) {
      panels[i].style.display = 'none';
    }
    
    // Keep minimal event listeners for reactivation
    setupReactivationListeners();
  }
  
  // Reactivate from idle mode
  function reactivate() {
    if (isActive) return;
    
    isActive = true;
    console.log('⚡ svarx.ai reactivated');
    
    // Restart scanning
    scanInterval = setInterval(scanTextboxes, 3000);
    
    // Restart observer
    observer = new MutationObserver(function() {
      trackActivity();
      setTimeout(scanTextboxes, 500);
    });
    
    observer.observe(document.body, {
      childList: true,
      subtree: true
    });
    
    // Scan immediately
    setTimeout(scanTextboxes, 100);
  }
  
  // Setup reactivation listeners
  function setupReactivationListeners() {
    var events = ['click', 'keydown', 'mousemove', 'scroll', 'focus'];
    
    function reactivationHandler() {
      trackActivity();
      // Remove listeners after reactivation
      for (var i = 0; i < events.length; i++) {
        document.removeEventListener(events[i], reactivationHandler, true);
      }
    }
    
    // Add lightweight listeners
    for (var i = 0; i < events.length; i++) {
      document.addEventListener(events[i], reactivationHandler, true);
    }
  }
  
  // Scan for textboxes
  function scanTextboxes() {
    if (!isActive) return;
    
    trackActivity();
    
    for (var i = 0; i < SELECTORS.length; i++) {
      try {
        var textboxes = document.querySelectorAll(SELECTORS[i]);
        for (var j = 0; j < textboxes.length; j++) {
          var textbox = textboxes[j];
          if (textbox.offsetWidth > 0 && textbox.offsetHeight > 0) {
            setupTextbox(textbox);
          }
        }
      } catch (error) {
        // Ignore selector errors
      }
    }
  }
  
  // Initialize
  function init() {
    console.log('✅ svarx.ai initializing with auto-idle feature...');
    
    // Initial scan
    setTimeout(scanTextboxes, 1000);
    
    // Start scanning interval
    scanInterval = setInterval(scanTextboxes, 3000);
    
    // Start mutation observer
    observer = new MutationObserver(function() {
      trackActivity();
      setTimeout(scanTextboxes, 500);
    });
    
    observer.observe(document.body, {
      childList: true,
      subtree: true
    });
    
    // Start idle timer
    resetIdleTimer();
    
    // Track initial activity
    trackActivity();
    
    console.log('✅ svarx.ai ready (will auto-idle after 1 minute of inactivity)');
  }
  
  // Cleanup on page unload
  function cleanup() {
    console.log('🧹 svarx.ai cleaning up...');
    
    if (scanInterval) {
      clearInterval(scanInterval);
    }
    
    if (observer) {
      observer.disconnect();
    }
    
    if (idleTimer) {
      clearTimeout(idleTimer);
    }
  }
  
  // Add professional CSS animations
  var style = document.createElement('style');
  style.textContent = 
    '@keyframes slideIn {' +
      'from { opacity: 0; transform: translateY(-10px) scale(0.95); }' +
      'to { opacity: 1; transform: translateY(0) scale(1); }' +
    '}' +
    '.' + CONFIG.panelClass + '::-webkit-scrollbar {' +
      'width: 6px;' +
    '}' +
    '.' + CONFIG.panelClass + '::-webkit-scrollbar-track {' +
      'background: transparent;' +
    '}' +
    '.' + CONFIG.panelClass + '::-webkit-scrollbar-thumb {' +
      'background: #cbd5e1;' +
      'border-radius: 3px;' +
    '}' +
    '.' + CONFIG.panelClass + '::-webkit-scrollbar-thumb:hover {' +
      'background: #94a3b8;' +
    '}';
  
  document.head.appendChild(style);
  
  // Start
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
  
  // Cleanup on page unload
  window.addEventListener('beforeunload', cleanup);
  window.addEventListener('unload', cleanup);
  
})();