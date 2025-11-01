# personalization.py
import sqlite3, re, json, time, threading
from pathlib import Path
from collections import Counter
import hashlib

BASE = Path(__file__).resolve().parent
DB_PATH = BASE / "personalization.db"

# Extensive Learning Limits with 10GB Storage
MAX_SAMPLES = 50000         # Massive learning capacity
MAX_TRAINING_PAIRS = 25000  # Extensive training data
MAX_INTERACTIONS = 100000   # Comprehensive user feedback
MAX_EMAIL_PATTERNS = 10000  # Deep email pattern analysis
MAX_DB_SIZE_MB = 5120       # 5GB for optimal learning capacity

lock = threading.Lock()

CREATE_SQL = """
CREATE TABLE IF NOT EXISTS samples (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at INTEGER,
    text TEXT
);

CREATE TABLE IF NOT EXISTS training_pairs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at INTEGER,
    original_email TEXT,
    chosen_reply TEXT,
    tone TEXT,
    length TEXT,
    user_rating INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS model_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at INTEGER,
    version_name TEXT,
    model_path TEXT,
    training_samples INTEGER,
    performance_score REAL
);

CREATE TABLE IF NOT EXISTS interaction_feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at INTEGER,
    interaction_type TEXT,
    original_email TEXT,
    suggestion TEXT,
    feedback TEXT,
    weight REAL,
    context TEXT
);
"""

def _connect():
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    return conn

with lock:
    conn = _connect()
    conn.executescript(CREATE_SQL)
    conn.commit()
    conn.close()

def sanitize_text(s: str) -> str:
    s = s.strip()
    s = re.sub(r">.*?$", "", s, flags=re.MULTILINE)
    s = re.sub(r"\s+", " ", s)
    return s.strip()

def get_text_hash(text: str) -> str:
    """Generate hash for duplicate detection"""
    return hashlib.md5(text.encode()).hexdigest()[:16]

def get_db_size_mb() -> float:
    """Get current database size in MB"""
    try:
        return DB_PATH.stat().st_size / (1024 * 1024)
    except:
        return 0.0

