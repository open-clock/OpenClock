import { ClockType } from "@/lib/clocktype";
import { useState } from "react";
import WelcomePage from "./setup-steps/welcome-page";
import WifiPage from "./setup-steps/wifi-page";
import LoginPage from "./setup-steps/login-page";
import CompletePage from "./setup-steps/complete-page";
import { Button } from "./ui/button";
import Copyright from "./copyright";

export default function SetupWizard({ clocktype }: { clocktype: ClockType }) {
  const [currentStep, setCurrentStep] = useState(0);

  const steps = [
    <WelcomePage key="welcome" clocktype={clocktype} />,
    <WifiPage key="wifi" />,
    <LoginPage key="login" />,
    <CompletePage key="complete" />
  ];

  return (
    <div className="min-h-screen flex flex-col">
      <div className="flex-1 flex items-center justify-center">
        <div className="max-w-xl w-full p-6 flex flex-col min-h-[500px]">
          <div className="flex-1 overflow-y-auto mb-8">
            {steps[currentStep]}
          </div>
          <div className="flex flex-col gap-4">
            <div className="flex justify-between">
              <Button
                onClick={() => setCurrentStep(prev => Math.max(0, prev - 1))}
                disabled={currentStep === 0}
              >
                Back
              </Button>
            
              <Button
                onClick={() => {
                  if (currentStep === steps.length - 1) {
                    window.location.reload();
                  } else {
                    setCurrentStep(prev => Math.min(steps.length - 1, prev + 1));
                  }
                }}
              >
                {currentStep === steps.length - 1 ? 'Finish' : 'Next'}
              </Button>
            </div>

            <div className="flex justify-center gap-2">
              {steps.map((_, index) => (
                <div
                  key={index}
                  className={`h-2 w-2 rounded-full ${index === currentStep ? 'bg-light-accent dark:bg-dark-accent' : 'bg-light-secondary dark:bg-dark-secondary'
                    }`}
                />
              ))}
            </div>
          </div>
        </div>
      </div>
      <div className="py-4 text-center">
        <Copyright clocktype={clocktype} />
      </div>
    </div>
  );
}