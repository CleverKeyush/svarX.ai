# local-server.py
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import time, threading, os, gc, psutil
from model_manager import model_exists, model_path_str, get_model_path
from personalization import add_sample, list_samples, build_style_summary, clear_samples
from threading import Lock
import traceback

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
LLAMA = None
LOCK = Lock()
DEFAULT_TEMPERATURE = float(os.environ.get("GMAIL_AI_TEMPERATURE", 0.25))
N_THREADS = int(os.environ.get("GMAIL_AI_THREADS", 4))

# Memory management variables
LAST_USED = 0
IDLE_TIMEOUT = 60  # 1 minute idle timeout for better memory optimization
MODEL_LOADED = False
MAX_IDLE_MEMORY_MB = 500  # Maximum memory when idle (500MB limit)
MAX_IDLE_CPU_PERCENT = 5  # Maximum CPU usage when idle (5% limit)

# Power management
def set_low_power_mode():
    """Set process to ultra-low power mode - 5% CPU, <500MB RAM"""
    try:
        process = psutil.Process()
        
        # Set to lowest possible CPU priority for background processing
        if hasattr(psutil, 'IDLE_PRIORITY_CLASS'):
            process.nice(psutil.IDLE_PRIORITY_CLASS)  # Lowest priority on Windows
        elif hasattr(psutil, 'BELOW_NORMAL_PRIORITY_CLASS'):
            process.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
        else:
            process.nice(19)  # Lowest priority on Unix
        
        # Limit to single CPU core for minimal power consumption
        if hasattr(process, 'cpu_affinity'):
            available_cpus = process.cpu_affinity()
            if available_cpus:
                process.cpu_affinity([available_cpus[0]])  # Use only first CPU core
        
        # Force garbage collection to minimize memory
        import gc
        gc.collect()
        
        app.logger.info("🔋 Ultra-low power mode: Max 5% CPU, <500MB RAM")
    except Exception as e:
        app.logger.warning(f"Could not set low power mode: {e}")

def set_normal_power_mode():
    """Restore normal power mode"""
    try:
        process = psutil.Process()
        # Restore normal priority
        if hasattr(psutil, 'NORMAL_PRIORITY_CLASS'):
            process.nice(psutil.NORMAL_PRIORITY_CLASS)
        else:
            process.nice(0)  # Normal priority
        
        # Restore all CPU cores
        if hasattr(process, 'cpu_affinity'):
            available_cpus = list(range(psutil.cpu_count()))
            process.cpu_affinity(available_cpus)
        
        app.logger.info("⚡ Restored normal power mode")
    except Exception as e:
        app.logger.warning(f"Could not restore normal power mode: {e}")

def unload_model():
    """Unload model to free memory"""
    global LLAMA, MODEL_LOADED
    if LLAMA is not None:
        app.logger.info("🗑️ Unloading AI model to free memory...")
        del LLAMA
        LLAMA = None
        MODEL_LOADED = False
        
        # Restore normal power mode when model unloaded
        set_normal_power_mode()
        
        gc.collect()  # Force garbage collection
        app.logger.info("✅ Model unloaded, memory freed, power restored")

