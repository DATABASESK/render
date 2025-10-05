import os
import datetime
import requests
import random
import json
import threading
from google import genai
import tweepy
from flask import Flask, jsonify, request
import time # Included for potential future use or debugging delays

# ==============================================================================
# 1. CONFIGURATION & SECRETS LOADING (FOR RENDER/ENVIRONMENT)
# ==============================================================================

app = Flask(__name__)

# --- Load Secrets from Environment Variables (Render) ---
print("Attempting to load secrets from Environment Variables (os.getenv)...")
try:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    ACCESS_TOKEN_LI = os.getenv("ACCESS_TOKEN_LI")
    PERSON_URN = os.getenv("PERSON_URN")
    ACCESS_TOKEN_IG = os.getenv("ACCESS_TOKEN_IG")
    INSTAGRAM_BUSINESS_ID = os.getenv("INSTAGRAM_BUSINESS_ID")
    CONSUMER_KEY = os.getenv("CONSUMER_KEY")
    CONSUMER_SECRET = os.getenv("CONSUMER_SECRET")
    X_ACCESS_TOKEN = os.getenv("X_ACCESS_TOKEN")
    X_ACCESS_SECRET = os.getenv("X_ACCESS_SECRET")
    REQUIRED_TRIGGER_KEY = os.getenv("TRIGGER_KEY", "growwithkishore2148") 
    print("✅ Successfully loaded all necessary secrets.")
except Exception as e:
    print(f"🛑 ERROR: Failed to load environment variables. Error: {e}")

# --- GitHub Repo Info ---
REPO_OWNER = "DATABASESK"
REPO_NAME = "kishore-personal-"
BRANCH = "main"
CONTENT_BASE_PATH = "content"

# --- Tagging Configuration (Working Instagram Tags) ---
INSTAGRAM_USER_TAGS = [
    # 1. digi_aura_meena
    {"username": "digi_aura_meena", "x": 0.2, "y": 0.8},
    # 2. saravanan.online
    {"username": "saravanan.online", "x": 0.75, "y": 0.25},
    # 3. archana_digital_marketer_06
    {"username": "archana_digital_marketer_06", "x": 0.1, "y": 0.1},
    # 4. ft_bilxl_0918
    {"username": "ft_bilxl_0918", "x": 0.5, "y": 0.5},
    # 5. monika_digital_marketer
    {"username": "monika_digital_marketer", "x": 0.15, "y": 0.9},
    # 6. shainsha_js
    {"username": "shainsha_js", "x": 0.85, "y": 0.8},
    # 7. prabhas_samuell
    {"username": "prabhas_samuell", "x": 0.4, "y": 0.1},
]

# ==============================================================================
# 2. DYNAMIC CONTENT SETUP & CONSTANTS
# ==============================================================================

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
# 3. UTILITY FUNCTIONS (Content Fetching and Generation)
# ==============================================================================

def generate_alt_text(caption_text):
    """Generates concise, descriptive Alt Text based on the post caption."""
    if not GEMINI_API_KEY:
        print("🛑 GEMINI_API_KEY is not set. Aborting Alt Text generation.")
        return "Digital marketing image by KISHORE S/growwithkishore."
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        system_instruction = (
            "You are an expert in social media accessibility and SEO. Analyze the provided post caption "
            "and generate a concise, descriptive, and informative **Alt Text** for the accompanying image. "
            "The Alt Text should be a short sentence or phrase describing the image's visual content, "
            "and **MUST** naturally include the name 'KISHORE S' and the company 'growwithkishore'. "
            "**DO NOT** use the phrases 'Image of' or 'Picture of'. "
            "Keep the response to **under 250 characters**."
        )
        print("🤖 Generating Alt Text with Gemini...")
        prompt_text = f"The image is for a post with the following caption: '{caption_text}'. Generate Alt Text for the image."

        response = client.models.generate_content(
            model='gemini-2.5-flash', contents=prompt_text, config={"system_instruction": system_instruction, "temperature": 0.5}
        )
        alt_text = response.text.strip()
        if len(alt_text) > 250:
            alt_text = alt_text[:247] + "..."
        print(f"✅ Generated Alt Text (Length: {len(alt_text)}): {alt_text}")
        return alt_text

    except Exception as e:
        print(f"🛑 Gemini API Error during Alt Text generation: {e}")
        return "Digital marketing graphic featuring tips or statistics, created by KISHORE S for growwithkishore."


def generate_gemini_article_text():
    """Generates a long, detailed LinkedIn article."""
    if not GEMINI_API_KEY:
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
            config={"system_instruction": system_instruction}
        )
        return response.text.strip()
    except Exception as e:
        print(f"🛑 Gemini API Error: Could not generate content. Error: {e}")
        return None