def smart_cleanup():
    """Intelligent cleanup to maintain storage limits - Enhanced Version"""
    with lock:
        conn = _connect()
        cur = conn.cursor()
        
        print("🧹 Starting intelligent storage cleanup...")
        
        # 1. Remove exact duplicates first
        cur.execute("""
            DELETE FROM samples WHERE id NOT IN (
                SELECT MIN(id) FROM samples GROUP BY text
            )
        """)
        duplicates_removed = cur.rowcount
        
        cur.execute("""
            DELETE FROM training_pairs WHERE id NOT IN (
                SELECT MIN(id) FROM training_pairs 
                GROUP BY original_email, chosen_reply
            )
        """)
        
        # 2. Remove old negative feedback (keep positive feedback longer)
        old_threshold = int(time.time()) - 30*24*3600  # 30 days
        cur.execute("""
            DELETE FROM interaction_feedback 
            WHERE feedback = 'negative' AND created_at < ?
        """, (old_threshold,))
        
        # 3. Compress old data by keeping only the best examples
        # Keep samples with diverse vocabulary (avoid repetitive content)
        cur.execute("SELECT COUNT(*) FROM samples")
        sample_count = cur.fetchone()[0]
        
        if sample_count > MAX_SAMPLES:
            # Keep 80% most recent + 20% highest quality older samples
            recent_limit = int(MAX_SAMPLES * 0.8)
            quality_limit = int(MAX_SAMPLES * 0.2)
            
            # Keep most recent samples
            cur.execute("""
                CREATE TEMP TABLE keep_samples AS
                SELECT id FROM samples ORDER BY created_at DESC LIMIT ?
            """, (recent_limit,))
            
            # Add quality older samples (longer, more diverse text)
            cur.execute("""
                INSERT INTO keep_samples 
                SELECT id FROM samples 
                WHERE id NOT IN (SELECT id FROM keep_samples)
                AND LENGTH(text) > 50
                ORDER BY LENGTH(text) DESC, created_at DESC 
                LIMIT ?
            """, (quality_limit,))
            
            # Remove samples not in keep list
            cur.execute("DELETE FROM samples WHERE id NOT IN (SELECT id FROM keep_samples)")
            cur.execute("DROP TABLE keep_samples")
        
        # 4. Smart training pair management
        cur.execute("SELECT COUNT(*) FROM training_pairs")
        pair_count = cur.fetchone()[0]
        
        if pair_count > MAX_TRAINING_PAIRS:
            # Prioritize: Recent + High ratings + Diverse tones
            cur.execute("""
                DELETE FROM training_pairs WHERE id NOT IN (
                    SELECT id FROM (
                        -- Recent pairs (70%)
                        SELECT id FROM training_pairs 
                        ORDER BY created_at DESC 
                        LIMIT ?
                        
                        UNION
                        
                        -- High-rated diverse pairs (30%)
                        SELECT id FROM training_pairs 
                        WHERE user_rating >= 4
                        ORDER BY user_rating DESC, created_at DESC
                        LIMIT ?
                    )
                )
            """, (int(MAX_TRAINING_PAIRS * 0.7), int(MAX_TRAINING_PAIRS * 0.3)))
        
        # 5. Keep only valuable interactions (weighted by importance)
        cur.execute("SELECT COUNT(*) FROM interaction_feedback")
        interaction_count = cur.fetchone()[0]
        
        if interaction_count > MAX_INTERACTIONS:
            cur.execute("""
                DELETE FROM interaction_feedback WHERE id NOT IN (
                    SELECT id FROM interaction_feedback 
                    WHERE weight > 0.5 OR feedback = 'selected'
                    ORDER BY weight DESC, created_at DESC 
                    LIMIT ?
                )
            """, (MAX_INTERACTIONS,))
        
        # 6. Clean up email patterns (keep only recent diverse patterns)
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='email_patterns'")
        if cur.fetchone():
            cur.execute("SELECT COUNT(*) FROM email_patterns")
            pattern_count = cur.fetchone()[0]
            
            if pattern_count > MAX_EMAIL_PATTERNS:
                cur.execute("""
                    DELETE FROM email_patterns WHERE id NOT IN (
                        SELECT id FROM email_patterns 
                        ORDER BY created_at DESC 
                        LIMIT ?
                    )
                """, (MAX_EMAIL_PATTERNS,))
        
        # 7. Vacuum database to reclaim space
        cur.execute("VACUUM")
        
        conn.commit()
        
        # Check final size
        final_size = get_db_size_mb()
        print(f"✅ Cleanup complete! Database size: {final_size:.1f}MB")
        print(f"   Removed {duplicates_removed} duplicate samples")
        
        conn.close()
        
        return final_size

def compress_old_data():
    """Compress older data into summary patterns"""
    with lock:
        conn = _connect()
        cur = conn.cursor()
        
        # Get old training pairs (older than 30 days)
        old_threshold = int(time.time()) - 30*24*3600
        cur.execute("""
            SELECT tone, length, COUNT(*) as count 
            FROM training_pairs 
            WHERE created_at < ? 
            GROUP BY tone, length
        """, (old_threshold,))
        
        old_patterns = cur.fetchall()
        
        # Store compressed patterns (if we had a patterns table)
        # For now, just remove old data
        cur.execute("DELETE FROM training_pairs WHERE created_at < ?", (old_threshold,))
        
        conn.commit()
        conn.close()
        
        return len(old_patterns)

