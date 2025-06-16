console.log("main.js loaded");

document.addEventListener('DOMContentLoaded', () => {
    console.log("DOM loaded");
    const modeSelection = document.getElementById('mode-selection');
    const chatContainer = document.getElementById('chat-container');
    const stockModeButton = document.getElementById('stock-mode');
    const economyModeButton = document.getElementById('economy-mode');
    const changeModeButton = document.getElementById('change-mode');
    const chatHistory = document.getElementById('chat-history');
    const chatInput = document.getElementById('chat-input');
    const sendButton = document.getElementById('send-button');

    if (!modeSelection || !chatContainer || !stockModeButton || !economyModeButton || !chatHistory || !chatInput || !sendButton) {
        console.error("Missing DOM elements:", {
            modeSelection: !!modeSelection,
            chatContainer: !!chatContainer,
            stockModeButton: !!stockModeButton,
            economyModeButton: !!economyModeButton,
            chatHistory: !!chatHistory,
            chatInput: !!chatInput,
            sendButton: !!sendButton
        });
        return;
    }

    console.log("All DOM elements found");

    let currentMode = null;
    let chatHistoryData = [];
    let awaitingEmail = false;

    function setMode(mode) {
        console.log("Setting mode:", mode);
        currentMode = mode;
        modeSelection.style.display = 'none';
        chatContainer.classList.remove('hidden');
        document.getElementById('current-mode').textContent = mode === 'stock' ? 'Stock Market Mode' : 'Economy Mode';
        chatHistory.innerHTML = '';
        chatHistoryData = [];
        chatInput.focus();
    }

    function showModeSelection() {
        console.log("Showing mode selection");
        currentMode = null;
        modeSelection.style.display = 'flex';
        chatContainer.classList.add('hidden');
        chatInput.value = '';
        awaitingEmail = false;
    }

    function addMessage(content, isUser) {
        console.log("Adding message:", content, isUser);
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${isUser ? 'user' : 'bot'}`;
        messageDiv.textContent = content;
        chatHistory.appendChild(messageDiv);
        chatHistoryData.push({ role: isUser ? 'user' : 'bot', content: content });
        chatHistory.scrollTop = chatHistory.scrollHeight;
    }

    async function sendMessage() {
        const message = chatInput.value.trim();
        if (!message) {
            console.warn("Empty message");
            return;
        }
        if (!currentMode) {
            console.warn("No mode selected");
            addMessage("Please select a mode (Stock Market or Economy) first.", false);
            return;
        }

        addMessage(message, true);
        chatInput.value = '';

        let userEmail = null;
        if (awaitingEmail && message.includes('@')) {
            userEmail = message;
            awaitingEmail = false;
            console.log("Detected email:", userEmail);
        }

        const payload = {
            message: message,
            mode: currentMode,
            chat_history: chatHistoryData,
            user_email: userEmail
        };
        console.log("Sending payload:", payload);

        try {
            const response = await fetch('/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`HTTP error! Status: ${response.status}, Details: ${errorText}`);
            }
            const data = await response.json();
            addMessage(data.response, false);

            if (data.response.includes("Please provide your email address")) {
                awaitingEmail = true;
                console.log("Awaiting email input");
            }
        } catch (error) {
            console.error("Request error:", error);
            addMessage(`Error: ${error.message}`, false);
        }
    }

    stockModeButton.addEventListener('click', () => setMode('stock'));
    economyModeButton.addEventListener('click', () => setMode('economy'));
    changeModeButton.addEventListener('click', showModeSelection);
    sendButton.addEventListener('click', sendMessage);
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage();
    });
});