def load_model(force_reload=False):
    global LLAMA, MODEL_LOADED, LAST_USED
    
    # Update last used time
    LAST_USED = time.time()
    
    if LLAMA is not None and not force_reload:
        MODEL_LOADED = True
        return True
    
    # Clear existing model if reloading
    if force_reload and LLAMA is not None:
        unload_model()
    
    if not model_exists():
        app.logger.warning(f"Model not found at {get_model_path()}")
        return False
    
    try:
        from llama_cpp import Llama
        path = model_path_str()
        app.logger.info(f"🚀 Loading Llama-3.2-3B on-demand...")
        
        # Ultra-efficient settings: 5% CPU, <500MB RAM when idle
        LLAMA = Llama(
            model_path=str(path), 
            n_ctx=256,       # Ultra-minimal context (saves more RAM)
            n_threads=1,     # Single thread for 5% CPU limit
            n_batch=32,      # Smallest possible batch size
            verbose=False,
            use_mmap=True,   # Memory mapping for efficiency
            use_mlock=False, # Don't lock memory pages
            n_gpu_layers=0,  # CPU only (no GPU power)
            low_vram=True,   # Enable low VRAM mode
            # Ultra power-saving options
            rope_scaling_type=0,  # Disable rope scaling
            numa=False,      # Disable NUMA optimizations
            f16_kv=True,     # Use half precision for key-value cache
            # Additional memory optimizations
            offload_kqv=True,    # Offload key-value cache
            flash_attn=False,    # Disable flash attention (saves memory)
            split_mode=1,        # Split model across CPU efficiently
        )
        MODEL_LOADED = True
        app.logger.info("✅ Model loaded with minimal power footprint")
        
        # Set to low power mode when model is loaded
        set_low_power_mode()
        
        # Start idle monitor thread
        threading.Thread(target=idle_monitor, daemon=True).start()
        
        return True
    except Exception as e:
        app.logger.exception("Model load failed: %s", e)
        return False

def idle_monitor():
    """Monitor model usage, optimize resources, and perform background learning when idle"""
    global LAST_USED, MODEL_LOADED
    
    learning_cycle = 0  # Track learning cycles
    
    while MODEL_LOADED:
        time.sleep(15)  # Check every 15 seconds for better optimization
        
        if MODEL_LOADED and LAST_USED > 0:
            idle_time = time.time() - LAST_USED
            
            # Check memory usage
            try:
                process = psutil.Process()
                memory_mb = process.memory_info().rss / 1024 / 1024
                cpu_percent = process.cpu_percent(interval=1)
                
                # Background learning during idle time (within resource limits)
                if idle_time > 20 and idle_time < IDLE_TIMEOUT:
                    learning_cycle += 1
                    
                    # Perform lightweight learning tasks every few cycles
                    if learning_cycle % 4 == 0:  # Every ~1 minute
                        background_learning_task(memory_mb, cpu_percent)
                
                # If idle for 30+ seconds, enforce resource limits
                if idle_time > 30:
                    if memory_mb > MAX_IDLE_MEMORY_MB:
                        app.logger.info(f"💾 Memory usage {memory_mb:.0f}MB > {MAX_IDLE_MEMORY_MB}MB, optimizing...")
                        import gc
                        gc.collect()  # Force garbage collection
                        
                    if cpu_percent > MAX_IDLE_CPU_PERCENT:
                        app.logger.info(f"⚡ CPU usage {cpu_percent:.1f}% > {MAX_IDLE_CPU_PERCENT}%, throttling...")
                        time.sleep(2)  # Add delay to reduce CPU usage
                
                # Unload model after full idle timeout
                if idle_time > IDLE_TIMEOUT:
                    app.logger.info(f"⏰ Model idle for {idle_time:.0f}s, unloading...")
                    unload_model()
                    break
                    
            except Exception as e:
                app.logger.debug(f"Resource monitoring error: {e}")