def check_storage_and_cleanup():
    """Check storage usage and perform cleanup if needed"""
    current_size = get_db_size_mb()
    
    if current_size > MAX_DB_SIZE_MB:
        print(f"⚠️  Storage limit reached: {current_size:.1f}MB / {MAX_DB_SIZE_MB}MB")
        print("🔄 Starting automatic cleanup to free space...")
        
        final_size = smart_cleanup()
        
        if final_size > MAX_DB_SIZE_MB * 0.9:  # Still over 90% capacity
            print("🗂️  Performing deep cleanup...")
            deep_cleanup()
        
        return True
    
    return False

def deep_cleanup():
    """Aggressive cleanup when storage is critically full"""
    with lock:
        conn = _connect()
        cur = conn.cursor()
        
        print("🔥 Performing deep storage cleanup...")
        
        # Keep only 50% of current limits for emergency space
        emergency_samples = MAX_SAMPLES // 2
        emergency_pairs = MAX_TRAINING_PAIRS // 2
        emergency_interactions = MAX_INTERACTIONS // 2
        
        # Keep only the most valuable data
        cur.execute("""
            DELETE FROM samples WHERE id NOT IN (
                SELECT id FROM samples 
                WHERE LENGTH(text) > 30
                ORDER BY created_at DESC 
                LIMIT ?
            )
        """, (emergency_samples,))
        
        cur.execute("""
            DELETE FROM training_pairs WHERE id NOT IN (
                SELECT id FROM training_pairs 
                WHERE user_rating > 0 OR created_at > ?
                ORDER BY user_rating DESC, created_at DESC 
                LIMIT ?
            )
        """, (int(time.time()) - 7*24*3600, emergency_pairs))  # Last 7 days or rated
        
        cur.execute("""
            DELETE FROM interaction_feedback WHERE id NOT IN (
                SELECT id FROM interaction_feedback 
                WHERE weight > 0.7 OR feedback = 'selected'
                ORDER BY weight DESC 
                LIMIT ?
            )
        """, (emergency_interactions,))
        
        # Remove old email patterns completely
        cur.execute("DROP TABLE IF EXISTS email_patterns")
        
        cur.execute("VACUUM")
        conn.commit()
        
        final_size = get_db_size_mb()
        print(f"🎯 Deep cleanup complete! Size reduced to {final_size:.1f}MB")
        
        conn.close()

def add_sample(text: str):
    text = sanitize_text(text)
    if not text or len(text) < 10:  # Skip very short texts
        return False
    
    # Check storage before adding
    check_storage_and_cleanup()
    
    text_hash = get_text_hash(text)
    ts = int(time.time())
    
    with lock:
        conn = _connect()
        cur = conn.cursor()
        
        # Check for duplicates
        cur.execute("SELECT id FROM samples WHERE text = ?", (text,))
        if cur.fetchone():
            conn.close()
            return False  # Skip duplicates
        
        # Add new sample
        cur.execute("INSERT INTO samples (created_at, text) VALUES (?,?)", (ts, text))
        
        conn.commit()
        conn.close()
    return True

def list_samples(limit=50):
    with lock:
        conn = _connect()
        cur = conn.cursor()
        cur.execute("SELECT id, created_at, text FROM samples ORDER BY created_at DESC LIMIT ?", (limit,))
        rows = cur.fetchall()
        conn.close()
    return [{"id": r[0], "created_at": r[1], "text": r[2]} for r in rows]

def clear_samples():
    with lock:
        conn = _connect()
        cur = conn.cursor()
        cur.execute("DELETE FROM samples")
        cur.execute("DELETE FROM training_pairs")
        conn.commit()
        conn.close()

def get_storage_status():
    """Get detailed storage status"""
    current_size = get_db_size_mb()
    usage_percent = (current_size / MAX_DB_SIZE_MB) * 100
    
    with lock:
        conn = _connect()
        cur = conn.cursor()
        
        # Count records in each table
        cur.execute("SELECT COUNT(*) FROM samples")
        sample_count = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM training_pairs")
        pair_count = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM interaction_feedback")
        feedback_count = cur.fetchone()[0]
        
        conn.close()
    
    return {
        "size_mb": current_size,
        "max_size_mb": MAX_DB_SIZE_MB,
        "usage_percent": usage_percent,
        "samples": sample_count,
        "training_pairs": pair_count,
        "interactions": feedback_count,
        "status": "critical" if usage_percent > 95 else "warning" if usage_percent > 80 else "healthy"
    }

