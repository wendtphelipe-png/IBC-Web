
document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('transcript-search');
    const searchMeta = document.getElementById('search-results-meta');
    const videoLibrary = document.getElementById('video-library');
    const allCards = Array.from(videoLibrary.querySelectorAll('.glass-card'));

    console.log('[Search] Initializing...');
    console.log('[Search] VIDEO_DB:', window.VIDEO_DB);

    // Store original HTML of cards and search data
    const videoData = [];
    allCards.forEach(card => {
        const id = card.getAttribute('onclick')?.match(/video_(\d+)/)?.[1];
        console.log(`[Search] Found card with ID: ${id}`);
        if (id) {
            videoData.push({
                id: id,
                element: card,
                originalHtml: card.innerHTML
            });
        }
    });
    console.log(`[Search] Total video cards tracked: ${videoData.length}`);

    searchInput.addEventListener('input', (e) => {
        const term = e.target.value.toLowerCase().trim();

        if (term.length < 2) {
            searchMeta.style.display = 'none';
            videoData.forEach(v => {
                v.element.style.display = 'flex';
                v.element.innerHTML = v.originalHtml;
            });
            return;
        }

        searchMeta.style.display = 'block';
        searchMeta.textContent = `SEARCHING TRANSCRIPTS FOR: "${term.toUpperCase()}"...`;

        let foundCount = 0;
        videoData.forEach(v => {
            const dbEntry = window.VIDEO_DB.find(db => db.id.toString() === v.id.toString());
            if (!dbEntry) return;

            const inTitle = dbEntry.title.toLowerCase().includes(term);
            const inDesc = dbEntry.description.toLowerCase().includes(term);
            const inTranscript = dbEntry.transcript.toLowerCase().includes(term);

            if (inTitle || inDesc || inTranscript) {
                v.element.style.display = 'flex';
                foundCount++;

                // If found in transcript, show snippet
                if (inTranscript && !inTitle && !inDesc) {
                    const index = dbEntry.transcript.toLowerCase().indexOf(term);
                    const start = Math.max(0, index - 60);
                    const end = Math.min(dbEntry.transcript.length, index + 60);
                    let snippet = dbEntry.transcript.substring(start, end);

                    // Highlight the term
                    const regex = new RegExp(`(${term})`, 'gi');
                    snippet = snippet.replace(regex, '<mark style="background: var(--cyan); color: black; border-radius: 4px; padding: 0 4px;">$1</mark>');

                    const snippetHtml = `
                        <div style="margin-top: 1rem; padding: 1rem; background: rgba(0,245,255,0.1); border-radius: 8px; font-size: 0.8rem; border-left: 2px solid var(--cyan);">
                            <span style="color: var(--gold); display: block; margin-bottom: 5px; font-size: 10px; letter-spacing: 1px;">TRANSCRIPT MATCH:</span>
                            "...${snippet}..."
                        </div>
                    `;

                    // Restore original then append snippet
                    v.element.innerHTML = v.originalHtml + snippetHtml;
                } else {
                    v.element.innerHTML = v.originalHtml;
                }
            } else {
                v.element.style.display = 'none';
            }
        });

        searchMeta.textContent = `FOUND ${foundCount} RELEVANT SESSIONS FOR "${term.toUpperCase()}"`;
    });
});