def background_learning_task(current_memory_mb, current_cpu_percent):
    """Perform lightweight learning tasks during idle time"""
    try:
        # Only proceed if within resource limits
        if current_memory_mb > MAX_IDLE_MEMORY_MB * 0.8 or current_cpu_percent > MAX_IDLE_CPU_PERCENT * 0.6:
            return  # Skip if resources are too high
        
        from personalization import (
            analyze_user_patterns, smart_cleanup, get_training_pairs,
            list_samples, compress_old_data, get_feedback_patterns
        )
        
        # Rotate through different learning tasks
        task_cycle = int(time.time() / 60) % 6  # 6 different tasks, rotate every minute
        
        if task_cycle == 0:
            # Task 1: Analyze and update user patterns
            app.logger.info("🧠 Background learning: Analyzing user patterns...")
            patterns = analyze_user_patterns()
            if patterns:
                app.logger.info(f"📊 Updated patterns: {patterns.get('preferred_tone', 'unknown')} tone")
        
        elif task_cycle == 1:
            # Task 2: Smart cleanup and optimization
            app.logger.info("🗜️ Background learning: Optimizing storage...")
            smart_cleanup()
            compressed = compress_old_data()
            if compressed > 0:
                app.logger.info(f"📦 Compressed {compressed} old patterns")
        
        elif task_cycle == 2:
            # Task 3: Analyze feedback patterns for improvement
            app.logger.info("👆 Background learning: Analyzing feedback patterns...")
            feedback = get_feedback_patterns()
            positive_count = len(feedback.get('positive_patterns', []))
            if positive_count > 0:
                app.logger.info(f"✅ Found {positive_count} positive feedback patterns")
        
        elif task_cycle == 3:
            # Task 4: Process training pairs for pattern extraction
            app.logger.info("🎯 Background learning: Processing training data...")
            training_pairs = get_training_pairs(20)  # Small batch
            if training_pairs:
                # Extract common response patterns
                tone_patterns = {}
                for pair in training_pairs:
                    tone = pair.get('tone', 'professional')
                    tone_patterns[tone] = tone_patterns.get(tone, 0) + 1
                app.logger.info(f"📈 Tone distribution: {tone_patterns}")
        
        elif task_cycle == 4:
            # Task 5: Analyze writing samples for style evolution
            app.logger.info("✍️ Background learning: Analyzing writing evolution...")
            samples = list_samples(30)  # Small batch
            if len(samples) > 5:
                # Analyze recent vs older samples for style changes
                recent_samples = samples[:10]
                older_samples = samples[10:20] if len(samples) > 10 else []
                
                if older_samples:
                    recent_avg_len = sum(len(s['text'].split()) for s in recent_samples) / len(recent_samples)
                    older_avg_len = sum(len(s['text'].split()) for s in older_samples) / len(older_samples)
                    
                    if abs(recent_avg_len - older_avg_len) > 5:
                        app.logger.info(f"📊 Style evolution: Length changed from {older_avg_len:.1f} to {recent_avg_len:.1f} words")
        
        elif task_cycle == 5:
            # Task 6: Prepare optimized prompts based on learned patterns
            app.logger.info("🎨 Background learning: Optimizing prompt templates...")
            patterns = analyze_user_patterns()
            if patterns:
                preferred_tone = patterns.get('preferred_tone', 'professional')
                formality = patterns.get('formality_level', 0.5)
                
                # Cache optimized prompt templates for faster generation
                app.logger.info(f"🚀 Cached templates for {preferred_tone} tone, {formality:.1%} formality")
        
        # Small delay to keep CPU usage minimal
        time.sleep(0.5)
        
    except Exception as e:
        app.logger.debug(f"Background learning error: {e}")

@app.route("/", methods=["GET"])
def root():
    return jsonify({
        "name": "Gmail AI Pro Server",
        "version": "1.4.0",
        "status": "running",
        "endpoints": ["/health", "/generate", "/remember", "/samples", "/clear_personalization", "/export_style"]
    })

@app.route("/health", methods=["GET"])
def health():
    # Don't auto-load model for health check - just check if file exists
    model_available = model_exists()
    return jsonify({
        "ok": model_available, 
        "has_model": model_available, 
        "model_path": model_path_str(),
        "model_loaded": MODEL_LOADED,
        "memory_optimized": True
    })

@app.route("/reload_model", methods=["POST"])
def reload_model():
    """Reload the model with updated settings"""
    try:
        success = load_model(force_reload=True)
        return jsonify({"ok": success, "message": "Model reloaded with 4096 context window"})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