def add_training_pair(original_email: str, chosen_reply: str, context: dict):
    """Add a training pair with smart deduplication"""
    original_email = sanitize_text(original_email)
    chosen_reply = sanitize_text(chosen_reply)
    
    if not original_email or not chosen_reply:
        return False
    
    # Skip if too short or too similar to existing
    if len(original_email) < 20 or len(chosen_reply) < 10:
        return False
    
    # Check storage before adding
    check_storage_and_cleanup()
    
    ts = int(time.time())
    tone = context.get('tone', 'professional')
    length = context.get('length', 'medium')
    
    with lock:
        conn = _connect()
        cur = conn.cursor()
        
        # Check for similar pairs (avoid near-duplicates)
        cur.execute("""
            SELECT id FROM training_pairs 
            WHERE original_email = ? OR chosen_reply = ?
        """, (original_email, chosen_reply))
        
        if cur.fetchone():
            conn.close()
            return False  # Skip duplicates
        
        # Add new pair
        cur.execute(
            "INSERT INTO training_pairs (created_at, original_email, chosen_reply, tone, length) VALUES (?,?,?,?,?)",
            (ts, original_email, chosen_reply, tone, length)
        )
        
        conn.commit()
        conn.close()
    return True

def get_training_pairs(limit=50):
    """Get recent training pairs for analysis"""
    with lock:
        conn = _connect()
        cur = conn.cursor()
        cur.execute("SELECT original_email, chosen_reply, tone, length FROM training_pairs ORDER BY created_at DESC LIMIT ?", (limit,))
        rows = cur.fetchall()
        conn.close()
    return [{"original": r[0], "reply": r[1], "tone": r[2], "length": r[3]} for r in rows]

def add_interaction_feedback(learning_data: dict, weight: float = 1.0):
    """Store user interaction feedback with smart filtering"""
    ts = int(time.time())
    
    # Only store valuable feedback
    if weight < 0 and abs(weight) < 0.3:  # Skip weak negative feedback
        return False
    
    # Check storage before adding
    check_storage_and_cleanup()
    
    with lock:
        conn = _connect()
        cur = conn.cursor()
        
        # Compress context to save space
        context = learning_data.get("context", {})
        compressed_context = json.dumps({
            "tone": context.get("tone", "professional"),
            "length": context.get("length", "medium")
        })
        
        cur.execute(
            "INSERT INTO interaction_feedback (created_at, interaction_type, original_email, suggestion, feedback, weight, context) VALUES (?,?,?,?,?,?,?)",
            (ts, learning_data["interaction_type"], learning_data["original_email"][:200],  # Limit email length
             learning_data["suggestion"][:200], learning_data["feedback"], weight,  # Limit suggestion length
             compressed_context)
        )
        
        conn.commit()
        conn.close()
    return True

def get_feedback_patterns():
    """Analyze user feedback patterns for learning"""
    with lock:
        conn = _connect()
        cur = conn.cursor()
        cur.execute("SELECT interaction_type, feedback, weight, suggestion, context FROM interaction_feedback ORDER BY created_at DESC LIMIT 100")
        rows = cur.fetchall()
        conn.close()
    
    patterns = {
        "positive_patterns": [],
        "negative_patterns": [],
        "preferred_styles": {},
        "avoided_styles": {}
    }
    
    for row in rows:
        interaction_type, feedback, weight, suggestion, context_json = row
        try:
            context = json.loads(context_json) if context_json else {}
        except:
            context = {}
        
        if weight > 0:  # Positive feedback
            patterns["positive_patterns"].append({
                "suggestion": suggestion[:50] + "...",
                "tone": context.get("tone", "unknown"),
                "weight": weight
            })
        elif weight < 0:  # Negative feedback
            patterns["negative_patterns"].append({
                "suggestion": suggestion[:50] + "...",
                "tone": context.get("tone", "unknown"),
                "weight": abs(weight)
            })
    
    return patterns