def generate_tweet_content():
    """Uses the Gemini API to generate a tweet."""
    print("\n🤖 Generating X (Twitter) Content with Gemini API...")
    if not GEMINI_API_KEY:
        print("❌ ERROR: Gemini API key is missing. Cannot generate X content.")
        return None
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        system_instruction = (
            f"You are a helpful and engaging social media expert focused on digital marketing. "
            f"Generate a single, high-impact tweet about a real-world digital marketing tool or new technology. "
            f"The content MUST NOT exceed {MAX_TWEET_LENGTH} characters. "
            f"The tweet MUST include the text 'KISHORE S' and the handle '@growwithkishore'. "
            f"Use 1-2 relevant emojis and 1-2 popular digital marketing hashtags. "
            f"DO NOT include any introductory or concluding text, ONLY the tweet content."
        )
        topics = ["Practical uses of Generative AI in content creation", "The best new MarTech tools for small businesses"]
        prompt_text = f"Generate a tweet on the topic: {random.choice(topics)}"
        response = client.models.generate_content(
            model='gemini-2.5-flash', contents=prompt_text, config={"system_instruction": system_instruction, "temperature": 0.8}
        )
        tweet_content = response.text.strip()
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
    except requests.exceptions.RequestException as e:
        print(f"🛑 Error fetching caption from {caption_url}: {e}")
        return None

# ==============================================================================
# 4. LINKEDIN POSTING FUNCTIONS (With Alt Text Integration)
# ==============================================================================

def post_media_update_to_linkedin():
    """Posts an Image and Caption, integrating Gemini-generated Alt Text."""
    print("\n--- Starting LinkedIn Image/Caption Post (via GitHub with Alt Text) ---")

    if not ACCESS_TOKEN_LI or not PERSON_URN:
        print("🛑 LinkedIn credentials missing. Aborting media post.")
        return

    POST_TEXT = fetch_caption(LINKEDIN_CAPTION_URL)
    if not POST_TEXT:
        print("🛑 LinkedIn caption fetch failed. Aborting media post.")
        return

    # >>> 1. Generate Alt Text <<<
    ALT_TEXT = generate_alt_text(POST_TEXT)

    headers = {"Authorization": f"Bearer {ACCESS_TOKEN_LI}", "Content-Type": "application/json"}

    try:
        # === STEP 1: Register Asset ===
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

        # === STEP 2: Upload Image ===
        image_data = requests.get(IMAGE_URL).content
        upload_headers = {"Authorization": f"Bearer {ACCESS_TOKEN_LI}", "Content-Type": "application/octet-stream"}
        requests.put(upload_url, data=image_data, headers=upload_headers).raise_for_status()
        print("✅ Step 2: Image uploaded successfully.")

        # === STEP 3: Post text + image (Including Alt Text in the 'media' object) ===
        post_url = "https://api.linkedin.com/v2/ugcPosts"
        post_body = {
            "author": PERSON_URN, "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": POST_TEXT},
                    "shareMediaCategory": "IMAGE",
                    "media": [
                        {
                            "status": "READY",
                            "media": asset_urn,
                            "altText": ALT_TEXT # Alt Text placed here
                        }
                    ]
                }
            },
            "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"}
        }
        requests.post(post_url, json=post_body, headers=headers).raise_for_status()
        print("🎉 Step 3: LinkedIn Image/Caption Post created successfully (with Alt Text)!")

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

    ARTICLE_TEXT = generate_gemini_article_text()
    if not ARTICLE_TEXT:
        print("🛑 Article content generation failed. Aborting article post.")
        return

    headers = {"Authorization": f"Bearer {ACCESS_TOKEN_LI}", "Content-Type": "application/json"}

    try:
        post_url = "https://api.linkedin.com/v2/ugcPosts"
        post_body = {
            "author": PERSON_URN, "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": ARTICLE_TEXT},
                    "shareMediaCategory": "NONE"
                }
            },
            "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"}
        }
        requests.post(post_url, json=post_body, headers=headers).raise_for_status()
        print("🎉 LinkedIn Article Post (Gemini content) created successfully!")

    except requests.exceptions.RequestException as e:
        print(f"🛑 LinkedIn Article Post FAILED. Error: {e}")
        if e.response is not None:
            print(f"    Response Status: {e.response.status_code}, Details: {e.response.text[:200]}...")

# ==============================================================================
# 5. X (Twitter) POSTING FUNCTION
# ==============================================================================

