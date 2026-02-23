import React, { useState, useRef } from 'react';
import { motion } from 'framer-motion';
import { Upload, FileUp, AlertCircle, CheckCircle, Loader, FileText } from 'lucide-react';
import { uploadPayslip, uploadForm16 } from '../utils/api';

const PayslipUpload = ({ onDataExtracted }) => {
  const [file, setFile] = useState(null);
  const [documentType, setDocumentType] = useState('payslip'); // 'payslip' or 'form16'
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [warnings, setWarnings] = useState([]);
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
    setWarnings([]);
  };

  const handleUpload = async () => {
    if (!file) {
      setError('Please select a file first');
      return;
    }

    setUploading(true);
    setError(null);
    setWarnings([]);

    try {
      console.log(`Uploading ${documentType}:`, file.name);
      
      let response;
      if (documentType === 'form16') {
        response = await uploadForm16(file);
      } else {
        response = await uploadPayslip(file);
      }

      console.log(`${documentType} upload response:`, response);

      if (response.success) {
        setResult(response);
        
        // Handle warnings/confidence
        if (response.warnings && response.warnings.length > 0) {
          setWarnings(response.warnings);
        }

        // Notify parent component with extracted data
        if (onDataExtracted) {
          if (documentType === 'form16' && response.extracted_data) {
            // Pass Form 16 data to parent
            onDataExtracted({
              type: 'form16',
              data: response.extracted_data,
              confidence: response.confidence
            });
          } else if (response.data_collected) {
            // Pass payslip data to parent
            onDataExtracted({
              type: 'payslip',
              data: response.data_collected,
              confidence: response.confidence
            });
          }
        }
      } else {
        setError(response.message || `Failed to analyze ${documentType}`);
      }
    } catch (err) {
      console.error(`${documentType} upload error:`, err);
      setError(err.response?.data?.detail || err.message || `Error uploading ${documentType}. Please try again.`);
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

  const documentTypeLabel = documentType === 'form16' ? 'Form 16' : 'Payslip';
  const documentTypeIcon = documentType === 'form16' ? <FileText className="w-6 h-6 text-white" /> : <FileUp className="w-6 h-6 text-white" />;

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
          {documentTypeIcon}
        </div>
        <div>
          <h3 className="text-xl font-bold text-white">Upload {documentTypeLabel}</h3>
          <p className="text-sm text-dark-400">Auto-extract {documentType === 'form16' ? 'salary & tax details from Form 16' : 'salary details'} from PDF/Image</p>
        </div>
      </div>

      {/* Document Type Selector */}
      {!result?.success && (
        <div className="flex gap-2 p-3 rounded-lg bg-white/5 border border-white/10">
          <button
            onClick={() => {
              setDocumentType('payslip');
              setFile(null);
              setError(null);
            }}
            className={`flex-1 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
              documentType === 'payslip'
                ? 'bg-primary-600 text-white shadow-lg'
                : 'bg-transparent text-dark-300 hover:text-white'
            }`}
          >
            📄 Payslip
          </button>
          <button
            onClick={() => {
              setDocumentType('form16');
              setFile(null);
              setError(null);
            }}
            className={`flex-1 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
              documentType === 'form16'
                ? 'bg-primary-600 text-white shadow-lg'
                : 'bg-transparent text-dark-300 hover:text-white'
            }`}
          >
            📋 Form 16
          </button>
        </div>
      )}

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
                {file ? file.name : `Click to upload or drag and drop`}
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

      {/* Warnings Alert */}
      {warnings.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="p-4 rounded-lg bg-yellow-500/10 border border-yellow-500/30 flex items-start gap-3"
        >
          <AlertCircle className="w-5 h-5 text-yellow-400 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-medium text-yellow-300">Warnings</p>
            <ul className="text-xs text-yellow-200 mt-2 space-y-1">
              {warnings.map((warning, idx) => (
                <li key={idx}>• {warning}</li>
              ))}
            </ul>
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
            {documentType === 'form16' && result.extracted_data && (
              <div className="mt-3 space-y-2 text-xs text-green-200">
                {result.extracted_data.employee_name && (
                  <p>👤 {result.extracted_data.employee_name}</p>
                )}
                {result.extracted_data.pan && (
                  <p>🆔 PAN: {result.extracted_data.pan}</p>
                )}
                {result.extracted_data.gross_salary && (
                  <p>💰 Gross Salary: ₹{Math.round(result.extracted_data.gross_salary).toLocaleString()}</p>
                )}
                {result.extracted_data.tds_deducted && (
                  <p>📊 TDS Deducted: ₹{Math.round(result.extracted_data.tds_deducted).toLocaleString()}</p>
                )}
              </div>
            )}
            {documentType === 'payslip' && result.extracted_data && (
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
          <span>Analyze {documentTypeLabel}</span>
        </button>
      )}

      {/* Loading State */}
      {uploading && (
        <div className="flex flex-col items-center justify-center py-6 space-y-3">
          <Loader className="w-8 h-8 text-primary-400 animate-spin" />
          <p className="text-sm text-dark-300">Analyzing {documentTypeLabel}...</p>
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
          <h4 className="text-sm font-semibold text-white">✓ {documentTypeLabel} Data Extracted Successfully</h4>
          <p className="text-xs text-dark-300">This information will be used in your chat to provide personalized advice.</p>

          <button
            onClick={() => {
              setResult(null);
              setFile(null);
              setWarnings([]);
              fileInputRef.current?.click();
            }}
            className="w-full btn-secondary text-sm mt-4"
          >
            Upload Another {documentTypeLabel}
          </button>
        </motion.div>
      )}

      {/* Hint Text */}
      <div className="p-3 rounded-lg bg-blue-500/10 border border-blue-500/20 flex items-start gap-2">
        <AlertCircle className="w-4 h-4 text-blue-400 flex-shrink-0 mt-0.5" />
        <div className="text-xs text-blue-200">
          <p className="font-medium">💡 Tip:</p>
          {documentType === 'form16' ? (
            <p className="mt-1">Form 16 contains complete salary and tax information. Uploading it will auto-fill your income details and TDS deducted - skip these questions during chat!</p>
          ) : (
            <p className="mt-1">Your payslip will be analyzed to auto-fill income and tax details. You can still edit or skip if needed.</p>
          )}
        </div>
      </div>
    </motion.div>
  );
};

export default PayslipUpload;