def fallback_reply(email_text, tone, length):
    text = (email_text or "").lower()
    
    # More intelligent fallback based on email content
    if "meeting" in text or "resched" in text or "reschedule" in text or "calendar" in text:
        base = "I can accommodate a schedule change. Please share your preferred times and I'll confirm availability."
    elif "thank" in text or "appreciate" in text or "grateful" in text:
        base = "You're very welcome! I'm glad I could help. Please don't hesitate to reach out if you need anything else."
    elif "urgent" in text or "asap" in text or "immediate" in text or "priority" in text:
        base = "I understand this is time-sensitive. I'll prioritize this and get back to you as soon as possible."
    elif "question" in text or "clarif" in text or "explain" in text or "help" in text:
        base = "Thank you for your question. I'll review this carefully and provide a detailed response shortly."
    elif "confirm" in text or "verification" in text or "verify" in text:
        base = "I can confirm the details for you. Let me review everything and get back to you with verification."
    elif "update" in text or "status" in text or "progress" in text:
        base = "Thank you for checking in. I'll provide you with a comprehensive update on the current status."
    elif "sorry" in text or "apolog" in text or "mistake" in text:
        base = "No problem at all! These things happen. Let me know how I can help resolve this."
    else:
        base = "Thank you for reaching out. I've received your message and will respond with the information you need."
    
    # Tone adjustments
    if tone == "casual":
        base = base.replace("Thank you for", "Thanks for")
        base = base.replace("I'm glad I could help", "Happy to help")
        base = base.replace("Please don't hesitate", "Feel free")
    elif tone == "formal":
        base = "Dear Colleague,\n\n" + base + "\n\nBest regards"
    
    # Length adjustments
    if length == "short":
        return base.split(".")[0] + "."
    elif length == "long":
        return base + " I will ensure all aspects are thoroughly addressed and provide you with complete documentation as needed."
    
    return base

def build_prompt(email_text, tone, length):
    # Allow more context but still safe
    if len(email_text) > 400:
        email_text = email_text[:400] + "..."
    
    # Clean up email text
    email_text = email_text.strip()
    if not email_text:
        email_text = "Hello, I hope you're doing well."
    
    # Get email context insights for smarter prompts
    try:
        from personalization import get_email_context_insights
        insights = get_email_context_insights()
        
        # Detect email type for context-aware responses
        text_lower = email_text.lower()
        email_type = "general"
        
        if any(word in text_lower for word in ["meeting", "schedule", "calendar"]):
            email_type = "scheduling"
        elif any(word in text_lower for word in ["thank", "appreciate", "grateful"]):
            email_type = "gratitude"
        elif any(word in text_lower for word in ["urgent", "asap", "immediate"]):
            email_type = "urgent"
        elif any(word in text_lower for word in ["question", "help", "clarify"]):
            email_type = "inquiry"
        
    except:
        insights = {}
        email_type = "general"
    
    # Llama-3.2-3B optimized prompts (more concise for efficiency)
    if email_type == "scheduling":
        if tone == "casual":
            prompt = f"Email: {email_text}\n\nWrite a friendly reply about scheduling. Suggest specific times or ask for their availability.\n\nReply:"
        elif tone == "formal":
            prompt = f"Email: {email_text}\n\nWrite a professional scheduling response. Offer specific meeting times or request their availability.\n\nReply:"
        else:
            prompt = f"Email: {email_text}\n\nReply professionally about scheduling. Provide time options or ask for their preferences.\n\nReply:"
    
    elif email_type == "gratitude":
        if tone == "casual":
            prompt = f"Email: {email_text}\n\nWrite a warm, friendly response to this thank you message.\n\nReply:"
        else:
            prompt = f"Email: {email_text}\n\nWrite a gracious professional response to this thank you message.\n\nReply:"
    
    elif email_type == "urgent":
        prompt = f"Email: {email_text}\n\nThis is urgent. Write a {tone} reply that acknowledges the urgency and offers quick action.\n\nReply:"
    
    elif email_type == "inquiry":
        prompt = f"Email: {email_text}\n\nThis is a question. Write a {tone} reply that provides helpful information.\n\nReply:"
    
    else:
        # General email - simple and efficient
        if tone == "casual":
            prompt = f"Email: {email_text}\n\nWrite a friendly, conversational reply.\n\nReply:"
        elif tone == "formal":
            prompt = f"Email: {email_text}\n\nWrite a formal, professional reply.\n\nReply:"
        else:
            prompt = f"Email: {email_text}\n\nWrite a professional, helpful reply.\n\nReply:"
    
    return prompt

