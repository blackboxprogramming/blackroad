"""
Customer Onboarding Service
Multi-step signup flow with email verification, welcome sequence, and success tracking.
"""

import os
import json
import uuid
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from enum import Enum
import logging

# Email
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Database
import psycopg2
from psycopg2.extras import Json, RealDictCursor
import psycopg2.pool

# Flask
from flask import Flask, request, jsonify
from functools import wraps

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://blackroad:dev-password@localhost:5432/blackroad_dev")
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "dev-admin-token-change-in-prod")
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.sendgrid.net")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "apikey")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "SG.fake_key")
SEND_EMAILS = os.getenv("SEND_EMAILS", "false").lower() == "true"

# ==============================================================================
# DATA MODELS
# ==============================================================================

class OnboardingStep(Enum):
    """Onboarding steps"""
    SIGNUP = "signup"
    EMAIL_VERIFICATION = "email_verification"
    PROFILE = "profile"
    PLAN_SELECTION = "plan_selection"
    PAYMENT = "payment"
    FIRST_API_KEY = "first_api_key"
    FIRST_REQUEST = "first_request"
    COMPLETED = "completed"

class OnboardingTier(Enum):
    """Available tiers"""
    FREE = "free"
    STARTER = "starter"
    PRO = "pro"
    ENTERPRISE = "enterprise"

# ==============================================================================
# DATABASE
# ==============================================================================

