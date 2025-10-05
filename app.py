import os
import datetime
import requests
import random
import threading
from google import genai
import tweepy
from flask import Flask, jsonify, request

# ==============================================================================
# 0. CONFIGURATION & SETUP
# ==============================================================================

app = Flask(__name__)

# --- Load Secrets from Environment ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
ACCESS_TOKEN_LI = os.getenv("ACCESS_TOKEN_LI")
PERSON_URN = os.getenv("PERSON_URN")
ACCESS_TOKEN_IG = os.getenv("ACCESS_TOKEN_IG")
INSTAGRAM_BUSINESS_ID = os.getenv("INSTAGRAM_BUSINESS_ID")
CONSUMER_KEY = os.getenv("CONSUMER_KEY")
CONSUMER_SECRET = os.getenv("CONSUMER_SECRET")
X_ACCESS_TOKEN = os.getenv("X_ACCESS_TOKEN")
X_ACCESS_SECRET = os.getenv("X_ACCESS_SECRET")

# --- Security & Deployment Config ---
REQUIRED_TRIGGER_KEY = os.getenv("TRIGGER_KEY", "growwithkishore2148") # Default if not set
GUNICORN_WORKER_COUNT = 2

# --- GitHub Repo Info (public) ---
REPO_OWNER = "DATABASESK"
REPO_NAME = "kishore-personal-"
BRANCH = "main"
CONTENT_BASE_PATH = "content"

# --- Dynamic Content Setup & Constants ---
TODAY_FOLDER = datetime.date.today().strftime("%Y-%m-%d")
GITHUB_RAW_BASE_URL = (
    f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/{BRANCH}/"
    f"{CONTENT_BASE_PATH}/{TODAY_FOLDER}"
)
IMAGE_URL = f"{GITHUB_RAW_BASE_URL}/image.png"
LINKEDIN_CAPTION_URL = f"{GITHUB_RAW_BASE_URL}/caption_linkedin.txt"
INSTAGRAM_CAPTION_URL = f"{GITHUB_RAW_BASE_URL}/caption_instagram.txt"
MAX_TWEET_LENGTH = 280

# ==============================================================================
# 1. UTILITY FUNCTIONS (Content Fetching and Generation)
# ==============================================================================

def generate_gemini_article_text():
    """Generates a long, detailed LinkedIn article."""
    if not GEMINI_API_KEY or GEMINI_API_KEY == "YOUR_GEMINI_API_KEY_HERE":
        print("🛑 GEMINI_API_KEY is not set. Aborting content generation.")
        return None
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        system_instruction = (
            "You are a savvy digital marketing expert. Generate a **long, detailed, and highly valuable** "
            "LinkedIn article structured as **'Real-World Digital Marketing Tips and Tricks'**. "
            "Use a headline in **ALL CAPS** for impact, and break down the tips using **numbered headings** followed by double line breaks. "
            "**DO NOT use asterisk symbols (*)** for formatting or bolding, use line breaks and numbering for clarity. "
            "The content should maximize information density. "
            "The **ENTIRE POST MUST NOT EXCEED 2,500 CHARACTERS**. "
            "Crucially, the content must naturally include the name 'KISHORE S' and the handle '@growwithkishore' "
            "at least once, which is vital for search engine visibility. End the post with relevant hashtags."
        )

        print("🤖 Generating LONG, Cleanly Formatted Article Content with Gemini API...")
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents="Generate today's real-world digital marketing tips and tricks article.",
            config={"system_instruction": system_instruction,}
        )
        return response.text.strip()
    except Exception as e:
        print(f"🛑 Gemini API Error: Could not generate content. Error: {e}")
        return None

