import pkg from 'whatsapp-web.js';
const { Client, LocalAuth } = pkg;
import qrcode from 'qrcode-terminal';
import axios from 'axios';
import dotenv from 'dotenv';
import { fileURLToPath } from 'url';
import { dirname } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Load environment variables
dotenv.config();

const PYTHON_API_URL = process.env.PYTHON_API_URL || 'http://localhost:8000';
const SESSION_NAME = process.env.SESSION_NAME || 'kuapa-ai-session';

// Store active conversations for context
const activeConversations = new Map();

console.log('🌾 Kuapa AI WhatsApp Bot - Starting...\n');

// Initialize WhatsApp client
const client = new Client({
    authStrategy: new LocalAuth({
        clientId: SESSION_NAME
    }),
    puppeteer: {
        headless: true,
        args: [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-accelerated-2d-canvas',
            '--no-first-run',
            '--no-zygote',
            '--single-process',
            '--disable-gpu'
        ]
    }
});

// QR Code event - scan this to authenticate
client.on('qr', (qr) => {
    console.log('📱 Scan this QR code with your WhatsApp mobile app:\n');
    qrcode.generate(qr, { small: true });
    console.log('\nWaiting for authentication...\n');
});

// Ready event - bot is authenticated and ready
client.on('ready', () => {
    console.log('✅ Kuapa AI WhatsApp Bot is ready!');
    console.log(`📞 Bot Phone Number: ${client.info.wid.user}`);
    console.log(`🔗 Connected to Python Backend: ${PYTHON_API_URL}`);
    console.log('🌾 Ready to help farmers with agricultural advice!\n');
});

// Authentication events
client.on('authenticated', () => {
    console.log('🔐 Authentication successful!');
});

client.on('auth_failure', (msg) => {
    console.error('❌ Authentication failed:', msg);
});

// Disconnection event
client.on('disconnected', (reason) => {
    console.log('📴 WhatsApp client disconnected:', reason);
    console.log('♻️  Attempting to reconnect...');
});

// Message handler
client.on('message', async (message) => {
    try {
        const from = message.from;
        const messageBody = message.body.trim();
        const contact = await message.getContact();
        const contactName = contact.pushname || contact.name || from;

        // Ignore group messages and status updates
        if (from.includes('@g.us') || from.includes('status@broadcast')) {
            return;
        }

        // Log incoming message
        console.log(`\n📩 Message from ${contactName} (${from}):`);
        console.log(`   "${messageBody}"`);

        // Send typing indicator
        const chat = await message.getChat();
        await chat.sendStateTyping();

        // Handle special commands
        if (messageBody.toLowerCase() === '/start' || messageBody.toLowerCase() === 'hello' || messageBody.toLowerCase() === 'hi') {
            const welcomeMessage = `🌾 *Welcome to Kuapa AI!*

I'm your agricultural advisor, here to help Ghanaian farmers with:
🌱 Crop management advice
🐛 Pest and disease control
🌧️ Irrigation and soil management
📅 Planting schedules
💡 Farming best practices

*How can I help you today?*

Example questions:
• How do I control fall armyworm?
• What are signs of nitrogen deficiency?
• When should I plant maize?
• How do I manage weeds?`;

            await chat.clearState();
            await message.reply(welcomeMessage);
            console.log(`   ✅ Sent welcome message`);
            return;
        }

        if (messageBody.toLowerCase() === '/help') {
            const helpMessage = `📚 *Kuapa AI Help*

Ask me any agricultural question and I'll provide advice based on reliable sources from:
• Ministry of Food and Agriculture (MoFA) Ghana
• Agricultural research institutions
• Extension officer guidelines

You can ask about:
• Crop diseases and pests
• Soil management
• Planting techniques
• Harvesting and storage
• And much more!

Just type your question and I'll do my best to help! 🌾`;

            await chat.clearState();
            await message.reply(helpMessage);
            console.log(`   ✅ Sent help message`);
            return;
        }

        // Process the message through RAG pipeline
        console.log(`   🔄 Processing through RAG pipeline...`);

        const startTime = Date.now();

        // Call Python backend
        const response = await axios.post(`${PYTHON_API_URL}/chat`, {
            message: messageBody
        }, {
            timeout: 60000, // 60 second timeout
            headers: {
                'Content-Type': 'application/json'
            }
        });

        const processingTime = Date.now() - startTime;

        const aiResponse = response.data.response;
        const metadata = response.data.metadata || {};

        console.log(`   ⚡ Processed in ${processingTime}ms`);
        console.log(`   🤖 AI Response: "${aiResponse.substring(0, 100)}${aiResponse.length > 100 ? '...' : ''}"`);

        // Send response back to WhatsApp
        await chat.clearState();
        await message.reply(aiResponse);

        console.log(`   ✅ Message sent successfully\n`);

        // Store conversation context
        activeConversations.set(from, {
            lastMessage: messageBody,
            lastResponse: aiResponse,
            timestamp: new Date()
        });

    } catch (error) {
        console.error(`   ❌ Error processing message:`, error.message);

        // Send error message to user
        try {
            const chat = await message.getChat();
            await chat.clearState();

            let errorMessage = '';

            if (error.code === 'ECONNREFUSED') {
                errorMessage = '⚠️ Sorry, I\'m having trouble connecting to my brain (backend service is down). Please try again in a moment.';
            } else if (error.code === 'ETIMEDOUT' || error.message.includes('timeout')) {
                errorMessage = '⚠️ Sorry, that took too long to process. Please try asking a simpler question or try again.';
            } else {
                errorMessage = '⚠️ Sorry, I encountered an error processing your message. Please try again or rephrase your question.';
            }

            await message.reply(errorMessage);
            console.log(`   ⚠️  Sent error message to user\n`);
        } catch (sendError) {
            console.error(`   ❌ Failed to send error message:`, sendError.message);
        }
    }
});

// Handle message reactions (optional - for future features)
client.on('message_reaction', async (reaction) => {
    console.log('👍 Reaction received:', reaction.emoji);
});

// Initialize the client
console.log('🚀 Initializing WhatsApp client...\n');
client.initialize();

// Graceful shutdown
process.on('SIGINT', async () => {
    console.log('\n\n🛑 Shutting down gracefully...');
    await client.destroy();
    console.log('✅ WhatsApp client destroyed');
    process.exit(0);
});

process.on('SIGTERM', async () => {
    console.log('\n\n🛑 Received SIGTERM, shutting down...');
    await client.destroy();
    console.log('✅ WhatsApp client destroyed');
    process.exit(0);
});

// Health check endpoint simulation (for monitoring)
setInterval(() => {
    const state = client.info ? 'CONNECTED' : 'DISCONNECTED';
    console.log(`💓 Health Check: Bot is ${state} | Active conversations: ${activeConversations.size}`);
}, 300000); // Every 5 minutes
