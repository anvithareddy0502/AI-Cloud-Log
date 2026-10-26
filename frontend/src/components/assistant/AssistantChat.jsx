import React, { useState, useRef, useEffect } from 'react';
import Card from '../common/Card';
import Button from '../common/Button';
import SuggestedPrompts from './SuggestedPrompts';
import ChatMessage from './ChatMessage';
import { Send, Bot, Trash2, Sparkles, RefreshCw } from 'lucide-react';
import { api } from '../../services/api';

export default function AssistantChat() {
  const [messages, setMessages] = useState([
    {
      id: 'msg-welcome',
      role: 'assistant',
      content: "Hello! I am your **AI-CLAR Cloud Assistant**. I correlate multi-server telemetry, anomaly patterns, and log events across your cluster to diagnose incidents and isolate root causes in seconds.\n\nAsk me any question about your servers, errors, or security events below.",
      timestamp: 'Just now',
      suggested_followups: [
        "What are today's critical errors?",
        "Why did Server-03 fail?",
        "Are there any security threats?"
      ]
    }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const scrollRef = useRef(null);

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const handleSendMessage = async (textToSend) => {
    const query = textToSend || input;
    if (!query.trim() || isLoading) return;

    const userMsg = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: query,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await api.sendAssistantQuery(query);
      const assistantMsg = {
        id: response.message_id || `asst-${Date.now()}`,
        role: 'assistant',
        content: response.answer,
        timestamp: response.timestamp || new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        related_server: response.related_server,
        related_incident_id: response.related_incident_id,
        confidence_score: response.confidence_score,
        key_evidence: response.key_evidence,
        suggested_followups: response.suggested_followups
      };
      setMessages(prev => [...prev, assistantMsg]);
    } catch (err) {
      console.error("AI Assistant query error:", err);
      const errMsg = {
        id: `err-${Date.now()}`,
        role: 'assistant',
        content: "Failed to communicate with AI-CLAR assistant engine. Please verify that the backend telemetry service is running.",
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        suggested_followups: ["What is the cluster health?"]
      };
      setMessages(prev => [...prev, errMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleClear = () => {
    setMessages([
      {
        id: 'msg-welcome',
        role: 'assistant',
        content: "Conversation history cleared. How can I assist with your cloud cluster analysis?",
        timestamp: 'Just now',
        suggested_followups: [
          "What are today's critical errors?",
          "Which server has the most problems?"
        ]
      }
    ]);
  };

  return (
    <Card className="flex flex-col h-[calc(100vh-12rem)] overflow-hidden">
      {/* Header */}
      <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between bg-slate-50/50">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-base font-bold text-slate-900">AI Cloud Assistant</h2>
            <span className="text-[10px] font-semibold uppercase tracking-wider bg-blue-50 text-blue-700 px-2 py-0.5 rounded border border-blue-200">
              RCA Engine
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            Ask questions about your cloud environment and logs.
          </p>
        </div>

        <button
          onClick={handleClear}
          title="Clear Conversation"
          className="p-1.5 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-md transition-colors"
        >
          <Trash2 className="w-4 h-4" />
        </button>
      </div>

      {/* Messages viewport */}
      <div className="flex-1 p-6 overflow-y-auto space-y-6 bg-slate-50/30">
        {messages.map((m) => (
          <ChatMessage
            key={m.id}
            message={m}
            onSelectFollowup={(q) => handleSendMessage(q)}
          />
        ))}

        {isLoading && (
          <div className="flex gap-3.5 justify-start">
            <div className="w-8 h-8 rounded-lg bg-blue-600 text-white flex items-center justify-center shrink-0 shadow-xs">
              <Bot className="w-4 h-4" />
            </div>
            <div className="p-4 bg-white border border-slate-200 rounded-lg shadow-xs flex items-center gap-2 text-xs text-slate-500">
              <RefreshCw className="w-3.5 h-3.5 text-blue-600 animate-spin" />
              <span>Analyzing correlated logs & anomaly models...</span>
            </div>
          </div>
        )}

        <div ref={scrollRef} />
      </div>

      {/* Input area */}
      <div className="p-4 bg-white border-t border-slate-200">
        <SuggestedPrompts onSelectPrompt={(q) => handleSendMessage(q)} />

        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSendMessage();
          }}
          className="flex items-center gap-2"
        >
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about your cloud logs..."
            disabled={isLoading}
            className="flex-1 px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-lg text-xs placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all font-sans"
          />
          <Button
            type="submit"
            variant="primary"
            size="md"
            icon={Send}
            disabled={!input.trim() || isLoading}
          >
            Send
          </Button>
        </form>
      </div>
    </Card>
  );
}
