import { useState, useCallback } from 'react';

export const useEntityForm = (initialData = null) => {
  const [currentStep, setCurrentStep] = useState(1);
  const [formData, setFormData] = useState(
    initialData || {
      company_details: {
        company_name: '',
        cin: '',
        pan: '',
        sector: '',
        subsector: '',
        turnover: '',
        address: '',
      },
      loan_details: {
        loan_type: '',
        loan_amount: '',
        tenure: '',
        interest_rate: '',
        purpose_of_loan: '',
      },
      is_draft: true,
    }
  );
  const [errors, setErrors] = useState({});
  const [autoSaveStatus, setAutoSaveStatus] = useState('idle');

  const validateCompanyDetails = useCallback(() => {
    const newErrors = {};
    const company = formData.company_details;

    if (!company.company_name?.trim()) newErrors.company_name = 'Company name is required';
    if (!company.cin?.trim()) newErrors.cin = 'CIN is required';
    if (!company.pan?.trim()) newErrors.pan = 'PAN is required';
    if (!company.sector?.trim()) newErrors.sector = 'Sector is required';
    if (!company.subsector?.trim()) newErrors.subsector = 'Subsector is required';
    if (!company.address?.trim()) newErrors.address = 'Address is required';

    return newErrors;
  }, [formData]);

  const validateLoanDetails = useCallback(() => {
    const newErrors = {};
    const loan = formData.loan_details;

    if (!loan.loan_type?.trim()) newErrors.loan_type = 'Loan type is required';
    if (!loan.loan_amount || loan.loan_amount <= 0) newErrors.loan_amount = 'Valid loan amount is required';
    if (!loan.tenure || loan.tenure <= 0) newErrors.tenure = 'Valid tenure is required';
    if (loan.interest_rate === '' || loan.interest_rate < 0) newErrors.interest_rate = 'Valid interest rate is required';
    if (!loan.purpose_of_loan?.trim()) newErrors.purpose_of_loan = 'Purpose of loan is required';

    return newErrors;
  }, [formData]);

  const handleStepChange = useCallback((step) => {
    setCurrentStep(step);
    setErrors({});
  }, []);

  const handleFieldChange = useCallback((section, field, value) => {
    setFormData((prev) => ({
      ...prev,
      [section]: {
        ...prev[section],
        [field]: value,
      },
    }));
  }, []);

  const handleNext = useCallback(() => {
    if (currentStep === 1) {
      const newErrors = validateCompanyDetails();
      if (Object.keys(newErrors).length > 0) {
        setErrors(newErrors);
        return false;
      }
    }
    if (currentStep < 2) {
      setCurrentStep((prev) => prev + 1);
      return true;
    }
    return true;
  }, [currentStep, validateCompanyDetails]);

  const handlePrevious = useCallback(() => {
    if (currentStep > 1) {
      setCurrentStep((prev) => prev - 1);
      setErrors({});
    }
  }, [currentStep]);

  return {
    currentStep,
    formData,
    errors,
    autoSaveStatus,
    setAutoSaveStatus,
    handleStepChange,
    handleFieldChange,
    handleNext,
    handlePrevious,
    validateCompanyDetails,
    validateLoanDetails,
  };
};