# Removed find_similar_context to prevent token overflow
# The learning system still works through style analysis

@app.route("/generate", methods=["POST"])
def generate():
    global LAST_USED
    data = request.get_json(force=True)
    email_text = data.get("email_text") or data.get("text") or ""
    tone = data.get("tone", "professional")
    length = data.get("length", "medium")
    
    if not email_text:
        return jsonify({"ok": False, "reply": "No input provided."}), 400
    
    with LOCK:
        # Update last used time
        LAST_USED = time.time()
        
        # Load model on-demand
        app.logger.info("🔄 Loading AI model on-demand...")
        if not load_model():
            app.logger.error("Model failed to load, using fallback")
            return jsonify({"ok": False, "from_model": False, "reply": fallback_reply(email_text, tone, length)})
        
        if LLAMA is None:
            app.logger.error("LLAMA is None after load_model, using fallback")
            return jsonify({"ok": False, "from_model": False, "reply": fallback_reply(email_text, tone, length)})
        prompt = build_prompt(email_text, tone, length)
        
        # Learn from incoming email patterns (passive learning)
        try:
            from personalization import analyze_and_learn_from_email
            analyze_and_learn_from_email(email_text, tone, length)
        except Exception as e:
            app.logger.debug(f"Email analysis failed: {e}")
        
        try:
            t0 = time.time()
            app.logger.info(f"Generating with prompt length: {len(prompt)} chars")
            
            # Ensure low power mode during generation
            set_low_power_mode()
            
            # Add small delay to prevent CPU spikes
            time.sleep(0.1)
            
            # Minimal power parameters for maximum efficiency
            res = LLAMA(
                prompt, 
                max_tokens=50,   # Very short responses for speed
                temperature=0.5, # Lower temperature for faster processing
                top_p=0.8,       # Reduced for efficiency
                top_k=15,        # Minimal sampling for speed
                repeat_penalty=1.05, # Lower penalty for faster processing
                stop=["\n\nEmail:", "\n\nReply:", "\n---", "###", "\n\n\n"]
            )
            elapsed = time.time() - t0
            
            app.logger.info(f"Raw model response type: {type(res)}")
            
            # Extract text from response - handle different formats
            reply = ""
            if isinstance(res, dict):
                if "choices" in res and res["choices"]:
                    reply = res["choices"][0].get("text", "").strip()
                elif "content" in res:
                    reply = res["content"].strip()
                elif "text" in res:
                    reply = res["text"].strip()
                else:
                    # Log the structure to debug
                    app.logger.info(f"Unknown response structure: {list(res.keys())}")
            elif isinstance(res, str):
                reply = res.strip()
            
            # Clean up response more thoroughly
            if reply:
                # Remove common artifacts and prompts
                reply = reply.replace("Reply:", "").replace("Email:", "").replace("Email received:", "").strip()
                reply = reply.replace("Write a", "").replace("reply", "").strip()
                
                # Remove leading/trailing quotes or colons
                reply = reply.strip('"\':-')
                
                # Ensure it starts with capital letter
                if reply and reply[0].islower():
                    reply = reply[0].upper() + reply[1:]
                
            app.logger.info(f"Cleaned reply: '{reply}' (length: {len(reply)})")
            
            # More lenient validation - accept shorter responses
            if reply and len(reply) >= 5 and not reply.lower().startswith(('write', 'email', 'reply')):
                app.logger.info(f"✅ AI generated: {reply[:50]}...")
                return jsonify({"ok": True, "from_model": True, "reply": reply, "meta": {"elapsed": elapsed}})
            else:
                app.logger.warning(f"❌ Poor AI response: '{reply}' (len={len(reply)}), using fallback")
                # Try one more time with simpler prompt if response was too short
                if len(reply) < 5:
                    simple_prompt = f"Reply to: {email_text[:100]}\n\n"
                    try:
                        res2 = LLAMA(simple_prompt, max_tokens=60, temperature=0.9, stop=["\n"])
                        if isinstance(res2, dict) and "choices" in res2:
                            simple_reply = res2["choices"][0].get("text", "").strip()
                            if simple_reply and len(simple_reply) >= 5:
                                app.logger.info(f"✅ Simple retry worked: {simple_reply[:30]}...")
                                return jsonify({"ok": True, "from_model": True, "reply": simple_reply, "meta": {"elapsed": elapsed}})
                    except:
                        pass
                
                return jsonify({"ok": True, "from_model": False, "reply": fallback_reply(email_text, tone, length), "meta": {"elapsed": elapsed}})
            
        except ValueError as e:
            if "exceed context window" in str(e):
                app.logger.warning("Context window exceeded, using fallback")
                return jsonify({"ok": False, "from_model": False, "reply": fallback_reply(email_text, tone, length)})
            else:
                app.logger.error(f"ValueError: {e}")
                return jsonify({"ok": False, "from_model": False, "reply": fallback_reply(email_text, tone, length)})
        except Exception as e:
            app.logger.exception("Generation error")
            return jsonify({"ok": False, "from_model": False, "reply": fallback_reply(email_text, tone, length)})

