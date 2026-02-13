import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Send, 
  Trash2, 
  MessageSquare, 
  Calculator,
  FileUp,
  Menu,
  X,
  Sparkles,
  IndianRupee
} from 'lucide-react';
import { v4 as uuidv4 } from 'uuid';
import ChatMessage, { TypingIndicator } from './components/ChatMessage';
import SuggestionChips from './components/SuggestionChips';
import TaxCalculator from './components/TaxCalculator';
import PayslipUpload from './components/PayslipUpload';
import InfoCards from './components/InfoCards';
import { sendMessage, clearSession } from './utils/api';

function App() {
  const [sessionId] = useState(() => uuidv4());
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [suggestions, setSuggestions] = useState([
    "I'm a salaried employee",
    "I have business income",
    "Help me choose tax regime",
    "Calculate my tax"
  ]);
  const [showCalculator, setShowCalculator] = useState(false);
  const [showPayslipUpload, setShowPayslipUpload] = useState(false);
  const [showSidebar, setShowSidebar] = useState(false);
  const [userContext, setUserContext] = useState({});
  
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // Disabled auto-scroll - user can scroll manually
  // const scrollToBottom = () => {
  //   messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  // };

  // Don't auto-scroll - let user scroll manually
  // useEffect(() => {
  //   scrollToBottom();
  // }, [messages, isTyping]);

  const handleSendMessage = async (messageText) => {
    const text = messageText || inputMessage.trim();
    if (!text) return;

    // Add user message
    const userMessage = {
      id: uuidv4(),
      text,
      isUser: true,
      timestamp: new Date().toISOString()
    };
    
    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsTyping(true);

    try {
      // Send to API
      const response = await sendMessage(sessionId, text, userContext);
      
      // Add assistant response
      const assistantMessage = {
        id: uuidv4(),
        text: response.response,
        isUser: false,
        timestamp: new Date().toISOString()
      };
      
      setMessages(prev => [...prev, assistantMessage]);
      
      // Update suggestions
      if (response.suggestions && response.suggestions.length > 0) {
        setSuggestions(response.suggestions);
      }
      
      // Update context
      if (response.data_collected) {
        setUserContext(prev => ({
          ...prev,
          ...response.data_collected
        }));
      }
      
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage = {
        id: uuidv4(),
        text: 'Sorry, I encountered an error. Please try again.',
        isUser: false,
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleClearChat = async () => {
    if (confirm('Are you sure you want to clear the conversation?')) {
      try {
        await clearSession(sessionId);
        setMessages([]);
        setUserContext({});
        setSuggestions([
          "I'm a salaried employee",
          "I have business income",
          "Help me choose tax regime",
          "Calculate my tax"
        ]);
      } catch (error) {
        console.error('Error clearing session:', error);
      }
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="min-h-screen flex flex-col">
      {/* Animated Background Orbs */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="floating-orb w-96 h-96 bg-primary-600 top-0 -left-48" 
             style={{ animationDelay: '0s' }} />
        <div className="floating-orb w-96 h-96 bg-accent-600 bottom-0 -right-48" 
             style={{ animationDelay: '2s' }} />
        <div className="floating-orb w-64 h-64 bg-purple-600 top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2" 
             style={{ animationDelay: '4s' }} />
      </div>

      {/* Header */}
      <motion.header
        initial={{ y: -20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        className="glass-card border-b border-white/10 sticky top-0 z-50"
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            {/* Logo */}
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary-600 to-primary-700 
                              flex items-center justify-center shadow-lg shadow-primary-500/50">
                <IndianRupee className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-display font-bold gradient-text">
                  ITR Tax Advisor
                </h1>
                <p className="text-xs text-dark-400">AI-Powered CA Assistant</p>
              </div>
            </div>

            {/* Actions */}
            <div className="flex items-center gap-3">
              <button
                onClick={() => setShowCalculator(!showCalculator)}
                className={`btn-secondary flex items-center gap-2 ${
                  showCalculator ? 'bg-primary-600/20 border-primary-500/50' : ''
                }`}
              >
                <Calculator className="w-4 h-4" />
                <span className="hidden sm:inline">Calculator</span>
              </button>

              <button
                onClick={() => setShowPayslipUpload(!showPayslipUpload)}
                className={`btn-secondary flex items-center gap-2 ${
                  showPayslipUpload ? 'bg-primary-600/20 border-primary-500/50' : ''
                }`}
              >
                <FileUp className="w-4 h-4" />
                <span className="hidden sm:inline">Upload</span>
              </button>
              
              {messages.length > 0 && (
                <button
                  onClick={handleClearChat}
                  className="btn-secondary flex items-center gap-2 text-red-400 
                             hover:bg-red-500/10 hover:border-red-500/50"
                >
                  <Trash2 className="w-4 h-4" />
                  <span className="hidden sm:inline">Clear</span>
                </button>
              )}
            </div>
          </div>
        </div>
      </motion.header>

      {/* Main Content */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-full">
          
          {/* Chat Section */}
          <div className="lg:col-span-2 flex flex-col">
            {/* Chat Container */}
            <div className="glass-card flex-1 flex flex-col">
              
              {/* Messages */}
              <div className="flex-1 overflow-y-auto p-6 space-y-6 scrollbar-hide">
                {messages.length === 0 ? (
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="text-center py-12"
                  >
                    <div className="w-20 h-20 mx-auto mb-6 rounded-2xl bg-gradient-to-br 
                                    from-primary-600 to-primary-700 flex items-center justify-center
                                    shadow-2xl shadow-primary-500/50">
                      <Sparkles className="w-10 h-10 text-white" />
                    </div>
                    <h2 className="text-2xl font-display font-bold text-white mb-2">
                      Welcome to ITR Tax Advisor
                    </h2>
                    <p className="text-dark-400 mb-8 max-w-md mx-auto">
                      Your AI-powered Chartered Accountant for Income Tax Return filing.
                      Ask me anything about ITR, deductions, or tax planning!
                    </p>
                    
                    <InfoCards onCardClick={handleSendMessage} />
                  </motion.div>
                ) : (
                  <>
                    {messages.map((msg) => (
                      <ChatMessage
                        key={msg.id}
                        message={msg.text}
                        isUser={msg.isUser}
                        timestamp={msg.timestamp}
                      />
                    ))}
                    {isTyping && <TypingIndicator />}
                  </>
                )}
                <div ref={messagesEndRef} />
              </div>

              {/* Suggestions */}
              {suggestions.length > 0 && !isTyping && (
                <div className="px-6 pb-4">
                  <SuggestionChips 
                    suggestions={suggestions}
                    onSelect={handleSendMessage}
                  />
                </div>
              )}

              {/* Input */}
              <div className="p-6 border-t border-white/10">
                <div className="flex gap-3">
                  <input
                    ref={inputRef}
                    type="text"
                    value={inputMessage}
                    onChange={(e) => setInputMessage(e.target.value)}
                    onKeyPress={handleKeyPress}
                    placeholder="Ask about ITR, deductions, tax planning..."
                    className="flex-1 glass-card px-6 py-4 text-white placeholder-dark-500 
                               focus:outline-none focus:ring-2 focus:ring-primary-500/50 
                               rounded-xl transition-all duration-300"
                    disabled={isTyping}
                  />
                  <button
                    onClick={() => handleSendMessage()}
                    disabled={!inputMessage.trim() || isTyping}
                    className="btn-primary w-14 h-14 flex items-center justify-center 
                               disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <Send className="w-5 h-5" />
                  </button>
                </div>
                
                <div className="mt-3 flex items-center justify-center gap-2 text-xs text-dark-500">
                  <Shield className="w-3 h-3" />
                  <span>Your data is secure. This is AI guidance, not official CA advice.</span>
                </div>
              </div>
            </div>
          </div>

          {/* Sidebar */}
          <div className="lg:col-span-1 space-y-6">
            {/* Tax Calculator */}
            <AnimatePresence>
              {showCalculator && (
                <motion.div
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 20 }}
                >
                  <TaxCalculator onCalculate={(result) => {
                    handleSendMessage(`I calculated tax of ₹${result.total_tax.toFixed(0)} on income of ₹${result.gross_income}`);
                  }} />
                </motion.div>
              )}
            </AnimatePresence>

            {/* Payslip Upload */}
            <AnimatePresence>
              {showPayslipUpload && (
                <motion.div
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 20 }}
                >
                  <PayslipUpload onDataExtracted={(data) => {
                    setUserContext(prev => ({
                      ...prev,
                      ...data
                    }));
                    handleSendMessage(`I've uploaded my payslip. Extracted data: Salary - ₹${Math.round(data.salary_income || 0)}, HRA - ₹${Math.round(data.hra || 0)}. Please help me with tax planning.`);
                  }} />
                </motion.div>
              )}
            </AnimatePresence>

            {/* Info Panel */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="glass-card p-6 space-y-4"
            >
              <h3 className="text-lg font-bold text-white flex items-center gap-2">
                <MessageSquare className="w-5 h-5 text-accent-400" />
                Quick Info
              </h3>
              
              <div className="space-y-3">
                <div className="p-4 rounded-lg bg-white/5 border border-white/10">
                  <p className="text-xs text-dark-400 mb-1">Financial Year</p>
                  <p className="text-white font-semibold">2024-25 (AY 2025-26)</p>
                </div>
                
                <div className="p-4 rounded-lg bg-white/5 border border-white/10">
                  <p className="text-xs text-dark-400 mb-1">ITR Filing Deadline</p>
                  <p className="text-white font-semibold">July 31, 2025</p>
                </div>
                
                <div className="p-4 rounded-lg bg-white/5 border border-white/10">
                  <p className="text-xs text-dark-400 mb-1">Session Status</p>
                  <p className="text-green-400 font-semibold flex items-center gap-2">
                    <span className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
                    Active
                  </p>
                </div>
              </div>
            </motion.div>

            {/* Features */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              className="glass-card p-6 space-y-3"
            >
              <h3 className="text-sm font-semibold text-dark-400 uppercase tracking-wide">
                What I Can Help With
              </h3>
              
              <ul className="space-y-2 text-sm text-dark-300">
                {[
                  'ITR form selection guidance',
                  'Tax regime comparison',
                  'Deduction recommendations',
                  'Tax liability calculation',
                  'Filing process walkthrough',
                  'Compliance requirements',
                  'Full forms & abbreviations'
                ].map((feature, index) => (
                  <li key={index} className="flex items-start gap-2">
                    <Sparkles className="w-4 h-4 text-primary-400 mt-0.5 flex-shrink-0" />
                    <span>{feature}</span>
                  </li>
                ))}
              </ul>
            </motion.div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <motion.footer
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.4 }}
        className="glass-card border-t border-white/10 py-4"
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <p className="text-center text-xs text-dark-500">
            © 2025 ITR Tax Advisor. Powered by AI. For guidance only, consult a CA for complex cases.
          </p>
        </div>
      </motion.footer>
    </div>
  );
}

// Add Shield import
import { Shield } from 'lucide-react';

export default App;
