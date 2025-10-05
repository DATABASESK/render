from flask import Flask, request, jsonify
import datetime
import requests
import random
import json
from google import genai
import tweepy
import os
import time
from typing import Optional

# ==============================================================================
# 1. CONFIGURATION & SECRETS LOADING (Render Environment Variables)
# ==============================================================================

# NOTE: These variables are loaded from the Render Dashboard settings.
# All secret values must be set in your Render project's Environment Variables.
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
ACCESS_TOKEN_LI = os.environ.get("ACCESS_TOKEN_LI")
PERSON_URN = os.environ.get("PERSON_URN")
ACCESS_TOKEN_IG = os.environ.get("ACCESS_TOKEN_IG")
INSTAGRAM_BUSINESS_ID = os.environ.get("INSTAGRAM_BUSINESS_ID")
CONSUMER_KEY = os.environ.get("CONSUMER_KEY")
CONSUMER_SECRET = os.environ.get("CONSUMER_SECRET")
X_ACCESS_TOKEN = os.environ.get("X_ACCESS_TOKEN")
X_ACCESS_SECRET = os.environ.get("X_ACCESS_SECRET")
WEB_TRIGGER_KEY = os.environ.get("WEB_TRIGGER_KEY") # Your custom security key: 'growwithkishore2148'

# --- GitHub Repo Info ---
REPO_OWNER = "DATABASESK"
REPO_NAME = "kishore-personal-"
BRANCH = "main"
CONTENT_BASE_PATH = "content"


# --- Tagging Configuration (Working Instagram Tags) ---
INSTAGRAM_USER_TAGS = [
    {"username": "digi_aura_meena", "x": 0.2, "y": 0.8},
    {"username": "saravanan.online", "x": 0.75, "y": 0.25},
    {"username": "archana_digital_marketer_06", "x": 0.1, "y": 0.1},
    {"username": "ft_bilxl_0918", "x": 0.5, "y": 0.5},
    {"username": "monika_digital_marketer", "x": 0.15, "y": 0.9},
    {"username": "shainsha_js", "x": 0.85, "y": 0.8},
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

def generate_alt_text(caption_text: str) -> str:
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
            model='gemini-2.5-flash',
            contents=prompt_text,
            config={"system_instruction": system_instruction, "temperature": 0.5,}
        )
        alt_text = response.text.strip()
        if len(alt_text) > 250:
             alt_text = alt_text[:247].strip() + "..."
        print(f"✅ Generated Alt Text (Length: {len(alt_text)}): {alt_text}")
        return alt_text

    except Exception as e:
        print(f"🛑 Gemini API Error during Alt Text generation: {e}")
        return "Digital marketing graphic featuring tips or statistics, created by KISHORE S for growwithkishore."


def generate_gemini_article_text() -> Optional[str]:
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
            "The **ENTIRE POST MUST NOT EXCEED 2,500 CHARACTERS** (including all headings and signatures). "
            "Crucially, the content must naturally include the name 'KISHORE S' and the handle '@growwithkishore' "
            "at least once, which is vital for search engine visibility. End the post with relevant hashtags."
        )
        print("🤖 Generating LONG, Cleanly Formatted Article Content with Gemini API...")
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents="Generate today's real-world digital marketing tips and tricks article.",
            config={"system_instruction": system_instruction, }
        )
        return response.text.strip()
    except Exception as e:
        print(f"🛑 Gemini API Error: Could not generate content. Error: {e}")
        return None


def generate_tweet_content() -> Optional[str]:
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
            f"Use 1-2 relevant emojis and 1-2 popular digital marketing hashtags (e.g., #DigitalMarketing, #AI). "
            f"DO NOT include any introductory or concluding text, ONLY the tweet content."
        )
        topics = ["Practical uses of Generative AI in content creation", "The best new MarTech tools for small businesses", "Latest privacy-first analytics and measurement technologies", "Real-world application of programmatic advertising", "New features in social media platform algorithms"]
        prompt_text = f"Generate a tweet on the topic: {random.choice(topics)}"
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt_text,
            config={"system_instruction": system_instruction, "temperature": 0.8}
        )
        tweet_content = response.text.strip()
        required_suffix = f" | KISHORE S @growwithkishore"
        if "KISHORE S" not in tweet_content or "@growwithkishore" not in tweet_content:
             if len(tweet_content) + len(required_suffix) < MAX_TWEET_LENGTH:
                 tweet_content = tweet_content.strip() + required_suffix
             else:
                 truncate_len = MAX_TWEET_LENGTH - len(required_suffix) - 3
                 tweet_content = tweet_content[:truncate_len].strip() + "..." + required_suffix.split(' | ')[1]
        if len(tweet_content) > MAX_TWEET_LENGTH:
             tweet_content = tweet_content[:MAX_TWEET_LENGTH - 3].strip() + "..."
             print(f"⚠️ Warning: Final tweet truncated to {len(tweet_content)} characters.")
        print(f"✅ Generated Tweet (Length: {len(tweet_content)}):\n---\n{tweet_content}\n---")
        return tweet_content
    except Exception as e:
        print(f"❌ An error occurred during Gemini API call for X: {e}")
        return None