def generate_tweet_content(api_key: str):
    """Uses the Gemini API to generate a tweet."""
    print("\n🤖 Generating X (Twitter) Content with Gemini API...")
    if not api_key:
        print("❌ ERROR: Gemini API key is missing. Cannot generate X content.")
        return None
    try:
        client = genai.Client(api_key=api_key)
        system_instruction = (
            f"You are a helpful and engaging social media expert focused on digital marketing. "
            f"Generate a single, high-impact tweet about a real-world digital marketing tool or new technology. "
            f"The content MUST NOT exceed {MAX_TWEET_LENGTH} characters. "
            f"The tweet MUST include the text 'KISHORE S' and the handle '@growwithkishore'. "
            f"Use 1-2 relevant emojis and 1-2 popular digital marketing hashtags. "
            f"DO NOT include any introductory or concluding text, ONLY the tweet content."
        )
        topics = [
            "Practical uses of Generative AI in content creation",
            "The best new MarTech tools for small businesses",
            "Latest privacy-first analytics and measurement technologies",
            "Real-world application of programmatic advertising",
        ]
        prompt_text = f"Generate a tweet on the topic: {random.choice(topics)}"
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt_text,
            config={"system_instruction": system_instruction, "temperature": 0.8}
        )
        tweet_content = response.text.strip()
        
        # Ensure it fits the length limit
        if len(tweet_content) > MAX_TWEET_LENGTH:
            tweet_content = tweet_content[:MAX_TWEET_LENGTH - 3].strip() + "..."

        print(f"✅ Generated Tweet (Length: {len(tweet_content)}):\n---\n{tweet_content}\n---")
        return tweet_content

    except Exception as e:
        print(f"❌ An error occurred during Gemini API call for X: {e}")
        return None

def fetch_caption(caption_url):
    """Fetches the caption text from the GitHub raw URL."""
    try:
        response = requests.get(caption_url)
        response.raise_for_status()
        return response.text.strip()
    except requests.exceptions.HTTPError as e:
        print(f"🛑 Error: Could not find content at {caption_url}. (HTTP Status {e.response.status_code})")
        print("    Ensure the folder and file names are correct for the current date.")
        return None
    except requests.exceptions.RequestException as e:
        print(f"🛑 Network Error fetching caption from {caption_url}: {e}")
        return None

# ==============================================================================
# 2. LINKEDIN POSTING FUNCTIONS (TWO SEPARATE POSTS)
# ==============================================================================

def post_media_update_to_linkedin():
    """Posts an Image and Caption using content fetched from GitHub."""
    print("\n--- Starting LinkedIn Image/Caption Post (via GitHub) ---")
    if not ACCESS_TOKEN_LI or not PERSON_URN:
        print("🛑 LinkedIn credentials missing. Aborting media post.")
        return

    POST_TEXT = fetch_caption(LINKEDIN_CAPTION_URL)
    if not POST_TEXT:
        print("🛑 LinkedIn caption fetch failed. Aborting media post.")
        return

    headers = {"Authorization": f"Bearer {ACCESS_TOKEN_LI}", "Content-Type": "application/json"}
    
    # === STEPS 1 & 2: Register and Upload Image (Simplified Error Handling) ===
    try:
        # 1. Register Upload
        register_url = "https://api.linkedin.com/v2/assets?action=registerUpload"
        register_body = {
            "registerUploadRequest": {
                "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
                "owner": PERSON_URN,
                "serviceRelationships": [{"relationshipType": "OWNER", "identifier": "urn:li:userGeneratedContent"}]
            }
        }
        res = requests.post(register_url, json=register_body, headers=headers)
        res.raise_for_status()
        register_data = res.json()
        upload_url = register_data['value']['uploadMechanism']['com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest']['uploadUrl']
        asset_urn = register_data['value']['asset']
        print(f"✅ Step 1: Registered upload. Asset URN: {asset_urn}")

        # 2. Upload Image
        image_data = requests.get(IMAGE_URL).content
        upload_headers = {"Authorization": f"Bearer {ACCESS_TOKEN_LI}", "Content-Type": "application/octet-stream"}
        res = requests.put(upload_url, data=image_data, headers=upload_headers)
        res.raise_for_status()
        print("✅ Step 2: Image uploaded successfully.")

        # === STEP 3: Post text + image ===
        post_url = "https://api.linkedin.com/v2/ugcPosts"
        post_body = {
            "author": PERSON_URN,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": POST_TEXT},
                    "shareMediaCategory": "IMAGE",
                    "media": [{"status": "READY", "media": asset_urn}]
                }
            },
            # THIS FIELD IS CRITICAL AND CORRECTLY INCLUDED
            "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"} 
        }
        res = requests.post(post_url, json=post_body, headers=headers)
        res.raise_for_status()
        print("🎉 Step 3: LinkedIn Image/Caption Post created successfully!")
    
    except requests.exceptions.RequestException as e:
        print(f"🛑 LinkedIn Media Post FAILED. Error: {e}")
        if e.response is not None:
            print(f"    Response Status: {e.response.status_code}, Details: {e.response.text[:200]}...")