class OnboardingDatabase:
    """Database operations for onboarding"""
    
    def __init__(self, connection_string: str):
        self.pool = psycopg2.pool.SimpleConnectionPool(1, 10, connection_string)
        self._init_tables()
    
    def _init_tables(self):
        """Initialize onboarding tables"""
        conn = self.pool.getconn()
        try:
            with conn.cursor() as cur:
                # Onboarding profiles
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS onboarding_profiles (
                        id TEXT PRIMARY KEY,
                        email TEXT UNIQUE NOT NULL,
                        user_id TEXT,
                        first_name TEXT,
                        last_name TEXT,
                        company TEXT,
                        tier TEXT DEFAULT 'free',
                        current_step TEXT DEFAULT 'signup',
                        progress INT DEFAULT 0,
                        started_at TIMESTAMP DEFAULT NOW(),
                        completed_at TIMESTAMP,
                        email_verified BOOLEAN DEFAULT FALSE,
                        email_verified_at TIMESTAMP,
                        welcome_email_sent BOOLEAN DEFAULT FALSE,
                        onboarding_email_1_sent BOOLEAN DEFAULT FALSE,
                        onboarding_email_2_sent BOOLEAN DEFAULT FALSE,
                        onboarding_email_3_sent BOOLEAN DEFAULT FALSE,
                        metadata JSONB,
                        created_at TIMESTAMP DEFAULT NOW(),
                        updated_at TIMESTAMP DEFAULT NOW()
                    );
                    CREATE INDEX IF NOT EXISTS idx_onboard_email ON onboarding_profiles(email);
                    CREATE INDEX IF NOT EXISTS idx_onboard_step ON onboarding_profiles(current_step);
                    CREATE INDEX IF NOT EXISTS idx_onboard_completed ON onboarding_profiles(completed_at);
                """)
                
                # Email verification tokens
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS email_verification_tokens (
                        id TEXT PRIMARY KEY,
                        onboarding_id TEXT NOT NULL,
                        token TEXT UNIQUE NOT NULL,
                        email TEXT NOT NULL,
                        expires_at TIMESTAMP NOT NULL,
                        used_at TIMESTAMP,
                        created_at TIMESTAMP DEFAULT NOW(),
                        FOREIGN KEY (onboarding_id) REFERENCES onboarding_profiles(id)
                    );
                    CREATE INDEX IF NOT EXISTS idx_verify_token ON email_verification_tokens(token);
                    CREATE INDEX IF NOT EXISTS idx_verify_expires ON email_verification_tokens(expires_at);
                """)
                
                # Onboarding steps completion tracking
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS onboarding_steps (
                        id TEXT PRIMARY KEY,
                        onboarding_id TEXT NOT NULL,
                        step TEXT NOT NULL,
                        completed_at TIMESTAMP,
                        data JSONB,
                        created_at TIMESTAMP DEFAULT NOW(),
                        FOREIGN KEY (onboarding_id) REFERENCES onboarding_profiles(id),
                        UNIQUE(onboarding_id, step)
                    );
                    CREATE INDEX IF NOT EXISTS idx_steps_onboard ON onboarding_steps(onboarding_id);
                """)
                
                # Onboarding resources (tutorials, docs)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS onboarding_resources (
                        id TEXT PRIMARY KEY,
                        title TEXT NOT NULL,
                        description TEXT,
                        type TEXT,
                        url TEXT,
                        step TEXT,
                        order_index INT,
                        created_at TIMESTAMP DEFAULT NOW()
                    );
                """)
                
                # Onboarding analytics
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS onboarding_analytics (
                        date DATE DEFAULT CURRENT_DATE,
                        started INT DEFAULT 0,
                        verified INT DEFAULT 0,
                        completed INT DEFAULT 0,
                        avg_duration_hours DECIMAL,
                        PRIMARY KEY (date)
                    );
                """)
                
                conn.commit()
                logger.info("✅ Onboarding tables initialized")
        except Exception as e:
            logger.error(f"❌ Failed to init tables: {e}")
            conn.rollback()
        finally:
            self.pool.putconn(conn)
    
    def create_profile(self, email: str, first_name: str, last_name: str, 
                      company: str = None) -> Optional[str]:
        """Create new onboarding profile"""
        conn = self.pool.getconn()
        try:
            profile_id = str(uuid.uuid4())
            
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO onboarding_profiles (
                        id, email, first_name, last_name, company, current_step, metadata
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    profile_id, email.lower(), first_name, last_name, company,
                    OnboardingStep.SIGNUP.value,
                    Json({"signup_source": "web", "ip_country": "US"})
                ))
                conn.commit()
                return profile_id
        except psycopg2.IntegrityError:
            logger.warning(f"⚠️  Email already exists: {email}")
            conn.rollback()
            return None
        except Exception as e:
            logger.error(f"❌ Failed to create profile: {e}")
            conn.rollback()
            return None
        finally:
            self.pool.putconn(conn)
    
    def get_profile(self, onboarding_id: str) -> Optional[Dict]:
        """Get onboarding profile"""
        conn = self.pool.getconn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM onboarding_profiles WHERE id = %s
                """, (onboarding_id,))
                return cur.fetchone()
        except Exception as e:
            logger.error(f"❌ Failed to get profile: {e}")
            return None
        finally:
            self.pool.putconn(conn)
    
    def get_profile_by_email(self, email: str) -> Optional[Dict]:
        """Get profile by email"""
        conn = self.pool.getconn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM onboarding_profiles WHERE email = %s
                """, (email.lower(),))
                return cur.fetchone()
        except Exception as e:
            logger.error(f"❌ Failed to get profile by email: {e}")
            return None
        finally:
            self.pool.putconn(conn)
    
    def create_verification_token(self, onboarding_id: str, email: str) -> str:
        """Create email verification token"""
        conn = self.pool.getconn()
        try:
            token_id = str(uuid.uuid4())
            token = secrets.token_urlsafe(32)
            expires_at = datetime.now() + timedelta(hours=24)
            
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO email_verification_tokens (
                        id, onboarding_id, token, email, expires_at
                    ) VALUES (%s, %s, %s, %s, %s)
                """, (token_id, onboarding_id, token, email, expires_at))
                conn.commit()
                return token
        except Exception as e:
            logger.error(f"❌ Failed to create token: {e}")
            conn.rollback()
            return None
        finally:
            self.pool.putconn(conn)
    
    def verify_email_token(self, token: str) -> Optional[Tuple[str, str]]:
        """Verify email token, return (onboarding_id, email)"""
        conn = self.pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT onboarding_id, email FROM email_verification_tokens
                    WHERE token = %s AND expires_at > NOW() AND used_at IS NULL
                """, (token,))
                result = cur.fetchone()
                
                if result:
                    onboarding_id, email = result
                    # Mark as used
                    cur.execute("""
                        UPDATE email_verification_tokens SET used_at = NOW() WHERE token = %s
                    """, (token,))
                    
                    # Update profile
                    cur.execute("""
                        UPDATE onboarding_profiles SET
                            email_verified = TRUE,
                            email_verified_at = NOW(),
                            current_step = %s,
                            progress = 25
                        WHERE id = %s
                    """, (OnboardingStep.EMAIL_VERIFICATION.value, onboarding_id))
                    
                    conn.commit()
                    return onboarding_id, email
                else:
                    return None
        except Exception as e:
            logger.error(f"❌ Failed to verify token: {e}")
            conn.rollback()
            return None
        finally:
            self.pool.putconn(conn)
    
    def update_step(self, onboarding_id: str, step: str, progress: int,
                   data: Dict = None) -> bool:
        """Update onboarding step"""
        conn = self.pool.getconn()
        try:
            with conn.cursor() as cur:
                # Update profile
                completed_at = datetime.now() if progress >= 100 else None
                
                cur.execute("""
                    UPDATE onboarding_profiles SET
                        current_step = %s,
                        progress = %s,
                        completed_at = %s,
                        updated_at = NOW()
                    WHERE id = %s
                """, (step, progress, completed_at, onboarding_id))
                
                # Record step completion
                step_id = str(uuid.uuid4())
                cur.execute("""
                    INSERT INTO onboarding_steps (id, onboarding_id, step, data, completed_at)
                    VALUES (%s, %s, %s, %s, NOW())
                    ON CONFLICT (onboarding_id, step) DO UPDATE SET
                        completed_at = NOW(),
                        data = EXCLUDED.data
                """, (step_id, onboarding_id, step, Json(data or {})))
                
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"❌ Failed to update step: {e}")
            conn.rollback()
            return False
        finally:
            self.pool.putconn(conn)
    
    def get_analytics(self, days: int = 30) -> Dict:
        """Get onboarding analytics"""
        conn = self.pool.getconn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Recent signups
                cur.execute("""
                    SELECT COUNT(*) as total, 
                           COUNT(CASE WHEN email_verified THEN 1 END) as verified,
                           COUNT(CASE WHEN completed_at IS NOT NULL THEN 1 END) as completed
                    FROM onboarding_profiles
                    WHERE created_at > NOW() - INTERVAL '%s days'
                """, (days,))
                
                stats = cur.fetchone()
                
                # Conversion rates
                total = stats['total'] or 1
                verified_rate = (stats['verified'] / total * 100) if total > 0 else 0
                completion_rate = (stats['completed'] / total * 100) if total > 0 else 0
                
                return {
                    "period_days": days,
                    "signups": stats['total'],
                    "verified_emails": stats['verified'],
                    "completed": stats['completed'],
                    "verification_rate": round(verified_rate, 1),
                    "completion_rate": round(completion_rate, 1)
                }
        except Exception as e:
            logger.error(f"❌ Failed to get analytics: {e}")
            return {}
        finally:
            self.pool.putconn(conn)

# ==============================================================================
# EMAIL SERVICE
# ==============================================================================

class OnboardingEmailService:
    """Send onboarding emails"""
    
    @staticmethod
    def send_verification_email(email: str, token: str, first_name: str) -> bool:
        """Send email verification link"""
        try:
            if not SEND_EMAILS:
                logger.info(f"📧 [DRY RUN] Verification email to {email} (token: {token[:10]}...)")
                return True
            
            subject = "Verify Your Email - Welcome to BlackRoad"
            
            verify_link = f"https://app.blackroad.io/onboarding/verify?token={token}"
            
            body = f"""
            <h2>Welcome, {first_name}!</h2>
            
            <p>Thanks for signing up to BlackRoad. Click the link below to verify your email:</p>
            
            <p><a href="{verify_link}" style="background: #007bff; color: white; padding: 12px 30px; text-decoration: none; border-radius: 4px;">Verify Email</a></p>
            
            <p>Or copy this link: {verify_link}</p>
            
            <p>This link expires in 24 hours.</p>
            
            <p>Questions? <a href="https://support.blackroad.io">Contact support</a></p>
            """
            
            return OnboardingEmailService._send_email(email, subject, body)
        except Exception as e:
            logger.error(f"❌ Failed to send verification email: {e}")
            return False
    
    @staticmethod
    def send_welcome_email(email: str, first_name: str, tier: str) -> bool:
        """Send welcome email"""
        try:
            if not SEND_EMAILS:
                logger.info(f"📧 [DRY RUN] Welcome email to {email} (tier: {tier})")
                return True
            
            subject = f"Welcome to BlackRoad {tier.capitalize()} Plan!"
            
            body = f"""
            <h2>🎉 Welcome, {first_name}!</h2>
            
            <p>You're all set on the <strong>{tier.upper()}</strong> plan.</p>
            
            <h3>What's next?</h3>
            <ul>
                <li><a href="https://app.blackroad.io/dashboard">View your dashboard</a></li>
                <li><a href="https://docs.blackroad.io/getting-started">Read getting started guide</a></li>
                <li><a href="https://app.blackroad.io/settings/api">Create your first API key</a></li>
            </ul>
            
            <h3>Your Plan Includes:</h3>
            <ul>
                <li>API access with rate limiting</li>
                <li>Real-time analytics</li>
                <li>Email support</li>
            </ul>
            
            <p>Happy coding! 🚀</p>
            """
            
            return OnboardingEmailService._send_email(email, subject, body)
        except Exception as e:
            logger.error(f"❌ Failed to send welcome email: {e}")
            return False
    
    @staticmethod
    def send_onboarding_email_1(email: str, first_name: str) -> bool:
        """Send onboarding email 1 - API Basics"""
        try:
            if not SEND_EMAILS:
                logger.info(f"📧 [DRY RUN] Onboarding email 1 to {email}")
                return True
            
            subject = "Your First API Request 🚀"
            
            body = f"""
            <h2>Hi {first_name},</h2>
            
            <p>Here's how to make your first API request to BlackRoad:</p>
            
            <pre>curl -X GET https://api.blackroad.io/api/billing/usage \\
  -H "Authorization: Bearer YOUR_API_KEY"</pre>
            
            <p><a href="https://docs.blackroad.io/api-reference">See full API reference</a></p>
            """
            
            return OnboardingEmailService._send_email(email, subject, body)
        except Exception as e:
            logger.error(f"❌ Failed to send onboarding email 1: {e}")
            return False
    
    @staticmethod
    def _send_email(to_email: str, subject: str, body: str) -> bool:
        """Send email via SMTP"""
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = "noreply@blackroad.io"
            msg['To'] = to_email
            
            # Attach HTML body
            msg.attach(MIMEText(body, 'html'))
            
            # Send via SMTP
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
                server.starttls()
                server.login(SMTP_USER, SMTP_PASSWORD)
                server.send_message(msg)
            
            logger.info(f"📧 Email sent to {to_email}: {subject[:50]}")
            return True
        except Exception as e:
            logger.error(f"❌ SMTP error: {e}")
            return False

# ==============================================================================
# FLASK API
# ==============================================================================

app = Flask(__name__)
db = OnboardingDatabase(DATABASE_URL)
email_service = OnboardingEmailService()

def require_api_key(f):
    """Require API key"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not api_key or len(api_key) < 10:
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated_function