def post_tweet(tweet_text):
    """Authenticates with the X API and posts the provided tweet."""
    print("\n--- Starting X (Twitter) Post ---")
    if not all([CONSUMER_KEY, CONSUMER_SECRET, X_ACCESS_TOKEN, X_ACCESS_SECRET]):
        print("🛑 X API credentials missing. Aborting X post.")
        return

    try:
        client = tweepy.Client(
            consumer_key=CONSUMER_KEY, consumer_secret=CONSUMER_SECRET,
            access_token=X_ACCESS_TOKEN, access_token_secret=X_ACCESS_SECRET
        )
        me_response = client.get_me()
        user_handle = me_response.data['username']
        print(f"✅ X API Authentication successful for user @{user_handle}.")

        response = client.create_tweet(text=tweet_text)
        tweet_id = response.data['id']
        tweet_url = f"https://x.com/{user_handle}/status/{tweet_id}"
        print(f"🎉 Successfully posted tweet to X account @{user_handle}!")
        print(f"Link: {tweet_url}")

    except Exception as e:
        print(f"❌ An error occurred during X posting: {e}")

# ==============================================================================
# 6. INSTAGRAM POSTING FUNCTION (With Alt Text and User Tags)
# ==============================================================================

def post_to_instagram():
    """Handles the 2-step process to post an image, caption, Alt Text, and User Tags."""
    print("\n--- Starting Instagram Post (with Alt Text & User Tags) ---")

    if not ACCESS_TOKEN_IG or not INSTAGRAM_BUSINESS_ID:
        print("🛑 Instagram credentials missing. Aborting Instagram post.")
        return

    CAPTION_TEXT = fetch_caption(INSTAGRAM_CAPTION_URL)
    if not CAPTION_TEXT:
        print("🛑 Instagram caption fetch failed. Aborting post.")
        return

    # >>> Generate Alt Text <<<
    ALT_TEXT = generate_alt_text(CAPTION_TEXT)

    try:
        # === STEP 1: Create Media Container ===
        media_url = f"https://graph.facebook.com/v17.0/{INSTAGRAM_BUSINESS_ID}/media"
        user_tags_json = json.dumps(INSTAGRAM_USER_TAGS)

        media_params = {
            "image_url": IMAGE_URL,
            "caption": CAPTION_TEXT,
            "access_token": ACCESS_TOKEN_IG,
            "alt_text": ALT_TEXT,
            "user_tags": user_tags_json
        }

        print(f"    Including {len(INSTAGRAM_USER_TAGS)} user tags for image.")
        res = requests.post(media_url, data=media_params)
        res.raise_for_status()
        media_container_id = res.json().get("id")

        if not media_container_id:
             raise Exception(f"Container ID not found. Response: {res.json()}")

        print(f"✅ Step 1: Media container created (with Alt Text and User Tags). ID: {media_container_id}")

        # === STEP 2: Publish the Media ===
        publish_url = f"https://graph.facebook.com/v17.0/{INSTAGRAM_BUSINESS_ID}/media_publish"
        publish_params = {"creation_id": media_container_id, "access_token": ACCESS_TOKEN_IG}
        requests.post(publish_url, data=publish_params).raise_for_status()
        print("🎉 Step 2: Instagram Post published successfully (with Alt Text and Tags)!")

    except requests.exceptions.RequestException as e:
        print(f"🛑 Instagram Post FAILED. Error: {e}")
        if e.response is not None:
            print(f"    Response Status: {e.response.status_code}, Details: {e.response.text[:500]}...")

# ==============================================================================
# 7. MAIN AUTOMATION SEQUENCE (EXECUTED IN BACKGROUND THREAD)
# ==============================================================================

def run_automation_sequence():
    """Executes the full, potentially long-running social media posting sequence."""
    print("=" * 60)
    print(f"🚀 Starting Unified Social Media Automation for: {TODAY_FOLDER}")
    print("=" * 60)
    
    # --- X (Twitter) Post ---
    final_tweet = generate_tweet_content()
    if final_tweet:
        post_tweet(final_tweet)

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
# 8. FLASK ROUTES (The HTTP Interface)
# ==============================================================================

@app.route("/")
def index():
    return jsonify({"status": "Automation Service is Running", "endpoint": "/trigger-automation"})

@app.route("/trigger-automation", methods=["POST"])
def social_automation_trigger():
    """
    HTTP endpoint with security and threading to prevent Gunicorn timeout.
    """
    # 1. Trigger Key Security Check
    key = request.headers.get("X-Trigger-Key")
    if key != REQUIRED_TRIGGER_KEY:
        print(f"🛑 Security Alert: Invalid X-Trigger-Key received: {key}")
        return jsonify({"message": "Forbidden: Invalid trigger key."}), 403

    # 2. Start the Automation in a separate thread (Timeout Fix)
    print(f"✅ Trigger Key validated. Starting automation sequence in background thread...")
    thread = threading.Thread(target=run_automation_sequence)
    thread.start()

    # 3. Return an immediate 202 Accepted response
    return jsonify({
        "message": "Automation sequence started successfully in the background.",
        "status_code": 202,
        "date_attempted": TODAY_FOLDER
    }), 202

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