def post_gemini_article_to_linkedin():
    """Posts a text-only Article generated by the Gemini API."""
    print("\n--- Starting LinkedIn Article Post (via Gemini API) ---")
    if not ACCESS_TOKEN_LI or not PERSON_URN:
        print("🛑 LinkedIn credentials missing. Aborting article post.")
        return

    # >>> Gemini Content Generation (THE LONG RUNNING CALL) <<<
    ARTICLE_TEXT = generate_gemini_article_text()
    if not ARTICLE_TEXT:
        print("🛑 Article content generation failed. Aborting article post.")
        return

    headers = {"Authorization": f"Bearer {ACCESS_TOKEN_LI}", "Content-Type": "application/json"}
    
    try:
        post_url = "https://api.linkedin.com/v2/ugcPosts"
        post_body = {
            "author": PERSON_URN,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": ARTICLE_TEXT},
                    "shareMediaCategory": "NONE"
                }
            },
            # THIS FIELD IS CRITICAL AND CORRECTLY INCLUDED
            "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"}
        }
        res = requests.post(post_url, json=post_body, headers=headers)
        res.raise_for_status()
        print("🎉 LinkedIn Article Post (Gemini content) created successfully!")
    
    except requests.exceptions.RequestException as e:
        print(f"🛑 LinkedIn Article Post FAILED. Error: {e}")
        if e.response is not None:
            print(f"    Response Status: {e.response.status_code}, Details: {e.response.text[:200]}...")

# ==============================================================================
# 3. X (Twitter) POSTING FUNCTION
# ==============================================================================

def post_tweet(tweet_text):
    """Posts the provided tweet using the modern tweepy Client."""
    print("\n--- Starting X (Twitter) Post ---")
    if not tweet_text:
        print("❌ Cannot post. Tweet content is empty.")
        return
    
    # Check for X credentials (using the correct X_ACCESS variables)
    if not all([CONSUMER_KEY, CONSUMER_SECRET, X_ACCESS_TOKEN, X_ACCESS_SECRET]):
        print("🛑 X API credentials missing. Aborting X post.")
        return

    try:
        client = tweepy.Client(
            consumer_key=CONSUMER_KEY,
            consumer_secret=CONSUMER_SECRET,
            access_token=X_ACCESS_TOKEN,       # <-- FIXED
            access_token_secret=X_ACCESS_SECRET # <-- FIXED
        )
        client.get_me() # Auth check
        print("✅ X API Authentication successful.")

        response = client.create_tweet(text=tweet_text)
        tweet_id = response.data['id']
        tweet_url = f"https://x.com/growwithkishore/status/{tweet_id}"
        
        print(f"🎉 Successfully posted tweet to X account @growwithkishore!")
        print(f"Link: {tweet_url}")

    except tweepy.TweepyException as e:
        print(f"❌ An error occurred during X API interaction (Tweepy Exception): {e}")
    except Exception as e:
        print(f"❌ A general error occurred during X posting: {e}")

# ==============================================================================
# 4. INSTAGRAM POSTING FUNCTION (Simplified)
# ==============================================================================