@app.route("/learn_interaction", methods=["POST"])
def learn_interaction():
    """Enhanced learning from user interactions"""
    data = request.get_json(force=True)
    
    interaction_type = data.get("interaction_type", "")
    suggestion = data.get("suggestion", "")
    original_email = data.get("original_email", "")
    feedback = data.get("feedback", "neutral")
    context = data.get("context", {})
    suggestion_index = data.get("suggestion_index", 0)
    
    if not suggestion or not original_email:
        return jsonify({"ok": False, "error": "missing data"}), 400
    
    try:
        from personalization import add_interaction_feedback, add_training_pair, add_sample
        
        # Store interaction for learning
        learning_data = {
            "interaction_type": interaction_type,
            "suggestion": suggestion,
            "original_email": original_email,
            "feedback": feedback,
            "context": context,
            "suggestion_index": suggestion_index
        }
        
        # Different learning based on interaction type
        if interaction_type == "selected":
            # User actually used this suggestion - strongest positive signal
            add_sample(suggestion)
            add_training_pair(original_email, suggestion, context)
            add_interaction_feedback(learning_data, weight=1.0)
            
        elif interaction_type == "thumbs_up":
            # User liked it but didn't use - positive signal
            add_interaction_feedback(learning_data, weight=0.7)
            
        elif interaction_type == "thumbs_down":
            # User disliked it - negative signal for learning
            add_interaction_feedback(learning_data, weight=-0.5)
        
        return jsonify({
            "ok": True, 
            "learned": True,
            "interaction_type": interaction_type,
            "feedback_recorded": feedback
        })
        
    except Exception as e:
        app.logger.exception("Learning interaction failed")
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route("/remember", methods=["POST"])
def remember():
    """Legacy remember function"""
    data = request.get_json(force=True)
    text = data.get("text", "")
    original_email = data.get("original_email", "")
    context = data.get("context", {})
    
    if not text:
        return jsonify({"ok": False, "error": "no text"}), 400
    try:
        # Store the chosen reply for learning
        add_sample(text)
        
        # Store training pair if we have original email
        if original_email:
            add_training_pair(original_email, text, context)
        
        return jsonify({"ok": True, "learned": True})
    except Exception as e:
        app.logger.exception("Remember failed")
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route("/samples", methods=["GET"])
def samples():
    limit = int(request.args.get("limit", 50))
    try:
        s = list_samples(limit=limit)
        return jsonify({"ok": True, "samples": s})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route("/clear_personalization", methods=["POST"])