@app.route('/api/onboarding/start', methods=['POST'])
def onboarding_start():
    """Start onboarding signup"""
    try:
        data = request.get_json()
        
        email = data.get('email', '').lower().strip()
        first_name = data.get('first_name', '').strip()
        last_name = data.get('last_name', '').strip()
        company = data.get('company', '').strip()
        
        if not all([email, first_name, last_name]):
            return jsonify({"error": "Missing required fields"}), 400
        
        # Check if email already exists
        existing = db.get_profile_by_email(email)
        if existing:
            if existing['email_verified']:
                return jsonify({"error": "Email already registered"}), 409
            else:
                # Resend verification for incomplete signup
                onboarding_id = existing['id']
        else:
            # Create new profile
            onboarding_id = db.create_profile(email, first_name, last_name, company)
            if not onboarding_id:
                return jsonify({"error": "Email already exists"}), 409
        
        # Create verification token
        token = db.create_verification_token(onboarding_id, email)
        
        # Send verification email
        email_service.send_verification_email(email, token, first_name)
        
        return jsonify({
            "status": "signup_started",
            "onboarding_id": onboarding_id,
            "email": email,
            "next_step": "email_verification",
            "message": f"Verification email sent to {email}"
        }), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/api/onboarding/verify-email', methods=['POST'])
