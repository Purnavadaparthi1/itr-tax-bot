import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Calculator, TrendingDown, TrendingUp, Info, IndianRupee, AlertCircle } from 'lucide-react';
import { calculateTax } from '../utils/api';

const TaxCalculator = ({ onCalculate }) => {
  const [income, setIncome] = useState('');
  const [regime, setRegime] = useState('new');
  const [deductions, setDeductions] = useState({
    section_80c: 0,
    section_80d: 0,
    section_80e: 0,
    section_80g: 0,
    section_80tta: 0,
    home_loan_interest: 0,
  });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleCalculate = async (e) => {
    e?.preventDefault?.();
    
    // Reset error
    setError(null);
    
    if (!income || parseFloat(income) <= 0) {
      setError('Please enter a valid income amount');
      return;
    }

    setLoading(true);
    try {
      console.log('Calculating tax with:', { income: parseFloat(income), regime, deductions });
      
      const taxResult = await calculateTax(parseFloat(income), deductions, regime);
      
      console.log('Tax calculation result:', taxResult);
      
      setResult(taxResult);
      if (onCalculate) onCalculate(taxResult);
    } catch (error) {
      console.error('Tax calculation error:', error);
      setError(error.response?.data?.detail || error.message || 'Failed to calculate tax. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(amount);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass-card p-6 space-y-6"
    >
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-accent-600 to-accent-700 
                        flex items-center justify-center">
          <Calculator className="w-6 h-6 text-white" />
        </div>
        <div>
          <h3 className="text-xl font-bold text-white">Tax Calculator</h3>
          <p className="text-sm text-dark-400">Calculate your income tax liability</p>
        </div>
      </div>

      {/* Income Input */}
      <div>
        <label className="block text-sm font-medium text-dark-300 mb-2">
          Gross Annual Income
        </label>
        <div className="relative">
          <IndianRupee className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-dark-500" />
          <input
            type="number"
            value={income}
            onChange={(e) => setIncome(e.target.value)}
            placeholder="Enter your total income"
            className="w-full pl-12 pr-4 py-3 glass-card text-white placeholder-dark-500 
                       focus:outline-none focus:ring-2 focus:ring-accent-500/50 rounded-xl"
          />
        </div>
      </div>

      {/* Regime Selection */}
      <div>
        <label className="block text-sm font-medium text-dark-300 mb-2">
          Tax Regime
        </label>
        <div className="grid grid-cols-2 gap-3">
          <button
            onClick={() => setRegime('new')}
            className={`py-3 px-4 rounded-xl font-medium transition-all duration-300 ${
              regime === 'new'
                ? 'bg-gradient-to-r from-primary-600 to-primary-700 text-white shadow-lg'
                : 'glass-card text-dark-400 hover:bg-white/10'
            }`}
          >
            New Regime
          </button>
          <button
            onClick={() => setRegime('old')}
            className={`py-3 px-4 rounded-xl font-medium transition-all duration-300 ${
              regime === 'old'
                ? 'bg-gradient-to-r from-primary-600 to-primary-700 text-white shadow-lg'
                : 'glass-card text-dark-400 hover:bg-white/10'
            }`}
          >
            Old Regime
          </button>
        </div>
      </div>

      {/* Deductions (Old Regime) */}
      {regime === 'old' && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          className="space-y-3"
        >
          <label className="block text-sm font-medium text-dark-300">
            Deductions (Old Regime Only)
          </label>
          
          {Object.entries(deductions).map(([key, value]) => (
            <div key={key}>
              <label className="block text-xs text-dark-400 mb-1 capitalize">
                {key.replace(/_/g, ' ')}
              </label>
              <input
                type="number"
                value={value}
                onChange={(e) => setDeductions({
                  ...deductions,
                  [key]: parseFloat(e.target.value) || 0
                })}
                className="w-full px-4 py-2 glass-card text-white text-sm placeholder-dark-500 
                           focus:outline-none focus:ring-2 focus:ring-accent-500/50 rounded-lg"
                placeholder="0"
              />
            </div>
          ))}
        </motion.div>
      )}

      {/* Error Alert */}
      {error && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="p-4 rounded-lg bg-red-500/10 border border-red-500/30 flex items-start gap-3"
        >
          <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-medium text-red-300">Error</p>
            <p className="text-xs text-red-200 mt-1">{error}</p>
          </div>
        </motion.div>
      )}

      {/* Calculate Button */}
      <button
        onClick={handleCalculate}
        disabled={loading || !income}
        className="w-full btn-primary flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
      >
        {loading ? (
          <>
            <div className="typing-indicator">
              <span></span>
              <span></span>
              <span></span>
            </div>
            <span>Calculating...</span>
          </>
        ) : (
          <>
            <Calculator className="w-5 h-5" />
            <span>Calculate Tax</span>
          </>
        )}
      </button>

      {/* Results */}
      {result && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-3 pt-4 border-t border-white/10"
        >
          <div className="flex items-center justify-between">
            <span className="text-dark-400">Gross Income</span>
            <span className="text-white font-semibold">{formatCurrency(result.gross_income)}</span>
          </div>
          
          <div className="flex items-center justify-between">
            <span className="text-dark-400">Total Deductions</span>
            <span className="text-green-400 font-semibold">- {formatCurrency(result.total_deductions)}</span>
          </div>
          
          <div className="flex items-center justify-between">
            <span className="text-dark-400">Taxable Income</span>
            <span className="text-white font-semibold">{formatCurrency(result.taxable_income)}</span>
          </div>
          
          <div className="h-px bg-gradient-to-r from-transparent via-white/20 to-transparent" />
          
          <div className="flex items-center justify-between text-lg">
            <span className="text-dark-300 font-semibold">Total Tax Payable</span>
            <span className="text-accent-400 font-bold text-xl">
              {formatCurrency(result.total_tax)}
            </span>
          </div>
          
          <div className="glass-card p-3 rounded-lg">
            <div className="flex items-start gap-2">
              <Info className="w-4 h-4 text-primary-400 mt-0.5" />
              <p className="text-xs text-dark-400">
                Tax calculated under <span className="text-white font-medium">{result.regime_used}</span> regime.
                Includes 4% Health & Education Cess.
              </p>
            </div>
          </div>
        </motion.div>
      )}
    </motion.div>
  );
};

export default TaxCalculator;