def extract_top_phrases(top_k=12):
    with lock:
        conn = _connect()
        cur = conn.cursor()
        cur.execute("SELECT text FROM samples")
        rows = cur.fetchall()
        conn.close()
    tokens = []
    for r in rows:
        txt = sanitize_text(r[0])
        tokens.extend(re.findall(r"\b\w+\b", txt.lower()))
    if not tokens: return []
    uni = Counter(tokens)
    bigrams = Counter()
    for i in range(len(tokens)-1):
        bigrams[" ".join(tokens[i:i+2])] += 1
    top_uni = [w for w,_ in uni.most_common(10)]
    top_bi = [w for w,_ in bigrams.most_common(10)]
    phrases = []
    for p in top_bi + top_uni:
        if len(phrases) >= top_k: break
        phrases.append(p)
    return phrases

def analyze_user_patterns():
    """Lightweight analysis of user communication patterns"""
    training_pairs = get_training_pairs(50)
    samples = list_samples(limit=100)
    
    if not training_pairs and not samples:
        return {}
    
    patterns = {
        "preferred_tone": "professional",
        "avg_length": 20,
        "common_phrases": [],
        "response_style": "balanced",
        "formality_level": 0.5
    }
    
    # Analyze training pairs for response patterns
    if training_pairs:
        tone_counts = Counter(pair["tone"] for pair in training_pairs)
        patterns["preferred_tone"] = tone_counts.most_common(1)[0][0] if tone_counts else "professional"
        
        # Analyze response lengths
        reply_lengths = [len(pair["reply"].split()) for pair in training_pairs]
        patterns["avg_length"] = int(sum(reply_lengths) / len(reply_lengths)) if reply_lengths else 20
        
        # Find common response starters
        starters = [pair["reply"].split()[:3] for pair in training_pairs if len(pair["reply"].split()) >= 3]
        starter_phrases = [" ".join(starter) for starter in starters]
        patterns["common_starters"] = Counter(starter_phrases).most_common(3)
    
    # Analyze formality from samples
    if samples:
        formal_indicators = ["regards", "sincerely", "please", "kindly", "thank you", "best"]
        casual_indicators = ["thanks", "hey", "sure", "ok", "cool", "awesome"]
        
        formal_count = sum(1 for s in samples for indicator in formal_indicators 
                          if indicator in s["text"].lower())
        casual_count = sum(1 for s in samples for indicator in casual_indicators 
                          if indicator in s["text"].lower())
        
        total_indicators = formal_count + casual_count
        patterns["formality_level"] = formal_count / max(1, total_indicators)
    
    return patterns

def build_style_summary(max_len=300):
    """Enhanced style summary with pattern analysis"""
    patterns = analyze_user_patterns()
    samples = list_samples(limit=50)
    
    if not patterns and not samples:
        return ""
    
    # Build intelligent summary
    tone = patterns.get("preferred_tone", "professional")
    avg_len = patterns.get("avg_length", 20)
    formality = patterns.get("formality_level", 0.5)
    
    style_desc = "formal" if formality > 0.6 else "casual" if formality < 0.3 else "balanced"
    
    summary = f"User prefers {tone} tone, {style_desc} style (~{avg_len} words)."
    
    # Add common phrases if available
    phrases = extract_top_phrases(5)
    if phrases:
        summary += f" Common phrases: {', '.join(phrases[:3])}."
    
    # Add response patterns
    if "common_starters" in patterns and patterns["common_starters"]:
        top_starter = patterns["common_starters"][0][0]
        summary += f" Often starts with: '{top_starter}'."
    
    return summary[:max_len]
