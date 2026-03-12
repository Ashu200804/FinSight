import React from 'react';

export const LoanDetailsForm = ({ formData, errors, onFieldChange }) => {
  const handleChange = (field) => (e) => {
    onFieldChange('loan_details', field, e.target.value);
  };

  const loanTypes = [
    { value: 'term_loan', label: 'Term Loan' },
    { value: 'working_capital', label: 'Working Capital' },
    { value: 'equipment_finance', label: 'Equipment Finance' },
    { value: 'invoice_discounting', label: 'Invoice Discounting' },
  ];

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-gray-800">Loan Details</h2>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Loan Type *
          </label>
          <select
            value={formData.loan_details.loan_type}
            onChange={handleChange('loan_type')}
            className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
              errors.loan_type ? 'border-red-500' : 'border-gray-300'
            }`}
          >
            <option value="">Select loan type</option>
            {loanTypes.map((type) => (
              <option key={type.value} value={type.value}>
                {type.label}
              </option>
            ))}
          </select>
          {errors.loan_type && (
            <p className="text-red-500 text-sm mt-1">{errors.loan_type}</p>
          )}
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Loan Amount (₹) *
          </label>
          <input
            type="number"
            value={formData.loan_details.loan_amount}
            onChange={handleChange('loan_amount')}
            placeholder="Enter loan amount"
            className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
              errors.loan_amount ? 'border-red-500' : 'border-gray-300'
            }`}
          />
          {errors.loan_amount && (
            <p className="text-red-500 text-sm mt-1">{errors.loan_amount}</p>
          )}
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Tenure (months) *
          </label>
          <input
            type="number"
            value={formData.loan_details.tenure}
            onChange={handleChange('tenure')}
            placeholder="Enter tenure in months"
            className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
              errors.tenure ? 'border-red-500' : 'border-gray-300'
            }`}
          />
          {errors.tenure && (
            <p className="text-red-500 text-sm mt-1">{errors.tenure}</p>
          )}
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Interest Rate (%) *
          </label>
          <input
            type="number"
            step="0.01"
            value={formData.loan_details.interest_rate}
            onChange={handleChange('interest_rate')}
            placeholder="Enter interest rate"
            className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
              errors.interest_rate ? 'border-red-500' : 'border-gray-300'
            }`}
          />
          {errors.interest_rate && (
            <p className="text-red-500 text-sm mt-1">{errors.interest_rate}</p>
          )}
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Purpose of Loan *
        </label>
        <textarea
          value={formData.loan_details.purpose_of_loan}
          onChange={handleChange('purpose_of_loan')}
          placeholder="Describe the purpose of the loan"
          rows="3"
          className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
            errors.purpose_of_loan ? 'border-red-500' : 'border-gray-300'
          }`}
        />
        {errors.purpose_of_loan && (
          <p className="text-red-500 text-sm mt-1">{errors.purpose_of_loan}</p>
        )}
      </div>
    </div>
  );
};

export default LoanDetailsForm;
