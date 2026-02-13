import React from 'react';
import { motion } from 'framer-motion';
import { User, Bot, CheckCircle2 } from 'lucide-react';
import ReactMarkdown from 'react-markdown';

const ChatMessage = ({ message, isUser, timestamp }) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className={`flex gap-4 mb-6 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}
    >
      {/* Avatar */}
      <div className={`flex-shrink-0 w-10 h-10 rounded-xl flex items-center justify-center ${
        isUser 
          ? 'bg-gradient-to-br from-primary-600 to-primary-700' 
          : 'glass-card'
      }`}>
        {isUser ? (
          <User className="w-5 h-5 text-white" />
        ) : (
          <Bot className="w-5 h-5 text-primary-400" />
        )}
      </div>

      {/* Message Content */}
      <div className={`flex-1 max-w-[80%] ${isUser ? 'items-end' : 'items-start'} flex flex-col gap-2`}>
        <div className={`${
          isUser 
            ? 'bg-gradient-to-br from-primary-600 to-primary-700 text-white' 
            : 'glass-card text-dark-50'
        } rounded-2xl px-6 py-4 shadow-lg`}>
          {isUser ? (
            <p className="text-sm leading-relaxed">{message}</p>
          ) : (
            <div className="prose prose-invert prose-sm max-w-none">
              <ReactMarkdown
                components={{
                  p: ({node, ...props}) => <p className="mb-2 last:mb-0 leading-relaxed" {...props} />,
                  ul: ({node, ...props}) => <ul className="list-disc list-inside mb-2 space-y-1" {...props} />,
                  ol: ({node, ...props}) => <ol className="list-decimal list-inside mb-2 space-y-1" {...props} />,
                  strong: ({node, ...props}) => <strong className="text-accent-400 font-semibold" {...props} />,
                  code: ({node, inline, ...props}) => 
                    inline ? (
                      <code className="bg-dark-800/50 px-2 py-1 rounded text-accent-400 text-xs font-mono" {...props} />
                    ) : (
                      <code className="block bg-dark-800/50 p-3 rounded-lg text-xs font-mono overflow-x-auto" {...props} />
                    ),
                }}
              >
                {message}
              </ReactMarkdown>
            </div>
          )}
        </div>
        
        {/* Timestamp */}
        {timestamp && (
          <span className="text-xs text-dark-500 px-2">
            {new Date(timestamp).toLocaleTimeString('en-IN', { 
              hour: '2-digit', 
              minute: '2-digit' 
            })}
          </span>
        )}
      </div>
    </motion.div>
  );
};

export const TypingIndicator = () => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex gap-4 mb-6"
    >
      <div className="glass-card w-10 h-10 rounded-xl flex items-center justify-center">
        <Bot className="w-5 h-5 text-primary-400" />
      </div>
      <div className="glass-card rounded-2xl px-6 py-4">
        <div className="typing-indicator text-primary-400">
          <span></span>
          <span></span>
          <span></span>
        </div>
      </div>
    </motion.div>
  );
};

export default ChatMessage;