def fetch_caption(caption_url: str) -> Optional[str]:
    """Fetches the caption text from the GitHub raw URL."""
    try:
        response = requests.get(caption_url)
        # Ensure that if the file is NOT found (404), we handle it gracefully
        response.raise_for_status() 
        return response.text.strip()
    except requests.exceptions.HTTPError as e:
        print(f"🛑 Error: Could not find content at {caption_url}. (HTTP Status {e.response.status_code})")
        # Returning None here allows the posting function to abort gracefully
        return None 
    except requests.exceptions.RequestException as e:
        print(f"🛑 Network Error fetching caption from {caption_url}: {e}")
        return None

# ==============================================================================
# 4. LINKEDIN POSTING FUNCTIONS
# ==============================================================================

def post_media_update_to_linkedin():
    """Posts an Image and Caption."""
    print("\n--- Starting LinkedIn Image/Caption Post ---")
    if not ACCESS_TOKEN_LI or not PERSON_URN:
        print("🛑 LinkedIn credentials missing. Aborting media post.")
        return
    POST_TEXT = fetch_caption(LINKEDIN_CAPTION_URL)
    if not POST_TEXT:
        print("🛑 LinkedIn caption fetch failed. Aborting media post.")
        return
    ALT_TEXT = generate_alt_text(POST_TEXT)
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN_LI}", "Content-Type": "application/json"}
    try:
        # === STEP 1: Register Asset ===
        register_url = "https://api.linkedin.com/v2/assets?action=registerUpload"
        register_body = {"registerUploadRequest": {"recipes": ["urn:li:digitalmediaRecipe:feedshare-image"], "owner": PERSON_URN, "serviceRelationships": [{"relationshipType": "OWNER", "identifier": "urn:li:userGeneratedContent"}]}}
        res = requests.post(register_url, json=register_body, headers=headers)
        res.raise_for_status()
        register_data = res.json()
        upload_url = register_data['value']['uploadMechanism']['com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest']['uploadUrl']
        asset_urn = register_data['value']['asset']
        print(f"✅ Step 1: Registered upload. Asset URN: {asset_urn}")
        # === STEP 2: Upload Image ===
        image_data = requests.get(IMAGE_URL).content
        upload_headers = {"Authorization": f"Bearer {ACCESS_TOKEN_LI}", "Content-Type": "application/octet-stream"}
        res = requests.put(upload_url, data=image_data, headers=upload_headers)
        res.raise_for_status()
        print("✅ Step 2: Image uploaded successfully.")
        # === STEP 3: Post text + image ===
        post_url = "https://api.linkedin.com/v2/ugcPosts"
        # CLEANED post_body structure to prevent 422 errors
        post_body = {"author": PERSON_URN, "lifecycleState": "PUBLISHED", "specificContent": {"com.linkedin.ugc.ShareContent": {"shareCommentary": {"text": POST_TEXT}, "shareMediaCategory": "IMAGE", "media": [{"status": "READY", "media": asset_urn, "altText": ALT_TEXT}]}, "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"}}}
        res = requests.post(post_url, json=post_body, headers=headers)
        res.raise_for_status()
        print("🎉 Step 3: LinkedIn Image/Caption Post created successfully!")
    except requests.exceptions.RequestException as e:
        print(f"🛑 LinkedIn Media Post FAILED. Error: {e}")
        if e.response is not None:
             print(f"     Response Status: {e.response.status_code}, Details: {e.response.text[:200]}...")


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
        post_body = {"author": PERSON_URN, "lifecycleState": "PUBLISHED", "specificContent": {"com.linkedin.ugc.ShareContent": {"shareCommentary": {"text": ARTICLE_TEXT}, "shareMediaCategory": "NONE"}}, "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"}}
        res = requests.post(post_url, json=post_body, headers=headers)
        res.raise_for_status()
        print("🎉 LinkedIn Article Post (Gemini content) created successfully!")
    except requests.exceptions.RequestException as e:
        print(f"🛑 LinkedIn Article Post FAILED. Error: {e}")
        if e.response is not None:
             print(f"     Response Status: {e.response.status_code}, Details: {e.response.text[:200]}...")

# ==============================================================================
# 5. X (Twitter) POSTING FUNCTION
# ==============================================================================

