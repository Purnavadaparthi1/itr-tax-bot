import React from 'react';
import { motion } from 'framer-motion';
import { 
  FileText, 
  Calendar, 
  Shield, 
  TrendingUp,
  BookOpen,
  HelpCircle 
} from 'lucide-react';

const InfoCards = ({ onCardClick }) => {
  const cards = [
    {
      icon: FileText,
      title: 'ITR Forms',
      description: 'Learn about different ITR forms',
      gradient: 'from-blue-600 to-blue-700',
      action: 'Tell me about ITR forms'
    },
    {
      icon: TrendingUp,
      title: 'Tax Deductions',
      description: 'Explore deduction options',
      gradient: 'from-green-600 to-green-700',
      action: 'What deductions can I claim?'
    },
    {
      icon: Calendar,
      title: 'Due Dates',
      description: 'Filing deadlines & penalties',
      gradient: 'from-orange-600 to-orange-700',
      action: 'What are the ITR filing deadlines?'
    },
    {
      icon: Shield,
      title: 'Compliance',
      description: 'Stay compliant with tax laws',
      gradient: 'from-purple-600 to-purple-700',
      action: 'Tell me about tax compliance requirements'
    },
    {
      icon: BookOpen,
      title: 'Full Forms',
      description: 'Tax abbreviations explained',
      gradient: 'from-pink-600 to-pink-700',
      action: 'Show me common tax abbreviations'
    },
    {
      icon: HelpCircle,
      title: 'FAQ',
      description: 'Common tax questions',
      gradient: 'from-indigo-600 to-indigo-700',
      action: 'Answer common tax questions'
    }
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {cards.map((card, index) => (
        <motion.button
          key={index}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: index * 0.1 }}
          whileHover={{ scale: 1.02, y: -4 }}
          whileTap={{ scale: 0.98 }}
          onClick={() => onCardClick(card.action)}
          className="glass-card p-6 text-left group hover:bg-white/10 transition-all duration-300"
        >
          <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${card.gradient} 
                          flex items-center justify-center mb-4 
                          group-hover:scale-110 transition-transform duration-300`}>
            <card.icon className="w-6 h-6 text-white" />
          </div>
          
          <h3 className="text-white font-semibold mb-1 group-hover:text-primary-400 
                         transition-colors duration-300">
            {card.title}
          </h3>
          
          <p className="text-sm text-dark-400 group-hover:text-dark-300 
                        transition-colors duration-300">
            {card.description}
          </p>
        </motion.button>
      ))}
    </div>
  );
};

export default InfoCards;
