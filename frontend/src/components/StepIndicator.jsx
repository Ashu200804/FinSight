import React from 'react';

export const StepIndicator = ({ currentStep, totalSteps = 2 }) => {
  return (
    <div className="w-full flex items-center justify-between mb-8">
      {[1, 2].map((step) => (
        <React.Fragment key={step}>
          <div className="flex flex-col items-center">
            <div
              className={`w-10 h-10 rounded-full flex items-center justify-center font-semibold transition-colors ${
                step <= currentStep
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-200 text-gray-500'
              }`}
            >
              {step}
            </div>
            <span className="mt-2 text-sm font-medium text-gray-700">
              {step === 1 ? 'Company Details' : 'Loan Details'}
            </span>
          </div>
          {step < totalSteps && (
            <div
              className={`flex-1 h-1 mx-4 ${
                step < currentStep ? 'bg-blue-600' : 'bg-gray-200'
              }`}
            />
          )}
        </React.Fragment>
      ))}
    </div>
  );
};

export default StepIndicator;