def post_to_instagram():
    """Handles the 2-step process to post an image and caption to Instagram."""
    print("\n--- Starting Instagram Post ---")
    if not ACCESS_TOKEN_IG or not INSTAGRAM_BUSINESS_ID:
        print("🛑 Instagram credentials missing. Aborting Instagram post.")
        return

    CAPTION_TEXT = fetch_caption(INSTAGRAM_CAPTION_URL)
    if not CAPTION_TEXT:
        print("🛑 Instagram caption fetch failed. Aborting post.")
        return

    try:
        # === STEP 1: Create Media Container ===
        media_url = f"https://graph.facebook.com/v17.0/{INSTAGRAM_BUSINESS_ID}/media"
        media_params = {
            "image_url": IMAGE_URL, 
            "caption": CAPTION_TEXT,
            "access_token": ACCESS_TOKEN_IG
        }
        res = requests.post(media_url, data=media_params)
        res.raise_for_status()
        media_container_id = res.json().get("id")

        if not media_container_id:
             raise Exception(f"Container ID not found. Response: {res.json()}")

        print(f"✅ Step 1: Media container created. ID: {media_container_id}")

        # === STEP 2: Publish the Media ===
        publish_url = f"https://graph.facebook.com/v17.0/{INSTAGRAM_BUSINESS_ID}/media_publish"
        publish_params = {
            "creation_id": media_container_id,
            "access_token": ACCESS_TOKEN_IG
        }
        res = requests.post(publish_url, data=publish_params)
        res.raise_for_status()
        print("🎉 Step 2: Instagram Post published successfully!")
    
    except requests.exceptions.RequestException as e:
        print(f"🛑 Instagram Post FAILED. Error: {e}")
        if e.response is not None:
            print(f"    Response Status: {e.response.status_code}, Details: {e.response.text[:200]}...")
    except Exception as e:
        print(f"🛑 Instagram Post FAILED (General Error): {e}")

# ==============================================================================
# 5. MAIN AUTOMATION SEQUENCE (EXECUTED IN BACKGROUND)
# ==============================================================================

def run_automation_sequence():
    """Executes the full, potentially long-running social media posting sequence."""
    print("=" * 60)
    print(f"🚀 Starting Unified Social Media Automation for: {TODAY_FOLDER}")
    print("=" * 60)
    
    # --- X (Twitter) Post ---
    final_tweet = generate_tweet_content(GEMINI_API_KEY)
    if final_tweet:
        post_tweet(final_tweet)
    else:
        print("⚠️ X Post Skipped: Content generation failed.")

    print("\n" + "=" * 60)

    # --- LinkedIn Posts ---
    post_media_update_to_linkedin()
    
    print("\n" + "=" * 60)

    post_gemini_article_to_linkedin()
    
    print("\n" + "=" * 60)

    # --- Instagram Post ---
    post_to_instagram()
    
    print("\n" + "=" * 60)
    print("✅ Full Automation Sequence Completed in background thread.")

# ==============================================================================
# 6. FLASK ROUTES (The HTTP Interface)
# ==============================================================================

@app.route("/")
def index():
    return jsonify({"status": "Automation Service is Running", "endpoint": "/trigger-automation"})

@app.route("/trigger-automation", methods=["POST"])
def social_automation_trigger():
    """
    HTTP endpoint to trigger the automation sequence.
    It uses threading to avoid Gunicorn timeouts.
    """
    # 1. Trigger Key Security Check
    key = request.headers.get("X-Trigger-Key")
    if key != REQUIRED_TRIGGER_KEY:
        print(f"🛑 Security Alert: Invalid X-Trigger-Key received: {key}")
        return jsonify({"message": "Forbidden: Invalid trigger key."}), 403

    # 2. Start the Automation in a separate thread
    print(f"✅ Trigger Key validated. Starting automation sequence in background thread...")
    
    # This is the Gunicorn Timeout fix: the heavy lifting (Gemini API) runs separately.
    thread = threading.Thread(target=run_automation_sequence)
    thread.start()

    # 3. Return an immediate 202 response to the HTTP client
    return jsonify({
        "message": "Automation sequence started in the background.",
        "status_code": 202,
        "date_attempted": TODAY_FOLDER
    }), 202

if __name__ == "__main__":
    # Note: In a production environment like Render, gunicorn is used (via Procfile)
    # This block is for local testing only.
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
