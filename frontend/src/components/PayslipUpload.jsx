import React, { useState, useRef } from 'react';
import { motion } from 'framer-motion';
import { Upload, FileUp, AlertCircle, CheckCircle, Loader } from 'lucide-react';
import { uploadPayslip } from '../utils/api';

const PayslipUpload = ({ onDataExtracted }) => {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const fileInputRef = useRef(null);

  const handleFileChange = (e) => {
    const selectedFile = e.target.files?.[0];
    if (!selectedFile) return;

    // Validate file type
    const validTypes = ['application/pdf', 'image/png', 'image/jpeg'];
    if (!validTypes.includes(selectedFile.type)) {
      setError('Please upload a PDF or image file (PNG/JPG)');
      setFile(null);
      return;
    }

    // Validate file size (max 10MB)
    if (selectedFile.size > 10 * 1024 * 1024) {
      setError('File size must be less than 10MB');
      setFile(null);
      return;
    }

    setFile(selectedFile);
    setError(null);
  };

  const handleUpload = async () => {
    if (!file) {
      setError('Please select a file first');
      return;
    }

    setUploading(true);
    setError(null);

    try {
      console.log('Uploading payslip:', file.name);
      const response = await uploadPayslip(file);

      console.log('Payslip upload response:', response);

      if (response.success) {
        setResult(response);
        
        // Notify parent component with extracted data
        if (onDataExtracted && response.data_collected) {
          onDataExtracted(response.data_collected);
        }
      } else {
        setError(response.message || 'Failed to analyze payslip');
      }
    } catch (err) {
      console.error('Payslip upload error:', err);
      setError(err.response?.data?.detail || err.message || 'Error uploading payslip. Please try again.');
    } finally {
      setUploading(false);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    
    const droppedFile = e.dataTransfer.files?.[0];
    if (droppedFile) {
      handleFileChange({ target: { files: [droppedFile] } });
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass-card p-6 space-y-6"
    >
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary-600 to-primary-700 
                        flex items-center justify-center">
          <FileUp className="w-6 h-6 text-white" />
        </div>
        <div>
          <h3 className="text-xl font-bold text-white">Upload Payslip</h3>
          <p className="text-sm text-dark-400">Auto-extract salary details from PDF/Image</p>
        </div>
      </div>

      {/* Upload Area */}
      {!result?.success && (
        <div
          onDragOver={handleDragOver}
          onDrop={handleDrop}
          className="border-2 border-dashed border-white/20 rounded-xl p-8 text-center 
                     hover:border-primary-500/50 hover:bg-primary-500/5 transition-all cursor-pointer 
                     group"
          onClick={() => fileInputRef.current?.click()}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.png,.jpg,.jpeg"
            onChange={handleFileChange}
            className="hidden"
          />

          <div className="space-y-3">
            <div className="flex justify-center">
              <Upload className="w-12 h-12 text-primary-400 group-hover:scale-110 transition-transform" />
            </div>

            <div>
              <p className="text-white font-medium mb-1">
                {file ? file.name : 'Click to upload or drag and drop'}
              </p>
              <p className="text-xs text-dark-400">
                PDF or image (PNG, JPG) • Max 10MB
              </p>
            </div>

            {file && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  setFile(null);
                  setError(null);
                }}
                className="text-xs text-red-400 hover:text-red-300"
              >
                Clear selection
              </button>
            )}
          </div>
        </div>
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

      {/* Success Alert */}
      {result?.success && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="p-4 rounded-lg bg-green-500/10 border border-green-500/30 flex items-start gap-3"
        >
          <CheckCircle className="w-5 h-5 text-green-400 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-medium text-green-300">{result.message}</p>
            {result.extracted_data && (
              <div className="mt-3 space-y-2 text-xs text-green-200">
                {result.extracted_data.employee_name && (
                  <p>👤 {result.extracted_data.employee_name}</p>
                )}
                {result.extracted_data.basic_salary && (
                  <p>💰 Salary: ₹{Math.round(result.extracted_data.basic_salary)}</p>
                )}
                {result.extracted_data.HRA && (
                  <p>🏠 HRA: ₹{Math.round(result.extracted_data.HRA)}</p>
                )}
              </div>
            )}
          </div>
        </motion.div>
      )}

      {/* Upload Button */}
      {file && !uploading && !result?.success && (
        <button
          onClick={handleUpload}
          className="w-full btn-primary flex items-center justify-center gap-2"
        >
          <FileUp className="w-5 h-5" />
          <span>Analyze Payslip</span>
        </button>
      )}

      {/* Loading State */}
      {uploading && (
        <div className="flex flex-col items-center justify-center py-6 space-y-3">
          <Loader className="w-8 h-8 text-primary-400 animate-spin" />
          <p className="text-sm text-dark-300">Analyzing payslip...</p>
          <p className="text-xs text-dark-500">This may take a moment</p>
        </div>
      )}

      {/* Extracted Data Display */}
      {result?.success && result?.extracted_data && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="space-y-3 pt-4 border-t border-white/10"
        >
          <h4 className="text-sm font-semibold text-white">Extracted Details:</h4>

          <div className="grid grid-cols-2 gap-2 text-xs">
            {Object.entries(result.extracted_data).map(([key, value]) => (
              value && value !== 'null' && (
                <div key={key} className="p-2 rounded-lg bg-white/5 border border-white/10">
                  <p className="text-dark-400 capitalize">{key.replace(/_/g, ' ')}</p>
                  <p className="text-white font-semibold truncate">{String(value)}</p>
                </div>
              )
            ))}
          </div>

          <button
            onClick={() => {
              setResult(null);
              setFile(null);
              fileInputRef.current?.click();
            }}
            className="w-full btn-secondary text-sm mt-4"
          >
            Upload Another Payslip
          </button>
        </motion.div>
      )}

      {/* Hint Text */}
      <div className="p-3 rounded-lg bg-blue-500/10 border border-blue-500/20 flex items-start gap-2">
        <AlertCircle className="w-4 h-4 text-blue-400 flex-shrink-0 mt-0.5" />
        <div className="text-xs text-blue-200">
          <p className="font-medium">💡 Tip:</p>
          <p className="mt-1">Your payslip will be analyzed to auto-fill income and tax details. You can still edit or skip if needed.</p>
        </div>
      </div>
    </motion.div>
  );
};

export default PayslipUpload;
