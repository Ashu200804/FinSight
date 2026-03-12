import React from 'react';

export const CompanyDetailsForm = ({ formData, errors, onFieldChange }) => {
  const handleChange = (field) => (e) => {
    onFieldChange('company_details', field, e.target.value);
  };

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-gray-800">Company Details</h2>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Company Name *
          </label>
          <input
            type="text"
            value={formData.company_details.company_name}
            onChange={handleChange('company_name')}
            placeholder="Enter company name"
            className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
              errors.company_name ? 'border-red-500' : 'border-gray-300'
            }`}
          />
          {errors.company_name && (
            <p className="text-red-500 text-sm mt-1">{errors.company_name}</p>
          )}
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            CIN *
          </label>
          <input
            type="text"
            value={formData.company_details.cin}
            onChange={handleChange('cin')}
            placeholder="Enter CIN"
            className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
              errors.cin ? 'border-red-500' : 'border-gray-300'
            }`}
          />
          {errors.cin && <p className="text-red-500 text-sm mt-1">{errors.cin}</p>}
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            PAN *
          </label>
          <input
            type="text"
            value={formData.company_details.pan}
            onChange={handleChange('pan')}
            placeholder="Enter PAN"
            className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
              errors.pan ? 'border-red-500' : 'border-gray-300'
            }`}
          />
          {errors.pan && <p className="text-red-500 text-sm mt-1">{errors.pan}</p>}
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Sector *
          </label>
          <input
            type="text"
            value={formData.company_details.sector}
            onChange={handleChange('sector')}
            placeholder="Enter sector"
            className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
              errors.sector ? 'border-red-500' : 'border-gray-300'
            }`}
          />
          {errors.sector && (
            <p className="text-red-500 text-sm mt-1">{errors.sector}</p>
          )}
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Subsector *
          </label>
          <input
            type="text"
            value={formData.company_details.subsector}
            onChange={handleChange('subsector')}
            placeholder="Enter subsector"
            className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
              errors.subsector ? 'border-red-500' : 'border-gray-300'
            }`}
          />
          {errors.subsector && (
            <p className="text-red-500 text-sm mt-1">{errors.subsector}</p>
          )}
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Turnover (Optional)
          </label>
          <input
            type="number"
            value={formData.company_details.turnover}
            onChange={handleChange('turnover')}
            placeholder="Enter turnover"
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Address *
        </label>
        <textarea
          value={formData.company_details.address}
          onChange={handleChange('address')}
          placeholder="Enter full address"
          rows="3"
          className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
            errors.address ? 'border-red-500' : 'border-gray-300'
          }`}
        />
        {errors.address && (
          <p className="text-red-500 text-sm mt-1">{errors.address}</p>
        )}
      </div>
    </div>
  );
};

export default CompanyDetailsForm;