def post_tweet(tweet_text: str):
    """Authenticates with the X API using OAuth 1.0a and posts the provided tweet."""
    print("\n--- Starting X (Twitter) Post ---")
    if not tweet_text: return
    if not all([CONSUMER_KEY, CONSUMER_SECRET, X_ACCESS_TOKEN, X_ACCESS_SECRET]):
          print("🛑 X API credentials missing. Aborting X post.")
          return
    try:
        client = tweepy.Client(consumer_key=CONSUMER_KEY, consumer_secret=CONSUMER_SECRET, access_token=X_ACCESS_TOKEN, access_token_secret=X_ACCESS_SECRET)
        try:
             me_response = client.get_me()
             user_handle = me_response.data['username']
             print(f"✅ X API Authentication successful for user @{user_handle}.")
        except Exception as e:
             print(f"❌ X API Authentication failed. Error: {e}")
             return
        response = client.create_tweet(text=tweet_text)
        tweet_id = response.data['id']
        tweet_url = f"https://x.com/{user_handle}/status/{tweet_id}"
        print(f"🎉 Successfully posted tweet to X account @{user_handle}!")
        print(f"Link: {tweet_url}")
    except tweepy.TweepyException as e:
        print(f"❌ An error occurred during X API interaction (Tweepy Exception): {e}")
    except Exception as e:
        print(f"❌ A general error occurred during X posting: {e}")

# ==============================================================================
# 6. INSTAGRAM POSTING FUNCTION
# ==============================================================================

def post_to_instagram():
    """Handles the 2-step process to post an image and caption to Instagram."""
    print("\n--- Starting Instagram Post (with Alt Text & User Tags) ---")
    if not ACCESS_TOKEN_IG or not INSTAGRAM_BUSINESS_ID:
        print("🛑 Instagram credentials missing. Aborting Instagram post.")
        return
    CAPTION_TEXT = fetch_caption(INSTAGRAM_CAPTION_URL)
    if not CAPTION_TEXT:
        print("🛑 Instagram caption fetch failed. Aborting post.")
        return
    ALT_TEXT = generate_alt_text(CAPTION_TEXT)
    try:
        # === STEP 1: Create Media Container ===
        media_url = f"https://graph.facebook.com/v17.0/{INSTAGRAM_BUSINESS_ID}/media"
        user_tags_json = json.dumps(INSTAGRAM_USER_TAGS)
        media_params = {"image_url": IMAGE_URL, "caption": CAPTION_TEXT, "access_token": ACCESS_TOKEN_IG, "alt_text": ALT_TEXT, "user_tags": user_tags_json}
        res = requests.post(media_url, data=media_params)
        res.raise_for_status()
        media_container_id = res.json().get("id")
        if not media_container_id:
             print(f"🛑 Error: Container ID not found. Response: {res.json()}")
             return
        print(f"✅ Step 1: Media container created (with Alt Text and User Tags). ID: {media_container_id}")
        # === STEP 2: Publish the Media ===
        publish_url = f"https://graph.facebook.com/v17.0/{INSTAGRAM_BUSINESS_ID}/media_publish"
        publish_params = {"creation_id": media_container_id, "access_token": ACCESS_TOKEN_IG}
        res = requests.post(publish_url, data=publish_params)
        res.raise_for_status()
        print("🎉 Step 2: Instagram Post published successfully (with Alt Text and Tags)!")
    except requests.exceptions.RequestException as e:
        print(f"🛑 Instagram Post FAILED. Error: {e}")
        if e.response is not None:
             print(f"     Response Status: {e.response.status_code}, Details: {e.response.text[:500]}...")


# ==============================================================================
# 7. RENDER FLASK ENTRY POINT
# ==============================================================================

app = Flask(__name__)

@app.route('/trigger-automation', methods=['POST'])
def social_automation_trigger():
    """
    HTTP endpoint to trigger the social media posting sequence via web request.
    """
    # 1. SECURITY CHECK (CRITICAL)
    provided_key = request.headers.get("X-Trigger-Key")
    
    # This line checks the key from the client header against the key read from Render's environment.
    if WEB_TRIGGER_KEY and provided_key != WEB_TRIGGER_KEY:
        return jsonify({"status": "error", "message": "Unauthorized access."}), 403
    
    if not GEMINI_API_KEY:
        return jsonify({"status": "error", "message": "Critical API Key Missing."}), 500

    print("=" * 60)
    print(f"🚀 Starting Unified Social Media Automation for: {TODAY_FOLDER}")
    print("=" * 60)

    # --- EXECUTION ---
    # The asynchronous worker (gevent) prevents the 500 error during long API calls.
    final_tweet = generate_tweet_content()
    if final_tweet:
        post_tweet(final_tweet)

    post_media_update_to_linkedin()
    post_gemini_article_to_linkedin()
    post_to_instagram()

    print("✅ Full Automation Sequence Complete.")
    
    # Render requires a quick response to the web trigger
    return jsonify({"status": "success", "message": "Automation sequence started successfully."}), 200

# Render uses the gunicorn command defined in the Procfile to start the server.
# This block is primarily for local testing purposes.
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
