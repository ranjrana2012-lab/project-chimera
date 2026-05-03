document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('chat-form');
    const input = document.getElementById('prompt-input');
    const messagesArea = document.getElementById('chat-messages');

    // Auto-resize textarea
    input.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
        if (this.value === '') {
            this.style.height = '48px';
        }
    });

    // Handle Enter key (but Shift+Enter for new line)
    input.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            if (this.value.trim() !== '') {
                form.dispatchEvent(new Event('submit'));
            }
        }
    });

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const prompt = input.value.trim();
        if (!prompt) return;

        // Clear input and reset height
        input.value = '';
        input.style.height = '48px';

        // Add user message
        appendUserMessage(prompt);
        
        // Show typing indicator
        const typingIndicator = showTypingIndicator();
        
        // Scroll to bottom
        scrollToBottom();

        try {
            // Call proxy endpoint
            const response = await fetch('/api/interact', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ prompt: prompt })
            });

            const data = await response.json();
            
            // Remove typing indicator
            typingIndicator.remove();

            if (response.ok && data.status === 'success') {
                appendSystemMessage(data.response, data.backend || 'unknown');
            } else {
                appendSystemMessage('Error: ' + (data.detail || data.message || 'Unknown error occurred.'), 'error');
            }
        } catch (error) {
            typingIndicator.remove();
            appendSystemMessage('Network Error: Could not connect to the orchestrator API.', 'error');
            console.error('Interaction error:', error);
        }

        scrollToBottom();
    });

    function appendUserMessage(text) {
        const div = document.createElement('div');
        div.className = 'message user-message';
        div.innerHTML = `
            <div class="avatar user-avatar">U</div>
            <div class="message-content">
                <p>${escapeHTML(text).replace(/\n/g, '<br>')}</p>
            </div>
        `;
        messagesArea.appendChild(div);
    }

    function appendSystemMessage(text, backend) {
        const div = document.createElement('div');
        div.className = 'message system-message';
        
        let backendTag = '';
        if (backend && backend !== 'error') {
            backendTag = `<div class="metadata"><span>Backend: ${backend}</span></div>`;
        }

        div.innerHTML = `
            <div class="avatar chimera-avatar"></div>
            <div class="message-content">
                <p>${escapeHTML(text).replace(/\n/g, '<br>')}</p>
                ${backendTag}
            </div>
        `;
        messagesArea.appendChild(div);
    }

    function showTypingIndicator() {
        const div = document.createElement('div');
        div.className = 'message system-message';
        div.id = 'typing-indicator';
        div.innerHTML = `
            <div class="avatar chimera-avatar"></div>
            <div class="message-content" style="padding: 12px 20px;">
                <div class="typing-indicator">
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                </div>
            </div>
        `;
        messagesArea.appendChild(div);
        return div;
    }

    function scrollToBottom() {
        messagesArea.scrollTop = messagesArea.scrollHeight;
    }

    function escapeHTML(str) {
        return str.replace(/[&<>'"]/g, 
            tag => ({
                '&': '&amp;',
                '<': '&lt;',
                '>': '&gt;',
                "'": '&#39;',
                '"': '&quot;'
            }[tag] || tag)
        );
    }
});
