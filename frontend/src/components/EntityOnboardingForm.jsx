import React, { useEffect, useMemo, useState } from 'react';
import { entityService } from '../services/entityService';
import { useEntityForm } from '../hooks/useEntityForm';
import StepIndicator from './StepIndicator';
import CompanyDetailsForm from './CompanyDetailsForm';
import LoanDetailsForm from './LoanDetailsForm';

export const EntityOnboardingForm = ({ entityId = null, onEntityCreated = null, title = 'Entity Onboarding' }) => {
  const [activeEntityId, setActiveEntityId] = useState(entityId);
  const [submitError, setSubmitError] = useState('');

  useEffect(() => {
    setActiveEntityId(entityId);
  }, [entityId]);

  const {
    currentStep,
    formData,
    errors,
    autoSaveStatus,
    setAutoSaveStatus,
    handleStepChange,
    handleFieldChange,
    handleNext,
    handlePrevious,
    validateLoanDetails,
  } = useEntityForm();

  const normalizedPayload = useMemo(() => {
    const toNullableNumber = (value) => {
      if (value === '' || value === null || value === undefined) return null;
      const numericValue = Number(value);
      return Number.isFinite(numericValue) ? numericValue : null;
    };

    const cleanString = (value) => (typeof value === 'string' ? value.trim() : value);

    return {
      company_details: {
        company_name: cleanString(formData.company_details.company_name),
        cin: cleanString(formData.company_details.cin),
        pan: cleanString(formData.company_details.pan),
        sector: cleanString(formData.company_details.sector),
        subsector: cleanString(formData.company_details.subsector),
        turnover: toNullableNumber(formData.company_details.turnover),
        address: cleanString(formData.company_details.address),
      },
      loan_details: {
        loan_type: formData.loan_details.loan_type || null,
        loan_amount: toNullableNumber(formData.loan_details.loan_amount),
        tenure: toNullableNumber(formData.loan_details.tenure),
        interest_rate: toNullableNumber(formData.loan_details.interest_rate),
        purpose_of_loan: cleanString(formData.loan_details.purpose_of_loan) || null,
      },
    };
  }, [formData]);

  // Load entity data if editing
  useEffect(() => {
    if (activeEntityId) {
      entityService
        .getEntity(activeEntityId)
        .then((response) => {
          const data = response.data;
          // Populate form with existing data
          handleFieldChange('company_details', 'company_name', data.company_name || '');
          handleFieldChange('company_details', 'cin', data.cin || '');
          handleFieldChange('company_details', 'pan', data.pan || '');
          handleFieldChange('company_details', 'sector', data.sector || '');
          handleFieldChange('company_details', 'subsector', data.subsector || '');
          handleFieldChange('company_details', 'turnover', data.turnover || '');
          handleFieldChange('company_details', 'address', data.address || '');
          handleFieldChange('loan_details', 'loan_type', data.loan_type || '');
          handleFieldChange('loan_details', 'loan_amount', data.loan_amount || '');
          handleFieldChange('loan_details', 'tenure', data.tenure || '');
          handleFieldChange('loan_details', 'interest_rate', data.interest_rate || '');
          handleFieldChange('loan_details', 'purpose_of_loan', data.purpose_of_loan || '');
        })
        .catch((error) => console.error('Error loading entity:', error));
    }
  }, [activeEntityId]);

  // Autosave draft
  useEffect(() => {
    const autoSaveTimer = setTimeout(() => {
      if (activeEntityId) {
        setAutoSaveStatus('saving');
        entityService
          .updateEntity(activeEntityId, {
            ...normalizedPayload,
            is_draft: true,
          })
          .then(() => {
            setAutoSaveStatus('saved');
            setTimeout(() => setAutoSaveStatus('idle'), 2000);
          })
          .catch(() => setAutoSaveStatus('error'));
      } else {
        setAutoSaveStatus('idle');
      }
    }, 1000);

    return () => clearTimeout(autoSaveTimer);
  }, [activeEntityId, normalizedPayload, setAutoSaveStatus]);

  const handleCreateEntity = async () => {
    const loanErrors = validateLoanDetails();
    if (Object.keys(loanErrors).length > 0) {
      return;
    }

    try {
      setSubmitError('');
      setAutoSaveStatus('saving');
      let response;
      const payload = {
        ...normalizedPayload,
        is_draft: false,
      };

      if (activeEntityId) {
        response = await entityService.updateEntity(activeEntityId, payload);
      } else {
        response = await entityService.createEntity(payload);
        setActiveEntityId(response.data.id);
      }

      setAutoSaveStatus('saved');
      if (onEntityCreated) {
        onEntityCreated(response.data);
      }
    } catch (error) {
      setAutoSaveStatus('error');
      setSubmitError(error.response?.data?.detail || 'Failed to save onboarding details');
      console.error('Error creating entity:', error);
    }
  };

  const handleSaveDraft = async () => {
    try {
      setSubmitError('');
      setAutoSaveStatus('saving');
      const payload = {
        ...normalizedPayload,
        is_draft: true,
      };

      if (activeEntityId) {
        await entityService.updateEntity(activeEntityId, payload);
      } else {
        const response = await entityService.createEntity(payload);
        setActiveEntityId(response.data.id);
      }
      setAutoSaveStatus('saved');
      setTimeout(() => setAutoSaveStatus('idle'), 2000);
    } catch (error) {
      setAutoSaveStatus('error');
      setSubmitError(error.response?.data?.detail || 'Failed to save draft');
      console.error('Error saving draft:', error);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-2xl mx-auto bg-white rounded-lg shadow p-8">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-3xl font-bold text-gray-900">{title}</h1>
          {autoSaveStatus === 'saving' && (
            <span className="text-sm text-blue-600 animate-pulse">Saving...</span>
          )}
          {autoSaveStatus === 'saved' && (
            <span className="text-sm text-green-600">✓ Saved</span>
          )}
          {autoSaveStatus === 'error' && (
            <span className="text-sm text-red-600">Error saving</span>
          )}
        </div>

        <StepIndicator currentStep={currentStep} totalSteps={2} />

        <div className="mb-8">
          {submitError && (
            <div className="mb-4 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
              {submitError}
            </div>
          )}
          {currentStep === 1 && (
            <CompanyDetailsForm
              formData={formData}
              errors={errors}
              onFieldChange={handleFieldChange}
            />
          )}
          {currentStep === 2 && (
            <LoanDetailsForm
              formData={formData}
              errors={errors}
              onFieldChange={handleFieldChange}
            />
          )}
        </div>

        <div className="flex justify-between gap-4">
          <button
            onClick={handlePrevious}
            disabled={currentStep === 1}
            className={`px-6 py-2 rounded-lg font-medium ${
              currentStep === 1
                ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                : 'bg-gray-200 text-gray-800 hover:bg-gray-300'
            }`}
          >
            Previous
          </button>

          <div className="flex gap-2">
            <button
              onClick={handleSaveDraft}
              className="px-6 py-2 rounded-lg font-medium bg-gray-200 text-gray-800 hover:bg-gray-300"
            >
              Save as Draft
            </button>

            {currentStep === 1 ? (
              <button
                onClick={handleNext}
                className="px-6 py-2 rounded-lg font-medium bg-blue-600 text-white hover:bg-blue-700"
              >
                Next
              </button>
            ) : (
              <button
                onClick={handleCreateEntity}
                className="px-6 py-2 rounded-lg font-medium bg-green-600 text-white hover:bg-green-700"
              >
                Submit
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default EntityOnboardingForm;