def analyze_and_learn_from_email(email_text: str, tone: str, length: str):
    """Learn patterns from incoming emails (passive learning)"""
    if not email_text or len(email_text) < 20:
        return False
    
    email_text = sanitize_text(email_text)
    ts = int(time.time())
    
    # Extract email patterns
    patterns = {
        "sender_style": "unknown",
        "email_type": "general",
        "urgency": "normal",
        "formality": "medium"
    }
    
    text_lower = email_text.lower()
    
    # Detect email type
    if any(word in text_lower for word in ["meeting", "schedule", "calendar", "appointment"]):
        patterns["email_type"] = "scheduling"
    elif any(word in text_lower for word in ["thank", "appreciate", "grateful"]):
        patterns["email_type"] = "gratitude"
    elif any(word in text_lower for word in ["urgent", "asap", "immediate", "priority"]):
        patterns["email_type"] = "urgent"
        patterns["urgency"] = "high"
    elif any(word in text_lower for word in ["question", "help", "clarify", "explain"]):
        patterns["email_type"] = "inquiry"
    elif any(word in text_lower for word in ["update", "status", "progress", "report"]):
        patterns["email_type"] = "update_request"
    
    # Detect formality level
    formal_indicators = ["dear", "sincerely", "regards", "please", "kindly", "would you"]
    casual_indicators = ["hey", "hi", "thanks", "sure", "ok", "cool"]
    
    formal_count = sum(1 for word in formal_indicators if word in text_lower)
    casual_count = sum(1 for word in casual_indicators if word in text_lower)
    
    if formal_count > casual_count:
        patterns["formality"] = "high"
    elif casual_count > formal_count:
        patterns["formality"] = "low"
    
    # Store email pattern for learning
    with lock:
        conn = _connect()
        cur = conn.cursor()
        
        # Create email_patterns table if not exists
        cur.execute("""
            CREATE TABLE IF NOT EXISTS email_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at INTEGER,
                email_snippet TEXT,
                email_type TEXT,
                formality TEXT,
                urgency TEXT,
                word_count INTEGER
            )
        """)
        
        # Store pattern
        cur.execute("""
            INSERT INTO email_patterns (created_at, email_snippet, email_type, formality, urgency, word_count)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (ts, email_text[:200], patterns["email_type"], patterns["formality"], 
              patterns["urgency"], len(email_text.split())))
        
        # Keep only recent 100 email patterns
        cur.execute("SELECT COUNT(*) FROM email_patterns")
        count = cur.fetchone()[0]
        if count > 100:
            cur.execute("""
                DELETE FROM email_patterns WHERE id IN (
                    SELECT id FROM email_patterns ORDER BY created_at ASC LIMIT ?
                )
            """, (count - 100,))
        
        conn.commit()
        conn.close()
    
    return True

def get_email_context_insights():
    """Get insights from analyzed email patterns"""
    with lock:
        conn = _connect()
        cur = conn.cursor()
        
        # Check if table exists
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='email_patterns'")
        if not cur.fetchone():
            conn.close()
            return {}
        
        cur.execute("""
            SELECT email_type, formality, urgency, COUNT(*) as count
            FROM email_patterns 
            WHERE created_at > ? 
            GROUP BY email_type, formality, urgency
            ORDER BY count DESC
        """, (int(time.time()) - 30*24*3600,))  # Last 30 days
        
        rows = cur.fetchall()
        conn.close()
    
    insights = {
        "common_email_types": {},
        "typical_formality": "medium",
        "urgency_patterns": {}
    }
    
    if rows:
        # Analyze most common patterns
        for email_type, formality, urgency, count in rows:
            if email_type not in insights["common_email_types"]:
                insights["common_email_types"][email_type] = 0
            insights["common_email_types"][email_type] += count
            
            if urgency not in insights["urgency_patterns"]:
                insights["urgency_patterns"][urgency] = 0
            insights["urgency_patterns"][urgency] += count
    
    return insights