def verify_email():
    """Verify email with token"""
    try:
        data = request.get_json()
        token = data.get('token', '').strip()
        
        if not token:
            return jsonify({"error": "Token required"}), 400
        
        result = db.verify_email_token(token)
        if not result:
            return jsonify({"error": "Invalid or expired token"}), 401
        
        onboarding_id, email = result
        profile = db.get_profile(onboarding_id)
        
        return jsonify({
            "status": "email_verified",
            "onboarding_id": onboarding_id,
            "email": email,
            "name": f"{profile['first_name']} {profile['last_name']}",
            "next_step": "profile",
            "progress": 25
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/api/onboarding/complete-profile', methods=['POST'])
@require_api_key
def complete_profile():
    """Complete profile and select plan"""
    try:
        data = request.get_json()
        onboarding_id = data.get('onboarding_id', '').strip()
        tier = data.get('tier', 'free').lower()
        
        if not onboarding_id:
            return jsonify({"error": "Onboarding ID required"}), 400
        
        if tier not in [e.value for e in OnboardingTier]:
            return jsonify({"error": "Invalid tier"}), 400
        
        profile = db.get_profile(onboarding_id)
        if not profile:
            return jsonify({"error": "Profile not found"}), 404
        
        # Update profile with tier
        db.update_step(
            onboarding_id,
            OnboardingStep.PLAN_SELECTION.value,
            50,
            {"tier": tier}
        )
        
        # Send welcome email
        email_service.send_welcome_email(
            profile['email'],
            profile['first_name'],
            tier
        )
        
        return jsonify({
            "status": "profile_completed",
            "onboarding_id": onboarding_id,
            "tier": tier,
            "next_step": "create_api_key",
            "progress": 50
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/api/onboarding/progress', methods=['GET'])
@require_api_key
def onboarding_progress():
    """Get onboarding progress"""
    try:
        onboarding_id = request.args.get('onboarding_id', '').strip()
        
        if not onboarding_id:
            return jsonify({"error": "Onboarding ID required"}), 400
        
        profile = db.get_profile(onboarding_id)
        if not profile:
            return jsonify({"error": "Profile not found"}), 404
        
        return jsonify({
            "onboarding_id": onboarding_id,
            "email": profile['email'],
            "name": f"{profile['first_name']} {profile['last_name']}",
            "tier": profile['tier'],
            "current_step": profile['current_step'],
            "progress": profile['progress'],
            "email_verified": profile['email_verified'],
            "completed": profile['completed_at'] is not None,
            "started_at": profile['started_at'].isoformat(),
            "completed_at": profile['completed_at'].isoformat() if profile['completed_at'] else None
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/api/onboarding/resources', methods=['GET'])
def onboarding_resources():
    """Get onboarding resources and tutorials"""
    resources = [
        {
            "id": "res_1",
            "title": "Getting Started",
            "description": "Learn the basics of BlackRoad",
            "type": "guide",
            "url": "https://docs.blackroad.io/getting-started",
            "step": "profile"
        },
        {
            "id": "res_2",
            "title": "API Authentication",
            "description": "How to authenticate API requests",
            "type": "guide",
            "url": "https://docs.blackroad.io/api-authentication",
            "step": "first_api_key"
        },
        {
            "id": "res_3",
            "title": "Make Your First Request",
            "description": "Make your first API call",
            "type": "tutorial",
            "url": "https://docs.blackroad.io/first-request",
            "step": "first_request"
        },
        {
            "id": "res_4",
            "title": "Dashboard Overview",
            "description": "Navigate the admin dashboard",
            "type": "video",
            "url": "https://videos.blackroad.io/dashboard-overview",
            "step": "profile"
        },
        {
            "id": "res_5",
            "title": "API Rate Limits",
            "description": "Understanding rate limiting",
            "type": "guide",
            "url": "https://docs.blackroad.io/rate-limits",
            "step": "first_request"
        },
    ]
    
    step = request.args.get('step')
    
    if step:
        resources = [r for r in resources if r['step'] == step]
    
    return jsonify({"resources": resources, "count": len(resources)}), 200

@app.route('/api/onboarding/analytics', methods=['GET'])
def onboarding_analytics():
    """Get onboarding analytics"""
    try:
        api_key = request.headers.get('Authorization', '').replace('Bearer ', '')
        if api_key != ADMIN_TOKEN:
            return jsonify({"error": "Unauthorized"}), 401
        
        days = int(request.args.get('days', 30))
        analytics = db.get_analytics(days)
        
        return jsonify(analytics), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/api/onboarding/health', methods=['GET'])
def onboarding_health():
    """Health check"""
    return jsonify({
        "status": "healthy",
        "version": "1.0",
        "features": [
            "email_verification",
            "welcome_emails",
            "onboarding_sequence",
            "progress_tracking",
            "analytics"
        ]
    }), 200

if __name__ == '__main__':
    logger.info("🎯 Onboarding Service v1.0 starting...")
    logger.info(f"📧 Email sending: {'ENABLED' if SEND_EMAILS else 'DISABLED (dry run)'}")
    logger.info("🚀 Port: 8007")
    app.run(host='0.0.0.0', port=8007, debug=False)
