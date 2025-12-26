let ws = null;
let clientId = null;
let reconnectAttempts = 0;
const maxReconnectAttempts = 5;

const messageInput = document.getElementById('message-input');
const sendButton = document.getElementById('send-button');
const chatMessages = document.getElementById('chat-messages');
const connectionStatus = document.getElementById('connection-status');
const connectionText = document.getElementById('connection-text');

function generateClientId() {
    return 'client_' + Math.random().toString(36).substr(2, 9);
}

function updateConnectionStatus(status) {
    connectionStatus.className = 'status-dot ' + status;
    const statusTexts = {
        'connecting': 'Connecting...',
        'connected': 'Connected',
        'disconnected': 'Disconnected'
    };
    connectionText.textContent = statusTexts[status] || status;
}

function connectWebSocket() {
    if (!clientId) {
        clientId = generateClientId();
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/${clientId}`;

    updateConnectionStatus('connecting');

    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
        console.log('WebSocket connected');
        updateConnectionStatus('connected');
        reconnectAttempts = 0;
        addSystemMessage('Connected to Kuapa AI');
    };

    ws.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);

            removeTypingIndicator();

            if (data.error) {
                addSystemMessage('Error: ' + data.error);
            } else {
                addMessage('assistant', data.response, data.timings_ms);
            }
        } catch (e) {
            console.error('Error parsing message:', e);
            addSystemMessage('Error processing response');
        }
    };

    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        updateConnectionStatus('disconnected');
    };

    ws.onclose = () => {
        console.log('WebSocket disconnected');
        updateConnectionStatus('disconnected');

        if (reconnectAttempts < maxReconnectAttempts) {
            reconnectAttempts++;
            const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), 10000);
            addSystemMessage(`Reconnecting in ${delay / 1000} seconds...`);
            setTimeout(connectWebSocket, delay);
        } else {
            addSystemMessage('Connection lost. Please refresh the page.');
        }
    };
}

function addMessage(sender, text, timings = null) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}`;

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.textContent = text;

    if (timings) {
        const timingDiv = document.createElement('div');
        timingDiv.className = 'timing-info';
        timingDiv.textContent = `Response time: ${timings.total}ms`;
        contentDiv.appendChild(timingDiv);
    }

    messageDiv.appendChild(contentDiv);
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function addSystemMessage(text) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message system';

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.textContent = text;

    messageDiv.appendChild(contentDiv);
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function addTypingIndicator() {
    const typingDiv = document.createElement('div');
    typingDiv.className = 'message assistant typing-message';
    typingDiv.innerHTML = `
        <div class="typing-indicator">
            <span></span>
            <span></span>
            <span></span>
        </div>
    `;
    chatMessages.appendChild(typingDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function removeTypingIndicator() {
    const typingMessage = chatMessages.querySelector('.typing-message');
    if (typingMessage) {
        typingMessage.remove();
    }
}

function sendMessage() {
    const message = messageInput.value.trim();

    if (!message) return;

    if (!ws || ws.readyState !== WebSocket.OPEN) {
        addSystemMessage('Not connected. Please wait...');
        return;
    }

    addMessage('user', message);
    addTypingIndicator();

    ws.send(message);

    messageInput.value = '';
    messageInput.focus();
}

sendButton.addEventListener('click', sendMessage);

messageInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        sendMessage();
    }
});

document.querySelectorAll('.suggestion-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const question = btn.dataset.question;
        messageInput.value = question;
        sendMessage();
    });
});

connectWebSocket();

addSystemMessage('Welcome to Kuapa AI! Ask any questions about farming, crops, pests, or diseases.');
