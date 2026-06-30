import { useEffect, useRef, useState } from 'react';
import type { ChatMessage, CityLocation } from '../api';
import { sendChat } from '../api';

interface Props {
  selectedCity: CityLocation | null;
  storeSize: number;
}

const SUGGESTIONS = [
  'What revenue can we expect here?',
  'Who are the main sunglasses competitors?',
  'When is peak season for this city?',
  'Is there an existing Meller store nearby?',
  'Should we open a store in this location?',
  'How does tourism affect revenue?',
];

export default function ChatPanel({ selectedCity, storeSize }: Props) {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: 'assistant',
      content: 'Welcome to MELLER Geo Intelligence. I\'m your expansion advisor — ask me about revenue projections, sunglasses competitors, tourist seasons, or our MELLER Factory store locations. Select a city on the map to get started.',
    },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async (text?: string) => {
    const content = (text ?? input).trim();
    if (!content || loading) return;

    const userMsg: ChatMessage = { role: 'user', content };
    const newMessages = [...messages, userMsg];
    setMessages(newMessages);
    setInput('');
    setLoading(true);

    try {
      const response = await sendChat(newMessages, selectedCity?.id, storeSize);
      setMessages([...newMessages, response.message]);
    } catch {
      setMessages([
        ...newMessages,
        { role: 'assistant', content: 'Sorry, I couldn\'t process that. Please try again.' },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="chat-panel">
      <div className="chat-header">
        <h2>AI Advisor</h2>
        {selectedCity && (
          <span className="chat-context">{selectedCity.city}, {selectedCity.country}</span>
        )}
      </div>

      <div className="chat-messages">
        {messages.map((msg, i) => (
          <div key={i} className={`chat-bubble ${msg.role}`}>
            <div className="chat-bubble-content">{msg.content}</div>
          </div>
        ))}
        {loading && (
          <div className="chat-bubble assistant">
            <div className="chat-bubble-content typing">Analyzing...</div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {!loading && messages.length <= 2 && (
        <div className="chat-suggestions">
          {SUGGESTIONS.map((s) => (
            <button key={s} className="suggestion-chip" onClick={() => handleSend(s)}>
              {s}
            </button>
          ))}
        </div>
      )}

      <div className="chat-input-area">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          placeholder={selectedCity ? `Ask about ${selectedCity.city}...` : 'Select a city first...'}
          disabled={loading}
        />
        <button className="chat-send" onClick={() => handleSend()} disabled={loading || !input.trim()}>
          Send
        </button>
      </div>
    </div>
  );
}
