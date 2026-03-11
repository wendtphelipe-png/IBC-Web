import json
import os
import re

DB_FILE = 'data/database.json'
TEMPLATES_DIR = 'templates'
DEPLOY_DIR = 'deploy'

def load_db():
    with open(DB_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def generate_video_pages(videos):
    with open(os.path.join(TEMPLATES_DIR, 'video.html'), 'r', encoding='utf-8') as f:
        template = f.read()
    
    for video in videos:
        print(f"[*] Generating page for: {video['title']}")
        
        # Build Chapters HTML
        chapters_html = ""
        for chapter in video.get('chapters', []):
            chapters_html += f"""
            <li class="chapter-item" onclick="seekTo('{chapter['time']}')">
                <span class="chapter-time">{chapter['time']}</span>
                <span class="chapter-title">{chapter['title']}</span>
            </li>
            """
        
        page_content = template
        page_content = page_content.replace('{{VIDEO_TITLE}}', video['title'])
        page_content = page_content.replace('{{VIDEO_ID}}', video['id'])
        page_content = page_content.replace('{{VIDEO_DESCRIPTION}}', video['description'])
        page_content = page_content.replace('{{VIDEO_DURATION}}', video['duration'])
        page_content = page_content.replace('{{VIDEO_DATE}}', video['publish_date'])
        page_content = page_content.replace('{{CHAPTERS_LIST}}', chapters_html)
        
        output_path = os.path.join(DEPLOY_DIR, f"video_{video['id']}.html")
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(page_content)

def generate_index_page(videos):
    with open(os.path.join(TEMPLATES_DIR, 'index.html'), 'r', encoding='utf-8') as f:
        template = f.read()
    
    # Inject Search Data for client-side searching
    search_data = json.dumps(videos, ensure_ascii=False)
    injection = f"<script>window.VIDEO_DB = {search_data};</script>\n<script src='search.js'></script>"
    template = template.replace('</body>', f"{injection}\n</body>")

    cards_html = ""
    for video in videos:
        cards_html += f"""
        <div class="glass-card" onclick="location.href='video_{video['id']}.html'" style="cursor: pointer; padding: 0; display: flex; flex-direction: column;">
            <div style="width: 100%; height: 200px; background: url('{video['thumbnail']}') center/cover no-repeat; border-bottom: 1px solid var(--border-gold);"></div>
            <div style="padding: 2rem;">
                <span class="card-label">{video['duration']} • {video['publish_date']}</span>
                <h3 class="card-title" style="font-size: 1.4rem; min-height: 4rem;">{video['title']}</h3>
                <p style="font-size: 0.8rem; color: rgba(255,255,255,0.5); line-height: 1.4;">{video['description'][:150]}...</p>
                <div style="margin-top: 1.5rem; display: flex; justify-content: flex-end; align-items: center;">
                    <button class="cta-btn" style="padding: 0.5rem 1rem; font-size: 0.6rem; border-radius: 6px;">Watch Session</button>
                </div>
            </div>
        </div>
        """
    
    page_content = template.replace('{{VIDEO_CARDS}}', cards_html)
    
    output_path = os.path.join(DEPLOY_DIR, "index.html")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(page_content)

if __name__ == "__main__":
    if not os.path.exists(DEPLOY_DIR):
        os.makedirs(DEPLOY_DIR)
        
    db = load_db()
    generate_video_pages(db['videos'])
    generate_index_page(db['videos'])
    print("[OK] Site generated successfully in /deploy")