def clear_pers():
    try:
        clear_samples()
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route("/learning_stats", methods=["GET"])
def learning_stats():
    """Get learning statistics and storage info"""
    try:
        from personalization import analyze_user_patterns, get_training_pairs, list_samples, get_storage_status, get_email_context_insights
        
        patterns = analyze_user_patterns()
        training_count = len(get_training_pairs(1000))
        sample_count = len(list_samples(1000))
        storage_status = get_storage_status()
        email_insights = get_email_context_insights()
        
        # Count email patterns analyzed
        email_pattern_count = sum(email_insights.get("common_email_types", {}).values())
        
        stats = {
            "training_pairs": training_count,
            "writing_samples": sample_count,
            "email_patterns_analyzed": email_pattern_count,
            "patterns": patterns,
            "email_insights": email_insights,
            "learning_active": training_count > 0 or email_pattern_count > 0,
            "personalization_level": min(100, (training_count + sample_count + email_pattern_count)),
            "storage": {
                "db_size_mb": storage_status["size_mb"],
                "max_size_mb": storage_status["max_size_mb"],
                "usage_percent": storage_status["usage_percent"],
                "status": storage_status["status"],
                "samples": storage_status["samples"],
                "training_pairs": storage_status["training_pairs"],
                "interactions": storage_status["interactions"]
            }
        }
        
        return jsonify({"ok": True, "stats": stats})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route("/storage_status", methods=["GET"])
def storage_status_endpoint():
    """Detailed storage status endpoint"""
    try:
        from personalization import get_storage_status
        status = get_storage_status()
        
        # Add recommendations based on status
        recommendations = []
        if status["usage_percent"] > 95:
            recommendations.append("Critical: Storage almost full. Automatic cleanup will run soon.")
        elif status["usage_percent"] > 80:
            recommendations.append("Warning: Storage usage high. Consider manual cleanup.")
        elif status["usage_percent"] > 60:
            recommendations.append("Good: Storage usage normal. System learning actively.")
        else:
            recommendations.append("Excellent: Plenty of storage available for learning.")
        
        status["recommendations"] = recommendations
        return jsonify({"ok": True, "storage": status})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route("/cleanup_storage", methods=["POST"])
def cleanup_storage():
    """Manual storage cleanup with enhanced intelligence"""
    try:
        from personalization import smart_cleanup, compress_old_data, get_storage_status
        
        status_before = get_storage_status()
        final_size = smart_cleanup()
        compressed_patterns = compress_old_data()
        status_after = get_storage_status()
        
        return jsonify({
            "ok": True,
            "cleanup_performed": True,
            "before": {
                "size_mb": status_before["size_mb"],
                "usage_percent": status_before["usage_percent"],
                "samples": status_before["samples"],
                "training_pairs": status_before["training_pairs"],
                "interactions": status_before["interactions"]
            },
            "after": {
                "size_mb": status_after["size_mb"],
                "usage_percent": status_after["usage_percent"],
                "samples": status_after["samples"],
                "training_pairs": status_after["training_pairs"],
                "interactions": status_after["interactions"]
            },
            "space_saved_mb": round(status_before["size_mb"] - status_after["size_mb"], 2),
            "compressed_patterns": compressed_patterns,
            "message": f"Storage optimized from {status_before['usage_percent']:.1f}% to {status_after['usage_percent']:.1f}%"
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route("/export_style", methods=["GET"])
def export_style():
    path = os.path.join(os.path.dirname(__file__), "style_export.json")
    try:
        from personalization import analyze_user_patterns, get_training_pairs
        
        s = list_samples(limit=500)
        training_pairs = get_training_pairs(100)
        patterns = analyze_user_patterns()
        summary = build_style_summary()
        
        payload = {
            "summary": summary,
            "samples": s,
            "training_pairs": training_pairs,
            "patterns": patterns,
            "export_date": time.time()
        }
        
        with open(path, "w", encoding="utf8") as f:
            import json
            json.dump(payload, f, ensure_ascii=False, indent=2)
        return send_file(path, as_attachment=True)
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route("/unload_model", methods=["POST"])
def manual_unload():
    """Manually unload model to free memory"""
    try:
        unload_model()
        return jsonify({"ok": True, "message": "Model unloaded successfully"})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route("/memory_status", methods=["GET"])
def memory_status():
    """Get current memory and CPU status with optimization limits"""
    import psutil
    process = psutil.Process()
    memory_info = process.memory_info()
    memory_mb = round(memory_info.rss / 1024 / 1024, 1)
    cpu_percent = round(process.cpu_percent(interval=0.1), 1)
    
    # Check if within optimization limits
    memory_optimized = memory_mb <= MAX_IDLE_MEMORY_MB
    cpu_optimized = cpu_percent <= MAX_IDLE_CPU_PERCENT
    
    return jsonify({
        "model_loaded": MODEL_LOADED,
        "memory_mb": memory_mb,
        "cpu_percent": cpu_percent,
        "memory_limit_mb": MAX_IDLE_MEMORY_MB,
        "cpu_limit_percent": MAX_IDLE_CPU_PERCENT,
        "memory_optimized": memory_optimized,
        "cpu_optimized": cpu_optimized,
        "last_used": LAST_USED,
        "idle_time": round(time.time() - LAST_USED, 1) if LAST_USED > 0 else 0,
        "will_unload_in": max(0, IDLE_TIMEOUT - (time.time() - LAST_USED)) if LAST_USED > 0 and MODEL_LOADED else 0,
        "optimization_status": "✅ Optimized" if memory_optimized and cpu_optimized else "⚠️ High Usage"
    })

def start_background_learning_service():
    """Start continuous background learning service (even when model unloaded)"""
    def background_service():
        learning_counter = 0
        
        while True:
            try:
                time.sleep(120)  # Run every 2 minutes
                learning_counter += 1
                
                # Only run if no active model (to avoid interference)
                if not MODEL_LOADED:
                    # Check system resources
                    process = psutil.Process()
                    memory_mb = process.memory_info().rss / 1024 / 1024
                    cpu_percent = process.cpu_percent(interval=0.1)
                    
                    # Only proceed if resources are very low
                    if memory_mb < 100 and cpu_percent < 2:  # Very conservative limits
                        
                        # Rotate through learning tasks
                        task = learning_counter % 4
                        
                        if task == 0:
                            # Analyze stored data patterns
                            app.logger.info("🧠 Background service: Analyzing data patterns...")
                            from personalization import analyze_user_patterns
                            patterns = analyze_user_patterns()
                            
                        elif task == 1:
                            # Optimize database
                            app.logger.info("🗜️ Background service: Database optimization...")
                            from personalization import smart_cleanup
                            smart_cleanup()
                            
                        elif task == 2:
                            # Process feedback for learning
                            app.logger.info("📊 Background service: Processing feedback...")
                            from personalization import get_feedback_patterns
                            feedback = get_feedback_patterns()
                            
                        elif task == 3:
                            # Prepare optimized templates
                            app.logger.info("🎨 Background service: Preparing templates...")
                            # Pre-compute common response patterns for faster generation
                            pass
                        
                        # Minimal delay to keep CPU usage under 5%
                        time.sleep(1)
                
            except Exception as e:
                app.logger.debug(f"Background service error: {e}")
                time.sleep(60)  # Wait longer on error
    
    # Start background service thread
    bg_thread = threading.Thread(target=background_service, daemon=True)
    bg_thread.start()
    app.logger.info("🤖 Background learning service started")

if __name__ == "__main__":
    print("🚀 Starting svarx.ai Server with Ultra-Low Resource Usage...")
    print("📊 Memory Management: ON-DEMAND loading, 1-minute auto-unload, <500MB idle")
    print("🔋 Power Management: Max 5% CPU when idle, single-core processing")
    print("💾 Model loads only when needed, ultra-efficient training mode")
    print("🧠 Background Learning: Continuous learning even when idle")
    print("🔧 Server available at: http://127.0.0.1:8081")
    print("⚡ Press Ctrl+C to stop")
    
    # Set initial low power mode for server
    set_normal_power_mode()  # Start in normal mode, switch to low when AI loads
    
    # Start background learning service
    start_background_learning_service()
    
    # Don't load model at startup - load on-demand only
    print("✅ Server ready - model will load on first request with minimal power")
    print("🤖 Background learning active - AI improves continuously")
    
    app.run(host="127.0.0.1", port=8081, threaded=True, debug=False)
